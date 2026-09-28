"""
Tests for linking website checkouts to customers (which drives the group name
shown on passenger manifests).
"""
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
