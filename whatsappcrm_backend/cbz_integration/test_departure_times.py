"""
Time-slot selection (admin-defined slots such as 08:00–10:00) on both booking
channels: website checkout and the WhatsApp booking flow. Tours with slots
require one, departed slots are refused, and the slot is kept on the booking
and in its shared (manifest) reference.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from conversations.models import Contact
from customer_data.models import Booking
from flows.actions import load_departure_slots, select_departure_slot
from flows.models import FlowStep
from flows.services import _coerce_model_field_value, _execute_step_actions
from products_and_services.models import Tour, TourTimeSlot

from .views import PricingError, _finalize_booking_reference_if_temporary, _resolve_or_create_booking


def _traveler(name):
    return {'name': name, 'age': 30, 'nationality': 'Zimbabwean', 'gender': 'Female',
            'id_number': f'ID-{name}', 'type': 'adult'}


def _at(day, hh, mm=0):
    return timezone.make_aware(datetime.combine(day, time(hh, mm)))


class SlotFixtureMixin:
    def make_tours(self):
        self.tour = Tour.objects.create(name='Slot Cruise', base_price=Decimal('30.00'), is_active=True)
        TourTimeSlot.objects.create(tour=self.tour, start_time=time(16), label='Sunset')
        TourTimeSlot.objects.create(tour=self.tour, start_time=time(8), end_time=time(10), label='Morning')
        TourTimeSlot.objects.create(tour=self.tour, start_time=time(12), end_time=time(14), is_active=False)
        self.untimed = Tour.objects.create(name='Day Trip', base_price=Decimal('30.00'), is_active=True)
        self.day = date.today() + timedelta(days=7)


class WebsiteCheckoutSlotTests(SlotFixtureMixin, TestCase):
    def setUp(self):
        self.make_tours()

    def _payload(self, tour_name='Slot Cruise', when=None, selected_time=None):
        details = {
            'tour_name': tour_name, 'selected_date': (when or self.day).isoformat(), 'number_of_people': 1,
            'customer': {'full_name': 'Ann Moyo', 'email': 'ann@example.com', 'phone': '0771234567'},
            'travelers': [_traveler('Ann')],
        }
        if selected_time is not None:
            details['selected_time'] = selected_time
        return {'booking_details': details}

    def test_slot_required_and_must_be_active(self):
        for bad in (None, '', '09:00', '12:00', 'noon'):  # 12:00 exists but is switched off
            with self.subTest(selected_time=bad), self.assertRaises(PricingError) as ctx:
                _resolve_or_create_booking(self._payload(selected_time=bad), Decimal('30.00'))
            self.assertIn('08:00–10:00, 16:00', str(ctx.exception))
        self.assertEqual(Booking.objects.count(), 0)

    def test_slot_times_are_stored_and_in_shared_reference(self):
        booking, _ = _resolve_or_create_booking(self._payload(selected_time='08:00'), Decimal('30.00'))
        self.assertEqual((booking.start_time, booking.end_time), (time(8), time(10)))
        self.assertEqual(booking.departure_display, '08:00–10:00')
        booking = _finalize_booking_reference_if_temporary(booking)
        self.assertEqual(booking.booking_reference, f"BK-T{self.tour.id:03d}-{self.day:%Y%m%d}-0800")

    def test_slots_of_one_day_get_separate_references(self):
        refs = {
            _finalize_booking_reference_if_temporary(
                _resolve_or_create_booking(self._payload(selected_time=t), Decimal('30.00'))[0]
            ).booking_reference
            for t in ('08:00', '16:00')
        }
        self.assertEqual(len(refs), 2)

    def test_departed_slot_refused_later_slot_accepted(self):
        today = timezone.localdate()
        with mock.patch('cbz_integration.views.timezone.localtime', return_value=_at(today, 9)), \
                mock.patch('products_and_services.departures.timezone.localtime', return_value=_at(today, 9)):
            with self.assertRaises(PricingError) as ctx:
                _resolve_or_create_booking(self._payload(when=today, selected_time='08:00'), Decimal('30.00'))
            self.assertIn('already left', str(ctx.exception))
            booking, _ = _resolve_or_create_booking(self._payload(when=today, selected_time='16:00'), Decimal('30.00'))
        self.assertEqual(booking.start_time, time(16))
        self.assertIsNone(booking.end_time)

    def test_all_slots_departed_and_past_dates_refused(self):
        today = timezone.localdate()
        with mock.patch('cbz_integration.views.timezone.localtime', return_value=_at(today, 17)), \
                mock.patch('products_and_services.departures.timezone.localtime', return_value=_at(today, 17)):
            with self.assertRaisesMessage(PricingError, 'have left'):
                _resolve_or_create_booking(self._payload(when=today, selected_time='16:00'), Decimal('30.00'))
        with self.assertRaises(PricingError):
            _resolve_or_create_booking(self._payload(when=date.today() - timedelta(days=1), selected_time='16:00'),
                                       Decimal('30.00'))

    def test_tour_without_slots_ignores_time(self):
        booking, _ = _resolve_or_create_booking(self._payload('Day Trip', selected_time='09:00'), Decimal('30.00'))
        self.assertIsNone(booking.start_time)
        self.assertEqual(_finalize_booking_reference_if_temporary(booking).booking_reference,
                         f"BK-T{self.untimed.id:03d}-{self.day:%Y%m%d}")

    def test_public_tour_list_exposes_active_slots_in_order(self):
        tours = {t['name']: t for t in self.client.get('/crm-api/tours/', HTTP_HOST='localhost').json()['tours']}
        self.assertEqual(
            [(s['start'], s['end'], s['label']) for s in tours['Slot Cruise']['time_slots']],
            [('08:00', '10:00', 'Morning'), ('16:00', None, 'Sunset')],
        )
        self.assertEqual(tours['Day Trip']['time_slots'], [])


class TimeSlotModelTests(TestCase):
    def test_end_must_follow_start(self):
        tour = Tour.objects.create(name='T', base_price=Decimal('1.00'))
        with self.assertRaises(ValidationError):
            TourTimeSlot(tour=tour, start_time=time(10), end_time=time(8)).full_clean()
        TourTimeSlot(tour=tour, start_time=time(8), end_time=time(10)).full_clean()

    def test_seeded_cruises_have_their_published_slots(self):
        slots = {
            t.name: [s.time_range for s in t.active_time_slots()]
            for t in Tour.objects.filter(name__in=['Sunrise Cruise', 'Lunch Cruise', 'Sunset Cruise'])
        }
        self.assertEqual(slots, {'Sunrise Cruise': ['06:00–08:00'], 'Lunch Cruise': ['12:00–14:00'], 'Sunset Cruise': ['16:00']})


class WhatsAppSlotFlowTests(SlotFixtureMixin, TestCase):
    def setUp(self):
        self.make_tours()
        self.contact = Contact.objects.create(whatsapp_id='263770000099', name='Bot Test')

    def _load(self, tour, day=None):
        return load_departure_slots(self.contact, {}, {'tour_id': str(tour.id), 'start_date': (day or self.day).isoformat()})

    def test_states(self):
        self.assertEqual(self._load(self.untimed)['departure_state'], 'none')

        ask = self._load(self.tour)
        self.assertEqual(ask['departure_state'], 'ask')
        self.assertEqual(ask['departure_rows'], [
            {'id': 'slot_0800', 'title': '08:00–10:00', 'description': 'Morning'},
            {'id': 'slot_1600', 'title': '16:00', 'description': 'Sunset'},
        ])

        single = Tour.objects.create(name='Single', base_price=Decimal('1.00'))
        TourTimeSlot.objects.create(tour=single, start_time=time(6), end_time=time(8), label='Sunrise')
        chosen = self._load(single)
        self.assertEqual((chosen['departure_state'], chosen['start_time'], chosen['end_time']), ('chosen', '06:00', '08:00'))

        today = timezone.localdate()
        with mock.patch('products_and_services.departures.timezone.localtime', return_value=_at(today, 17)):
            self.assertEqual(self._load(self.tour, today)['departure_state'], 'full')

    def test_selection_validated_against_open_slots(self):
        params = {'tour_id': self.tour.id, 'start_date': self.day.isoformat()}
        ok = select_departure_slot(self.contact, {}, {**params, 'reply_id': 'slot_0800'})
        self.assertEqual(ok, {'departure_valid': True, 'start_time': '08:00', 'end_time': '10:00',
                              'departure_display': 'Morning · 08:00–10:00'})
        for bad in ('slot_1200', 'slot_0900', ''):
            self.assertEqual(select_departure_slot(self.contact, {}, {**params, 'reply_id': bad}),
                             {'departure_valid': False})

    def test_ask_step_renders_a_real_whatsapp_list(self):
        from flows.definitions.booking_flow import BOOKING_FLOW
        step_def = next(s for s in BOOKING_FLOW['steps'] if s['name'] == 'ask_departure_time')
        step = FlowStep(name=step_def['name'], step_type=step_def['type'], config=step_def['config'])
        context = {'tour_name': 'Slot Cruise', 'start_date': self.day.isoformat(), **self._load(self.tour)}
        actions, _ = _execute_step_actions(step, self.contact, context)
        payload = next(a for a in actions if a.get('type') == 'send_whatsapp_message')['data']
        rows = payload['action']['sections'][0]['rows']
        self.assertIsInstance(rows, list)
        self.assertEqual([r['id'] for r in rows], ['slot_0800', 'slot_1600'])

    def test_booking_creation_coerces_slot_times(self):
        start, end = Booking._meta.get_field('start_time'), Booking._meta.get_field('end_time')
        self.assertEqual(_coerce_model_field_value(start, '08:00'), time(8))
        self.assertIsNone(_coerce_model_field_value(end, ''))
        self.assertIsNone(_coerce_model_field_value(end, 'None'))


class SlotCapacityTests(SlotFixtureMixin, TestCase):
    """Seats per slot: paid bookings always hold seats, unpaid ones only for the hold window."""

    def setUp(self):
        self.make_tours()
        self.morning = TourTimeSlot.objects.get(tour=self.tour, start_time=time(8))
        self.morning.capacity = 3
        self.morning.save()
        self.contact = Contact.objects.create(whatsapp_id='263770000098', name='Cap Test')

    def _book(self, adults=1, status=Booking.PaymentStatus.PAID, created_minutes_ago=0, children=0):
        booking = Booking.objects.create(
            tour=self.tour, tour_name=self.tour.name, start_date=self.day, start_time=time(8), end_time=time(10),
            end_date=self.day, number_of_adults=adults, number_of_children=children, payment_status=status,
        )
        if created_minutes_ago:
            Booking.objects.filter(pk=booking.pk).update(created_at=timezone.now() - timedelta(minutes=created_minutes_ago))
        return booking

    def _checkout(self, people=1):
        details = {
            'tour_name': 'Slot Cruise', 'selected_date': self.day.isoformat(), 'selected_time': '08:00',
            'number_of_people': people,
            'customer': {'full_name': 'Ann Moyo', 'email': 'ann@example.com', 'phone': '0771234567'},
            'travelers': [_traveler(f'P{i}') for i in range(people)],
        }
        return _resolve_or_create_booking({'booking_details': details}, Decimal('30.00') * people)

    def test_what_holds_seats(self):
        from products_and_services.departures import seats_left
        self._book(adults=1, children=1)                                            # paid: 2 seats
        self._book(status=Booking.PaymentStatus.CANCELLED)                           # never holds
        self._book(status=Booking.PaymentStatus.PENDING, created_minutes_ago=45)     # hold expired
        self.assertEqual(seats_left(self.morning, self.day), 1)
        self._book(status=Booking.PaymentStatus.PENDING, created_minutes_ago=5)      # active checkout
        self.assertEqual(seats_left(self.morning, self.day), 0)
        unlimited = TourTimeSlot.objects.get(tour=self.tour, start_time=time(16))
        self.assertIsNone(seats_left(unlimited, self.day))

    def test_checkout_refuses_when_full_and_says_how_many_are_left(self):
        self._book(adults=2)
        with self.assertRaisesMessage(PricingError, 'Only 1 seat left'):
            self._checkout(people=2)
        booking, _ = self._checkout(people=1)       # the last seat
        self.assertIsNotNone(booking)
        with self.assertRaisesMessage(PricingError, 'fully booked'):
            self._checkout(people=1)
        self.assertEqual(Booking.objects.filter(start_time=time(8)).count(), 2)

    def test_paying_an_unpaid_booking_after_its_hold_rechecks_seats(self):
        late = self._book(adults=2, status=Booking.PaymentStatus.PENDING, created_minutes_ago=60)
        late.booking_reference = 'BK-LATE-1'
        late.total_amount = Decimal('60.00')
        late.save()
        self._book(adults=1)
        # 1 paid + 2 unpaid = 3 seats: still fits.
        _resolve_or_create_booking({'booking_reference': 'BK-LATE-1'}, Decimal('60.00'))
        self._book(adults=1)
        with self.assertRaisesMessage(PricingError, 'Only 1 seat left'):
            _resolve_or_create_booking({'booking_reference': 'BK-LATE-1'}, Decimal('60.00'))

    def test_availability_endpoint(self):
        self._book(adults=2)
        body = self.client.get(f'/crm-api/tours/{self.tour.id}/availability/?date={self.day.isoformat()}',
                               HTTP_HOST='localhost').json()
        by_start = {s['start']: s for s in body['slots']}
        self.assertEqual((by_start['08:00']['capacity'], by_start['08:00']['seats_left']), (3, 1))
        self.assertIsNone(by_start['16:00']['seats_left'])
        self.assertFalse(by_start['08:00']['departed'])
        for bad in ('', 'tomorrow', '2026-02-30'):
            self.assertEqual(self.client.get(f'/crm-api/tours/{self.tour.id}/availability/?date={bad}',
                                             HTTP_HOST='localhost').status_code, 400)

    def test_whatsapp_hides_slots_without_room_and_rechecks_before_payment(self):
        params = {'tour_id': self.tour.id, 'start_date': self.day.isoformat()}
        self._book(adults=2)
        rows = load_departure_slots(self.contact, {}, {**params, 'party': '1'})['departure_rows']
        self.assertEqual(rows[0], {'id': 'slot_0800', 'title': '08:00–10:00', 'description': 'Morning · 1 seat left'})
        rows = load_departure_slots(self.contact, {}, {**params, 'party': '2'})['departure_rows']
        self.assertEqual([r['id'] for r in rows], ['slot_1600'])
        self.assertEqual(select_departure_slot(self.contact, {}, {**params, 'party': '2', 'reply_id': 'slot_0800'}),
                         {'departure_valid': False})

        from flows.actions import check_departure_capacity
        self.assertTrue(check_departure_capacity(self.contact, {}, {**params, 'start_time': '08:00', 'party': '1'})['departure_still_open'])
        self._book(adults=1)
        self.assertFalse(check_departure_capacity(self.contact, {}, {**params, 'start_time': '08:00', 'party': '1'})['departure_still_open'])
        self.assertTrue(check_departure_capacity(self.contact, {}, {'tour_id': self.untimed.id, 'start_date': self.day.isoformat(),
                                                                    'start_time': '', 'party': '9'})['departure_still_open'])

    def test_whatsapp_reports_fully_booked_day(self):
        TourTimeSlot.objects.filter(tour=self.tour, start_time=time(16)).update(capacity=1)
        self._book(adults=3)
        Booking.objects.create(tour=self.tour, tour_name=self.tour.name, start_date=self.day, start_time=time(16),
                               end_date=self.day, number_of_adults=1, payment_status=Booking.PaymentStatus.PAID)
        state = load_departure_slots(self.contact, {}, {'tour_id': self.tour.id, 'start_date': self.day.isoformat(), 'party': '1'})
        self.assertEqual((state['departure_state'], state['departure_full_reason']), ('full', 'booked'))


class SlotFlowWiringTests(TestCase):
    """The WhatsApp re-check before payment and the re-pick route are wired as intended."""

    def setUp(self):
        from flows.definitions.booking_flow import BOOKING_FLOW
        self.steps = {s['name']: s for s in BOOKING_FLOW['steps']}

    def targets(self, name):
        return [(t['to_step'], t.get('priority')) for t in self.steps[name]['transitions']]

    def test_summary_confirm_rechecks_seats_before_payment(self):
        self.assertTrue(all(to == 'recheck_departure_capacity'
                            for to, _ in self.targets('show_booking_summary') if to != 'edit_booking_details'))
        self.assertIn(('departure_filled_up', 1), self.targets('recheck_departure_capacity'))
        self.assertIn(('ask_payment_option', 2), self.targets('recheck_departure_capacity'))

    def test_repick_goes_back_through_traveler_gate_to_summary(self):
        self.assertEqual(self.targets('set_departure_repick'), [('load_departure_slots', None)])
        self.assertIn(('validate_travelers_before_booking', 1), self.targets('departure_chosen'))
        self.assertIn(('repick_travelers_checked', 0), self.targets('validate_travelers_before_booking'))
        self.assertIn(('show_booking_summary', 1), self.targets('repick_travelers_checked'))
        # The flag is cleared at the start of every booking, so it can't leak into the next one.
        resets = [a for a in self.steps['query_tour_details']['config']['actions_to_run']
                  if a.get('variable_name') == 'departure_repick']
        self.assertEqual(resets[0]['value_template'], 'False')
