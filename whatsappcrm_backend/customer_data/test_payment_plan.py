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
from .balance_reminders import move_unpaid_to_hold, send_balance_reminders
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
    def test_notices_a_week_before_due_and_a_final_warning_once(self, _send):
        upcoming = self.booking(10 + 7)
        due = self.booking(10)
        late = self.booking(9)          # booked/deposited after its due date: still gets the warning first
        quiet = self.booking(20)
        settled = self.booking(10, paid='100.00', status='paid')
        sent = send_balance_reminders(self.today)
        self.assertEqual(sorted(sent), sorted([upcoming.booking_reference, due.booking_reference, late.booking_reference]))
        subjects = [m.subject for m in mail.outbox]
        self.assertTrue(any('due soon' in s for s in subjects))
        final = [m for m in mail.outbox if 'Action needed' in m.subject]
        self.assertEqual(len(final), 2)
        move_on = (self.today + timedelta(days=2)).strftime('%d %b')
        self.assertIn(move_on, final[0].subject)
        self.assertIn('moved off this cruise', final[0].body)
        self.assertIn('https://kalaisafaris.com/manage/', final[0].body)
        due.refresh_from_db()
        self.assertEqual(due.final_notice_sent_on, self.today)
        self.assertEqual(send_balance_reminders(self.today), [])                       # once a day
        self.assertEqual(send_balance_reminders(self.today + timedelta(days=1)), [])  # the final notice only once
        self.assertNotIn(quiet.booking_reference, sent)
        self.assertNotIn(settled.booking_reference, sent)

    @patch('meta_integration.utils.send_whatsapp_message', return_value=None)
    def test_unreached_customer_is_retried_and_never_moved_unwarned(self, _send):
        CustomerProfile.objects.filter(pk=self.customer.pk).update(email='')
        booking = self.booking(10)
        self.assertEqual(send_balance_reminders(self.today), [])
        booking.refresh_from_db()
        self.assertIsNone(booking.balance_reminder_sent_on)
        self.assertIsNone(booking.final_notice_sent_on)
        self.assertEqual(move_unpaid_to_hold(self.today + timedelta(days=3)), [])

    @patch('meta_integration.utils.send_whatsapp_message', return_value=None)
    def test_unpaid_48h_after_final_notice_moves_to_hold_and_frees_seats(self, _send):
        from products_and_services.departures import seats_taken
        from products_and_services.models import Tour, TourTimeSlot
        from datetime import time

        tour = Tour.objects.create(name='Hold Cruise', base_price=Decimal('100.00'), is_active=True)
        TourTimeSlot.objects.create(tour=tour, start_time=time(16, 0), end_time=time(18, 0), capacity=10, is_active=True)
        booking = self.booking(10)
        paid_up = self.booking(10)
        Booking.objects.filter(pk__in=[booking.pk, paid_up.pk]).update(tour=tour, start_time=time(16, 0))
        send_balance_reminders(self.today)
        self.assertEqual(seats_taken(tour, booking.start_date, time(16, 0)), 2)

        self.assertEqual(move_unpaid_to_hold(self.today + timedelta(days=1)), [])      # grace not over
        Booking.objects.filter(pk=paid_up.pk).update(amount_paid=Decimal('100.00'), payment_status='paid')
        with self.captureOnCommitCallbacks(execute=True):
            moved = move_unpaid_to_hold(self.today + timedelta(days=2))
        self.assertEqual(moved, [booking.booking_reference])
        booking.refresh_from_db()
        self.assertEqual(booking.payment_status, 'on_hold')
        self.assertEqual(booking.held_from_date, self.today + timedelta(days=10))
        self.assertEqual(booking.amount_paid, Decimal('50.00'))  # credit kept
        self.assertEqual(seats_taken(tour, booking.start_date, time(16, 0)), 1)  # its seat is free again
        self.assertTrue(any('on hold' in m.subject for m in mail.outbox))

    def test_customer_reschedules_an_on_hold_booking(self):
        from products_and_services.models import Tour, TourTimeSlot
        from datetime import time
        from .manage_links import issue_token

        tour = Tour.objects.create(name='Hold Cruise', base_price=Decimal('100.00'), is_active=True)
        TourTimeSlot.objects.create(tour=tour, start_time=time(16, 0), end_time=time(18, 0), capacity=1, is_active=True)
        booking = self.booking(9)
        Booking.objects.filter(pk=booking.pk).update(
            tour=tour, start_time=time(16, 0), payment_status='on_hold', held_from_date=booking.start_date, held_at=timezone.now())
        url = f'/crm-api/customer-data/manage/{issue_token(booking)}/'
        api = APIClient()
        data = api.get(url).json()
        self.assertTrue(data['on_hold'] and data['can_reschedule'])
        self.assertFalse(data['can_pay'])

        soon = (self.today + timedelta(days=20)).isoformat()
        self.assertIn('more than 30 days', api.post(url + 'reschedule/', {'date': soon, 'time': '16:00'}, format='json').json()['detail'])
        later = self.today + timedelta(days=45)
        full = self.booking(45)
        Booking.objects.filter(pk=full.pk).update(tour=tour, start_time=time(16, 0))  # takes the only seat
        self.assertIn('enough seats', api.post(url + 'reschedule/', {'date': later.isoformat(), 'time': '16:00'}, format='json').json()['detail'])
        Booking.objects.filter(pk=full.pk).update(payment_status='cancelled')
        res = api.post(url + 'reschedule/', {'date': later.isoformat(), 'time': '16:00'}, format='json')
        self.assertEqual(res.status_code, 200, res.content)
        booking.refresh_from_db()
        self.assertEqual((booking.start_date, booking.payment_status), (later, 'deposit_paid'))
        self.assertEqual(booking.amount_paid, Decimal('50.00'))
        self.assertTrue(res.json()['can_pay'])
        self.assertEqual(res.json()['balance_due_by'], (later - timedelta(days=10)).isoformat())

    def test_api_due_date_and_filters(self):
        overdue = self.booking(8)     # due 2 days ago
        owing = self.booking(40)      # due in 30 days
        self.booking(5, paid='0.00', status='pending')  # nothing paid: not "owing"
        api = APIClient()
        api.force_authenticate(get_user_model().objects.create_user('ops', 'o@example.com', 'x', is_staff=True))
        url = '/crm-api/customer-data/bookings/'
        refs = lambda params: {b['booking_reference'] for b in api.get(url, params).json()['results']}
        self.assertEqual(refs({'balance': 'outstanding'}), {overdue.booking_reference, owing.booking_reference})
        self.assertEqual(refs({'balance': 'overdue'}), {overdue.booking_reference})
        row = next(b for b in api.get(url).json()['results'] if b['booking_reference'] == owing.booking_reference)
        self.assertEqual(row['balance_due_by'], (owing.start_date - timedelta(days=payment_plan.BALANCE_DUE_DAYS_BEFORE)).isoformat())

    def test_manage_summary_and_first_payment_minimum(self):
        from .manage_links import ManageLinkError, issue_token, validate_instalment

        booking = self.booking(8)
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


