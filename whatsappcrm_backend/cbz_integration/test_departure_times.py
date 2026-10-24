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
