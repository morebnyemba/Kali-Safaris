"""Booking confirmation email: sent once when a booking is confirmed, never retroactively."""
import importlib
from datetime import time, timedelta
from decimal import Decimal
from unittest import mock

from django.apps import apps
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from conversations.models import Contact

from .admin import BookingAdmin
from .booking_emails import send_booking_confirmation
from .models import Booking, CustomerProfile, Traveler

backfill = importlib.import_module('customer_data.migrations.0012_booking_confirmation_email_sent_at')


@override_settings(STAFF_ALERT_EMAILS=[])  # customer emails only; staff alerts are tested in notifications
class BookingConfirmationEmailTests(TestCase):
    def setUp(self):
        contact = Contact.objects.create(whatsapp_id='263771112233', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', last_name='Moyo', email='ann@example.com')
        self.customer.refresh_from_db()
        self.day = timezone.localdate() + timedelta(days=5)

    def booking(self, **extra):
        fields = dict(
            customer=self.customer, tour_name='Sunrise Cruise', start_date=self.day, end_date=self.day,
            start_time=time(6), end_time=time(8), number_of_adults=1, total_amount=Decimal('25.00'),
            booking_reference='BK-T001-TEST-0600',
        )
        fields.update(extra)
        booking = Booking.objects.create(**fields)
        Traveler.objects.create(booking=booking, name='Ann Moyo', age=30, nationality='Zimbabwean',
                                gender='female', id_number='AB123456')
        return booking

    def pay(self, booking, status=Booking.PaymentStatus.PAID):
        with self.captureOnCommitCallbacks(execute=True):
            booking.payment_status = status
            booking.amount_paid = booking.total_amount
            booking.save()
        booking.refresh_from_db()
        return booking

    def test_sent_once_when_paid(self):
        booking = self.pay(self.booking())
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['ann@example.com'])
        self.assertIn('BK-T001-TEST-0600', email.subject)
        self.assertIn('Departs: 06:00–08:00', email.body)
        self.assertIn('Hi Ann', email.body)
        self.assertIn('Ann Moyo', email.alternatives[0][0])
        self.assertIsNotNone(booking.confirmation_email_sent_at)

        with self.captureOnCommitCallbacks(execute=True):
            booking.notes = 'edited by staff'
            booking.save()
        self.assertEqual(len(mail.outbox), 1)

    def test_not_sent_when_not_wanted(self):
        self.pay(self.booking(), status=Booking.PaymentStatus.PENDING_MANUAL)                       # not confirmed
        self.pay(self.booking(start_date=timezone.localdate() - timedelta(days=1)))                   # trip already happened
        self.pay(self.booking(booking_reference='PENDING-WEB-ABC123'))                                # temporary reference
        CustomerProfile.objects.filter(pk=self.customer.pk).update(email='')
        self.customer.refresh_from_db()
        self.pay(self.booking(booking_reference='BK-NOEMAIL'))                                        # no address
        self.assertEqual(mail.outbox, [])

    def test_waits_for_real_reference_then_sends(self):
        booking = self.pay(self.booking(booking_reference='PENDING-WEB-XYZ'))
        self.assertEqual(mail.outbox, [])
        with self.captureOnCommitCallbacks(execute=True):
            booking.booking_reference = 'BK-T001-REAL'
            booking.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('BK-T001-REAL', mail.outbox[0].subject)

    def test_website_checkout_email_used_when_profile_has_none(self):
        CustomerProfile.objects.filter(pk=self.customer.pk).update(email='')
        self.customer.refresh_from_db()
        self.pay(self.booking(booking_details_payload={'customer': {'email': 'web@example.com'}}))
        self.assertEqual(mail.outbox[0].to, ['web@example.com'])

    def test_failed_send_is_released_for_retry(self):
        booking = self.booking()
        Booking.objects.filter(pk=booking.pk).update(payment_status=Booking.PaymentStatus.PAID)
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('smtp down')):
            with self.assertRaises(OSError):
                send_booking_confirmation(booking.pk)
        booking.refresh_from_db()
        self.assertIsNone(booking.confirmation_email_sent_at)
        self.assertTrue(send_booking_confirmation(booking.pk))
        self.assertFalse(send_booking_confirmation(booking.pk))
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_resend(self):
        booking = self.pay(self.booking())
        admin = BookingAdmin(Booking, AdminSite())
        request = RequestFactory().post('/')
        request.user = get_user_model().objects.create_superuser('root', 'root@example.com', 'x')
        with mock.patch.object(admin, 'message_user'):
            admin.resend_confirmation_email(request, Booking.objects.filter(pk=booking.pk))
        self.assertEqual(len(mail.outbox), 2)

    def test_backfill_marks_existing_confirmed_bookings(self):
        old_paid = self.booking(booking_reference='BK-OLD-1')
        Booking.objects.filter(pk=old_paid.pk).update(payment_status=Booking.PaymentStatus.PAID)
        pending = self.booking(booking_reference='BK-OLD-2')
        backfill.mark_existing_confirmed_as_sent(apps, None)
        old_paid.refresh_from_db()
        pending.refresh_from_db()
        self.assertIsNotNone(old_paid.confirmation_email_sent_at)
        self.assertIsNone(pending.confirmation_email_sent_at)
