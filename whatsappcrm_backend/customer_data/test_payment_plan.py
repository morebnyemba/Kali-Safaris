"""Deposit / instalment plan for trips >30 days away, balance due date and reminders."""
import re
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from conversations.models import Contact

from . import payment_plan
from .balance_reminders import send_balance_reminders
from .models import Booking, CustomerProfile, Payment, Traveler

REPO = Path(__file__).resolve().parents[2]


class PolicyMirrorTests(SimpleTestCase):
    def test_website_constants_match_backend(self):
        source = (REPO / 'public-website/src/lib/paymentPlan.ts').read_text()
        for name in ('INSTALMENT_MIN_DAYS_AHEAD', 'DEPOSIT_PERCENT', 'BALANCE_DUE_DAYS_BEFORE'):
            with self.subTest(name=name):
                value = int(re.search(rf"export const {name} = (\d+);", source).group(1))
                self.assertEqual(value, getattr(payment_plan, name))

    def test_rules(self):
        today = timezone.localdate()
        self.assertFalse(payment_plan.instalments_allowed(today + timedelta(days=30), today))
        self.assertTrue(payment_plan.instalments_allowed(today + timedelta(days=31), today))
        self.assertEqual(payment_plan.deposit_amount(Decimal('100.05')), Decimal('50.03'))


class WebsiteDepositCheckoutTests(TestCase):
    def setUp(self):
        from products_and_services.models import Tour
        Tour.objects.create(name='Plan Cruise', base_price=Decimal('50.00'), is_active=True)

    def payload(self, days, plan):
        return {'booking_details': {
            'tour_name': 'Plan Cruise', 'number_of_people': 2, 'payment_plan': plan,
            'selected_date': (timezone.localdate() + timedelta(days=days)).isoformat(),
            'customer': {'full_name': 'Ann Moyo', 'email': 'ann@example.com', 'phone': '0771234567'},
            'travelers': [
                {'name': n, 'age': 30, 'nationality': 'Zimbabwean', 'gender': 'female', 'id_number': f'ID-{n}', 'type': 'adult'}
                for n in ('Ann', 'Ben')
            ],
        }}

    def test_deposit_for_trip_more_than_30_days_away(self):
        from cbz_integration.views import _resolve_or_create_booking

        booking, charge = _resolve_or_create_booking(self.payload(45, 'deposit'), Decimal('50.00'))
        self.assertEqual(charge, Decimal('50.00'))
        self.assertEqual(booking.total_amount, Decimal('100.00'))  # the booking is for the full price
        self.assertEqual(booking.booking_details_payload['payment_plan'], 'deposit')

    def test_deposit_refused_for_trip_30_days_or_less(self):
        from cbz_integration.views import PricingError, _resolve_or_create_booking

        with self.assertRaisesMessage(PricingError, 'more than 30 days away'):
            _resolve_or_create_booking(self.payload(30, 'deposit'), Decimal('50.00'))
        with self.assertRaisesMessage(PricingError, 'has changed'):  # deposit amount without the deposit plan
            _resolve_or_create_booking(self.payload(45, 'full'), Decimal('50.00'))
        self.assertEqual(Booking.objects.count(), 0)

    def test_retry_cannot_undercut_the_chosen_plan(self):
        from cbz_integration.views import PricingError, _resolve_or_create_booking

        full, _ = _resolve_or_create_booking(self.payload(45, 'full'), Decimal('100.00'))
        with self.assertRaisesMessage(PricingError, 'at least $100.00'):
            _resolve_or_create_booking({'booking_reference': full.booking_reference}, Decimal('50.00'))
        deposit, _ = _resolve_or_create_booking(self.payload(60, 'deposit'), Decimal('50.00'))
        with self.assertRaisesMessage(PricingError, 'at least $50.00'):
            _resolve_or_create_booking({'booking_reference': deposit.booking_reference}, Decimal('1.00'))
        _, ok = _resolve_or_create_booking({'booking_reference': deposit.booking_reference}, Decimal('50.00'))
        self.assertEqual(ok, Decimal('50.00'))


