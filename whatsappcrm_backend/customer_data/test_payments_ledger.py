"""Payments ledger API: filters, totals and staff review of manual payments."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from conversations.models import Contact

from .models import Booking, CustomerProfile, Payment, Traveler

URL = '/crm-api/customer-data/payments/'


class PaymentsLedgerTests(TestCase):
    def setUp(self):
        contact = Contact.objects.create(whatsapp_id='263771110000', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', last_name='Moyo')
        day = timezone.localdate() + timedelta(days=5)
        self.booking = Booking.objects.create(
            customer=self.customer, tour_name='Sunset Cruise', start_date=day, end_date=day,
            number_of_adults=1, total_amount=Decimal('100.00'), payment_status='pending_manual',
        )
        Traveler.objects.create(booking=self.booking, name='Ann Moyo', age=30, nationality='Zimbabwean',
                                gender='female', id_number='AB123456')
        self.card = Payment.objects.create(booking=self.booking, amount=Decimal('40.00'), status='successful',
                                           payment_method='cbz_card', transaction_reference='CBZ-1')
        self.manual = Payment.objects.create(booking=self.booking, amount=Decimal('60.00'), status='pending',
                                             payment_method='bank_transfer')
        Payment.objects.create(booking=self.booking, amount=Decimal('5.00'), status='successful',
                               payment_method='omari', currency='ZWG')
        User = get_user_model()
        self.staff = APIClient()
        self.staff.force_authenticate(User.objects.create_user('fin', 'f@example.com', 'x', is_staff=True))
        self.agent = APIClient()
        self.agent.force_authenticate(User.objects.create_user('agent', 'a@example.com', 'x'))

    def test_list_carries_booking_context_and_filters(self):
        rows = self.staff.get(URL, {'search': 'moyo'}).json()['results']
        self.assertEqual(len(rows), 3)
        row = next(r for r in rows if r['transaction_reference'] == 'CBZ-1')
        self.assertEqual(row['customer_name'], 'Ann Moyo')
        self.assertEqual(row['booking_reference'], self.booking.booking_reference)
        self.assertEqual(row['tour_name'], 'Sunset Cruise')
        self.assertEqual(self.staff.get(URL, {'status': 'pending'}).json()['count'], 1)
        today = timezone.localdate().isoformat()
        self.assertEqual(self.staff.get(URL, {'date_from': today, 'date_to': today}).json()['count'], 3)
        self.assertEqual(self.staff.get(URL, {'date_to': '2000-01-01'}).json()['count'], 0)

    def test_summary_never_mixes_currencies(self):
        data = self.staff.get(URL + 'summary/').json()
        self.assertEqual(data['by_status']['successful'], {'count': 2, 'totals': {'USD': '40.00', 'ZWG': '5.00'}})
        self.assertEqual(data['by_status']['pending']['totals'], {'USD': '60.00'})
        self.assertEqual({(m['payment_method'], m['currency']) for m in data['by_method']}, {('cbz_card', 'USD'), ('omari', 'ZWG')})

    @patch('meta_integration.utils.send_whatsapp_message')
    def test_approve_confirms_booking_once(self, send):
        with self.captureOnCommitCallbacks(execute=True):
            res = self.staff.post(f'{URL}{self.manual.pk}/approve/')
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()['status'], 'successful')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.amount_paid, Decimal('105.00'))  # sums every successful row
        self.assertEqual(self.booking.payment_status, 'paid')
        self.assertTrue(send.called)
        self.assertEqual(self.staff.post(f'{URL}{self.manual.pk}/approve/').status_code, 409)

    @patch('meta_integration.utils.send_whatsapp_message')
    def test_reject_keeps_totals_and_records_reason(self, send):
        res = self.staff.post(f'{URL}{self.manual.pk}/reject/', {'reason': 'Amount not received'}, format='json')
        self.assertEqual(res.status_code, 200, res.content)
        self.manual.refresh_from_db()
        self.assertEqual(self.manual.status, 'failed')
        self.assertIn('Amount not received', self.manual.notes)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, 'pending_manual')

    def test_only_staff_can_review(self):
        self.assertEqual(self.agent.get(URL).status_code, 200)
        self.assertEqual(self.agent.post(f'{URL}{self.manual.pk}/approve/').status_code, 403)

    def test_bookings_filter_by_tour_date_range(self):
        day = self.booking.start_date.isoformat()
        url = '/crm-api/customer-data/bookings/'
        self.assertEqual(self.staff.get(url, {'start_date__gte': day, 'start_date__lte': day}).json()['count'], 1)
        self.assertEqual(self.staff.get(url, {'start_date__lte': '2000-01-01'}).json()['count'], 0)
