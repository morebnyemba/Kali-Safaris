"""
Tests for linking website checkouts to customers (which drives the group name
shown on passenger manifests).
"""
from decimal import Decimal

from django.test import TestCase

from conversations.models import Contact
from customer_data.models import CustomerProfile

from .views import _normalize_phone_to_whatsapp_id, _resolve_web_customer_profile


class NormalizePhoneTests(TestCase):
    def test_formats(self):
        self.assertEqual(_normalize_phone_to_whatsapp_id('0771234567'), '263771234567')
        self.assertEqual(_normalize_phone_to_whatsapp_id('+263 77 123 4567'), '263771234567')
        self.assertEqual(_normalize_phone_to_whatsapp_id('00263771234567'), '263771234567')
        self.assertEqual(_normalize_phone_to_whatsapp_id('+44 7700 900123'), '447700900123')
        self.assertEqual(_normalize_phone_to_whatsapp_id('123'), '')
        self.assertEqual(_normalize_phone_to_whatsapp_id(''), '')


class ResolveWebCustomerProfileTests(TestCase):
    def setUp(self):
        contact = Contact.objects.create(whatsapp_id='263779999999', name='John Existing')
        self.existing = CustomerProfile.objects.create(
            contact=contact, first_name='John', last_name='Existing', email='john@example.com',
        )

    def test_never_matches_on_first_name_alone(self):
        profile = _resolve_web_customer_profile('John Stranger', 'stranger@example.com', '0771112222', 'ZW')
        self.assertIsNotNone(profile)
        self.assertNotEqual(profile.pk, self.existing.pk)
        self.assertEqual(profile.contact.whatsapp_id, '263771112222')
        self.assertEqual(profile.get_full_name(), 'John Stranger')
        self.assertEqual(profile.email, 'stranger@example.com')

    def test_matches_email_case_insensitively_without_overwriting(self):
        profile = _resolve_web_customer_profile('Someone Else', 'JOHN@example.com', '', 'ZW')
        self.assertEqual(profile.pk, self.existing.pk)
        profile.refresh_from_db()
        self.assertEqual(profile.get_full_name(), 'John Existing')
        self.assertEqual(profile.country, 'ZW')  # gap filled

    def test_reuses_whatsapp_contact_for_same_phone(self):
        profile = _resolve_web_customer_profile('John Existing', '', '+263 77 999 9999', '')
        self.assertEqual(profile.pk, self.existing.pk)

    def test_no_identity_returns_none(self):
        self.assertIsNone(_resolve_web_customer_profile('Nameless', '', '', ''))


class WebBookingRequiresTravelerDetailsTests(TestCase):
    """Website checkout must not create a booking without full passenger details."""

    def setUp(self):
        from datetime import date, timedelta
        from products_and_services.models import Tour
        self.tour = Tour.objects.create(name='Test Gate Cruise', base_price=Decimal('50.00'), is_active=True)
        self.travel_date = (date.today() + timedelta(days=14)).isoformat()

    def _payload(self, travelers, people=2):
        return {'booking_details': {
            'tour_name': 'Test Gate Cruise', 'selected_date': self.travel_date, 'number_of_people': people,
            'customer': {'full_name': 'Ann Moyo', 'email': 'ann@example.com', 'phone': '0771234567'},
            'travelers': travelers,
        }}

    def _traveler(self, name, **extra):
        data = {'name': name, 'age': 30, 'nationality': 'Zimbabwean', 'gender': 'Female',
                'id_number': f'ID-{name}', 'type': 'adult'}
        data.update(extra)
        return data

    def test_rejects_before_creating_anything(self):
        from customer_data.models import Booking
        from .views import PricingError, _resolve_or_create_booking

        bad_payloads = [
            self._payload([]),
            self._payload([self._traveler('Ann')]),                             # 1 of 2
            self._payload([self._traveler('Ann'), self._traveler('Ben', id_number='')]),
            self._payload([self._traveler('Ann'), self._traveler('Ben', age='')]),
        ]
        for payload in bad_payloads:
            with self.assertRaises(PricingError):
                _resolve_or_create_booking(payload, Decimal('100.00'))
        self.assertEqual(Booking.objects.count(), 0)

    def test_creates_booking_with_all_travelers_including_infant(self):
        from .views import _resolve_or_create_booking

        payload = self._payload([self._traveler('Ann'), self._traveler('Baby', age=0, type='child')])
        booking, amount = _resolve_or_create_booking(payload, Decimal('100.00'))
        self.assertIsNotNone(booking)
        self.assertEqual(amount, Decimal('100.00'))
        self.assertEqual(booking.travelers.count(), 2)
        self.assertEqual(booking.travelers.get(name='Baby').age, 0)
        self.assertEqual(booking.customer.email, 'ann@example.com')


class OmariAuthRequiresTravelerDetailsTests(TestCase):
    def test_incomplete_travelers_rejected_without_charging(self):
        import json
        from datetime import date, timedelta
        from unittest.mock import patch
        from django.test import Client
        from products_and_services.models import Tour

        Tour.objects.create(name='Test Gate Cruise', base_price=Decimal('50.00'), is_active=True)
        payload = {
            'msisdn': '263771234567', 'amount': '50.00', 'currency': 'USD',
            'booking_details': {
                'tour_name': 'Test Gate Cruise', 'number_of_people': 1,
                'selected_date': (date.today() + timedelta(days=7)).isoformat(),
                'travelers': [{'name': 'Ann', 'age': 30}],  # no nationality/gender/ID
            },
        }
        with patch('omari_integration.views._build_client') as build_client:
            response = Client().post('/crm-api/payments/omari/auth/', json.dumps(payload),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        build_client.assert_not_called()