class WhatsAppDepositGuardTests(SimpleTestCase):
    def test_bot_offers_deposit_only_more_than_30_days_ahead(self):
        from flows.actions import check_deposit_allowed

        today = timezone.localdate()
        far, near = today + timedelta(days=45), today + timedelta(days=12)
        self.assertTrue(check_deposit_allowed(None, {}, {'start_date': far.isoformat()})['deposit_allowed'])
        self.assertTrue(check_deposit_allowed(None, {}, {'start_date': far.strftime('%d/%m/%Y')})['deposit_allowed'])
        self.assertFalse(check_deposit_allowed(None, {}, {'start_date': near.isoformat()})['deposit_allowed'])
        self.assertFalse(check_deposit_allowed(None, {}, {'start_date': 'next week'})['deposit_allowed'])

    def test_booking_flow_routes_deposits_through_the_guard(self):
        from flows.definitions.booking_flow import BOOKING_FLOW

        steps = {s['name']: s for s in BOOKING_FLOW['steps']}
        targets = {t['condition_config'].get('value'): t['to_step'] for t in steps['ask_payment_option']['transitions']}
        self.assertEqual(targets['cbz_deposit'], 'check_deposit_cbz')
        self.assertEqual(targets['card_web_deposit'], 'check_deposit_card_web')
        for name in ('check_deposit_cbz', 'check_deposit_card_web', 'deposit_not_available'):
            for t in steps[name]['transitions']:
                self.assertIn(t['to_step'], steps)
