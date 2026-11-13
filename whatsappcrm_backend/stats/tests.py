from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from conversations.models import Contact
from customer_data.models import Booking, CustomerProfile, Payment, TourInquiry


@override_settings(STAFF_ALERT_EMAILS=[])
class NavCountsTests(TestCase):
    URL = '/crm-api/stats/nav-counts/'

    def setUp(self):
        cache.clear()
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user('ops', 'o@example.com', 'x', is_staff=True))

    def test_counts_what_needs_a_person(self):
        Contact.objects.create(whatsapp_id='263770000001', needs_human_intervention=True)
        contact = Contact.objects.create(whatsapp_id='263770000002')
        profile = CustomerProfile.objects.get_or_create(contact=contact)[0]
        TourInquiry.objects.create(customer=profile, status='new')
        TourInquiry.objects.create(customer=profile, status='contacted')
        day = timezone.localdate() + timedelta(days=40)
        booking = Booking.objects.create(tour_name='Sunset', start_date=day, end_date=day, total_amount=Decimal('100'), booking_reference='BK-1')
        Booking.objects.filter(pk=booking.pk).update(payment_status='on_hold')
        Payment.objects.create(booking=booking, amount=Decimal('10'), status='pending', payment_method='bank_transfer')
        Payment.objects.create(booking=booking, amount=Decimal('10'), status='successful', payment_method='bank_transfer')

        data = self.api.get(self.URL).json()
        self.assertEqual(data, {'inbox_attention': 1, 'payments_pending': 1, 'inquiries_new': 1,
                                'bookings_on_hold': 1, 'bookings_awaiting_details': 0})

    def test_requires_login(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)


class DashboardSummaryTests(TestCase):
    def test_handover_without_request_time_does_not_break_summary(self):
        api = APIClient()
        api.force_authenticate(get_user_model().objects.create_user('ops2', 'p@example.com', 'x', is_staff=True))
        contact = Contact.objects.create(whatsapp_id='263770000009')
        Contact.objects.filter(pk=contact.pk).update(needs_human_intervention=True, intervention_requested_at=None)
        self.assertEqual(api.get('/crm-api/stats/summary/').status_code, 200)