@override_settings(PUBLIC_SITE_URL='https://kalaisafaris.com')
class BalanceDueAndReminderTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        contact = Contact.objects.create(whatsapp_id='263771230777', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', last_name='Moyo', email='ann@example.com')
        self.customer.refresh_from_db()

    def booking(self, days_ahead, paid='50.00', status='deposit_paid'):
        day = self.today + timedelta(days=days_ahead)
        booking = Booking.objects.create(
            customer=self.customer, tour_name='Sunset Cruise', start_date=day, end_date=day, number_of_adults=1,
            total_amount=Decimal('100.00'), booking_reference=f'BK-R{days_ahead}-{status}',
        )
        Traveler.objects.create(booking=booking, name='Ann Moyo', age=30, nationality='Zimbabwean', gender='female', id_number='AB1')
        Booking.objects.filter(pk=booking.pk).update(amount_paid=Decimal(paid), payment_status=status)
        booking.refresh_from_db()
        return booking

    @patch('meta_integration.utils.send_whatsapp_message', return_value=None)  # outside the 24h window
    def test_reminders_go_out_a_week_before_on_the_day_and_3_days_before_trip(self, _send):
        upcoming = self.booking(14 + 7)
        due = self.booking(14)
        final = self.booking(3)
        quiet = self.booking(20)
        settled = self.booking(14, paid='100.00', status='paid')
        sent = send_balance_reminders(self.today)
        self.assertEqual(sorted(sent), sorted([upcoming.booking_reference, due.booking_reference, final.booking_reference]))
        subjects = sorted(m.subject for m in mail.outbox)
        self.assertTrue(any('due soon' in s for s in subjects))
        self.assertTrue(any('due today' in s for s in subjects))
        self.assertTrue(any('Final reminder' in s for s in subjects))
        self.assertIn('https://kalaisafaris.com/manage/', mail.outbox[0].body)
        self.assertEqual(send_balance_reminders(self.today), [])  # once a day
        self.assertNotIn(quiet.booking_reference, sent)
        self.assertNotIn(settled.booking_reference, sent)

    @patch('meta_integration.utils.send_whatsapp_message', return_value=None)
    def test_unreached_customer_is_retried_next_run(self, _send):
        CustomerProfile.objects.filter(pk=self.customer.pk).update(email='')
        booking = self.booking(14)
        self.assertEqual(send_balance_reminders(self.today), [])
        booking.refresh_from_db()
        self.assertIsNone(booking.balance_reminder_sent_on)

    def test_api_due_date_and_filters(self):
        overdue = self.booking(10)    # due 4 days ago
        owing = self.booking(40)      # due in 26 days
        self.booking(5, paid='0.00', status='pending')  # nothing paid: not "owing"
        api = APIClient()
        api.force_authenticate(get_user_model().objects.create_user('ops', 'o@example.com', 'x', is_staff=True))
        url = '/crm-api/customer-data/bookings/'
        refs = lambda params: {b['booking_reference'] for b in api.get(url, params).json()['results']}
        self.assertEqual(refs({'balance': 'outstanding'}), {overdue.booking_reference, owing.booking_reference})
        self.assertEqual(refs({'balance': 'overdue'}), {overdue.booking_reference})
        row = next(b for b in api.get(url).json()['results'] if b['booking_reference'] == owing.booking_reference)
        self.assertEqual(row['balance_due_by'], (owing.start_date - timedelta(days=14)).isoformat())

    def test_manage_summary_and_first_payment_minimum(self):
        from .manage_links import ManageLinkError, issue_token, validate_instalment

        booking = self.booking(10)
        data = APIClient().get(f'/crm-api/customer-data/manage/{issue_token(booking)}/').json()
        self.assertTrue(data['balance_overdue'])
        self.assertEqual(data['minimum_payment'], '10.00')
        unpaid = self.booking(50, paid='0.00', status='pending')
        with self.assertRaisesMessage(ManageLinkError, 'first payment'):
            validate_instalment(unpaid, Decimal('20.00'))
        validate_instalment(unpaid, Decimal('50.00'))
        Payment.objects.create(booking=unpaid, amount=Decimal('50.00'), status='successful', payment_method='omari')
        unpaid.refresh_from_db()
        validate_instalment(unpaid, Decimal('10.00'))
