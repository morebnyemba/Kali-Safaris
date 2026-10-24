"""
Departure-time selection for website checkouts: tours with fixed departures
require one of them, past departures are refused, and the time is kept on the
booking and in its shared (manifest) reference.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from customer_data.models import Booking
from products_and_services.models import Tour, parse_departure_times

from .views import PricingError, _finalize_booking_reference_if_temporary, _resolve_or_create_booking


def _traveler(name):
    return {'name': name, 'age': 30, 'nationality': 'Zimbabwean', 'gender': 'Female',
            'id_number': f'ID-{name}', 'type': 'adult'}


class DepartureTimeCheckoutTests(TestCase):
    def setUp(self):
        self.tour = Tour.objects.create(name='Slot Cruise', base_price=Decimal('30.00'),
                                        departure_times='16:00, 06:00, 12:00', is_active=True)
        self.untimed = Tour.objects.create(name='Day Trip', base_price=Decimal('30.00'), is_active=True)
        self.day = date.today() + timedelta(days=7)

    def _payload(self, tour_name='Slot Cruise', when=None, selected_time=None):
        details = {
            'tour_name': tour_name, 'selected_date': (when or self.day).isoformat(), 'number_of_people': 1,
            'customer': {'full_name': 'Ann Moyo', 'email': 'ann@example.com', 'phone': '0771234567'},
            'travelers': [_traveler('Ann')],
        }
        if selected_time is not None:
            details['selected_time'] = selected_time
        return {'booking_details': details}

    def test_time_required_and_must_be_offered(self):
        for bad in (None, '', '09:00', 'noon', '06:00,12:00'):
            with self.subTest(selected_time=bad), self.assertRaises(PricingError) as ctx:
                _resolve_or_create_booking(self._payload(selected_time=bad), Decimal('30.00'))
            self.assertIn('06:00, 12:00, 16:00', str(ctx.exception))
        self.assertEqual(Booking.objects.count(), 0)

    def test_valid_time_is_stored_and_in_shared_reference(self):
        booking, _ = _resolve_or_create_booking(self._payload(selected_time='16:00'), Decimal('30.00'))
        self.assertEqual(booking.start_time, time(16, 0))
        booking = _finalize_booking_reference_if_temporary(booking)
        self.assertEqual(booking.booking_reference, f"BK-T{self.tour.id:03d}-{self.day:%Y%m%d}-1600")

    def test_departures_of_one_day_get_separate_references(self):
        refs = set()
        for slot in ('06:00', '16:00'):
            booking, _ = _resolve_or_create_booking(self._payload(selected_time=slot), Decimal('30.00'))
            refs.add(_finalize_booking_reference_if_temporary(booking).booking_reference)
        self.assertEqual(len(refs), 2)

    def test_departure_that_has_left_today_is_refused(self):
        today = timezone.localdate()
        noon = timezone.make_aware(datetime.combine(today, time(12, 30)))
        with mock.patch('cbz_integration.views.timezone.localtime', return_value=noon):
            with self.assertRaises(PricingError) as ctx:
                _resolve_or_create_booking(self._payload(when=today, selected_time='12:00'), Decimal('30.00'))
            self.assertIn('already left', str(ctx.exception))
            booking, _ = _resolve_or_create_booking(self._payload(when=today, selected_time='16:00'), Decimal('30.00'))
        self.assertEqual(booking.start_time, time(16, 0))

    def test_past_date_is_refused(self):
        with self.assertRaises(PricingError):
            _resolve_or_create_booking(self._payload(when=date.today() - timedelta(days=1), selected_time='16:00'),
                                       Decimal('30.00'))

    def test_tour_without_times_ignores_time(self):
        booking, _ = _resolve_or_create_booking(self._payload('Day Trip', selected_time='09:00'), Decimal('30.00'))
        self.assertIsNone(booking.start_time)
        booking = _finalize_booking_reference_if_temporary(booking)
        self.assertEqual(booking.booking_reference, f"BK-T{self.untimed.id:03d}-{self.day:%Y%m%d}")

    def test_public_tour_list_exposes_sorted_times(self):
        tours = {t['name']: t for t in self.client.get('/crm-api/tours/', HTTP_HOST='localhost').json()['tours']}
        self.assertEqual(tours['Slot Cruise']['departure_times'], ['06:00', '12:00', '16:00'])
        self.assertEqual(tours['Day Trip']['departure_times'], [])


class DepartureTimesFieldTests(TestCase):
    def test_parse_normalises_and_dedupes(self):
        self.assertEqual(parse_departure_times(' 16:00; 6:00, 16:00 ,'), [time(6, 0), time(16, 0)])
        self.assertEqual(parse_departure_times(''), [])
        with self.assertRaises(ValueError):
            parse_departure_times('6pm')

    def test_admin_save_normalises_and_rejects_bad_times(self):
        tour = Tour.objects.create(name='Norm', base_price=Decimal('1.00'), departure_times='16:00,6:00')
        self.assertEqual(tour.departure_times, '06:00, 16:00')
        with self.assertRaises(ValidationError):
            Tour.objects.create(name='Bad', base_price=Decimal('1.00'), departure_times='25:00')

    def test_seeded_cruises_have_their_published_times(self):
        times = dict(Tour.objects.filter(name__in=['Sunrise Cruise', 'Lunch Cruise', 'Sunset Cruise'])
                     .values_list('name', 'departure_times'))
        self.assertEqual(times, {'Sunrise Cruise': '06:00', 'Lunch Cruise': '12:00', 'Sunset Cruise': '16:00'})
