"""Staff alerts: payments with full gateway detail, booking events, and a template for every name the code uses."""
import re
from datetime import time, timedelta
from decimal import Decimal
from pathlib import Path

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from conversations.models import Contact
from customer_data.models import Booking, CustomerProfile, Payment, Traveler

BACKEND = Path(__file__).resolve().parents[1]
# Inherited from another project (online shop orders), not used by Kalai Safaris.
LEGACY_FILES = {'definitions.py', 'lead_gen_flow.py', 'simple_add_order_flow.py', 'admin_update_order_status_flow.py'}


@override_settings(STAFF_ALERT_EMAILS=['ops@kalaisafaris.com'], STAFF_ALERT_GROUPS=[], DASHBOARD_URL='https://dashboard.kalaisafaris.com')
class StaffAlertTests(TestCase):
    def setUp(self):
        contact = Contact.objects.create(whatsapp_id='263771230555', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', last_name='Moyo')
        self.customer.refresh_from_db()
        self.day = timezone.localdate() + timedelta(days=40)

    def staff_mail(self):
        return [m for m in mail.outbox if m.to == ['ops@kalaisafaris.com']]

    def booking(self, **extra):
        fields = dict(customer=self.customer, tour_name='Sunset Cruise', start_date=self.day, end_date=self.day,
                      number_of_adults=1, total_amount=Decimal('100.00'), booking_reference='BK-STAFF-1')
        fields.update(extra)
        with self.captureOnCommitCallbacks(execute=True):
            booking = Booking.objects.create(**fields)
            Traveler.objects.create(booking=booking, name='Ann Moyo', age=30, nationality='Zimbabwean',
                                    gender='female', id_number='AB1')
        return booking

    def save(self, booking, **changes):
        with self.captureOnCommitCallbacks(execute=True):
            for k, v in changes.items():
                setattr(booking, k, v)
            booking.save()

    def test_card_payment_alert_carries_gateway_details_without_card_data(self):
        from cbz_integration.models import CBZTransaction

        booking = self.booking()
        CBZTransaction.objects.create(
            merchant_reference='KS-ABC123', payment_type='card', amount=Decimal('50.00'), currency='USD',
            status='APPROVED', transaction_index='TI-998877', bank_reference='BR-445566', authorisation_code='AUTH42',
            result_code='0', result_description='Approved', masked_pan='424242******4242', card_bin='424242',
            gateway_response={'TransactionIndex': 'TI-998877', 'PAN': '4242424242424242', 'Echo': 'card 4242424242424242',
                              '_signed_card': 'SIGNED-SECRET', 'CVV': '123'},
        )
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            payment = Payment.objects.create(booking=booking, amount=Decimal('50.00'), status='successful',
                                             payment_method='cbz_card', transaction_reference='KS-ABC123')
        alert = self.staff_mail()[-1]
        self.assertIn('Payment received USD 50.00 · BK-STAFF-1', alert.subject)
        for detail in ('TI-998877', 'BR-445566', 'AUTH42', '424242******4242', 'Ann Moyo', '263771230555', 'USD 50.00'):
            self.assertIn(detail, alert.body)
        html = alert.alternatives[0][0]
        for secret in ('4242424242424242', 'SIGNED-SECRET', '"123"'):
            self.assertNotIn(secret, alert.body)
            self.assertNotIn(secret, html)
        self.assertIn('https://dashboard.kalaisafaris.com/payments?q=KS-ABC123', alert.body)
        with self.captureOnCommitCallbacks(execute=True):
            payment.notes = 'touched'
            payment.save()
        self.assertEqual(sum('Payment received' in m.subject for m in self.staff_mail()), 1)  # once per payment

    def test_omari_payment_alert(self):
        from omari_integration.models import OmariTransaction

        booking = self.booking()
        OmariTransaction.objects.create(reference='om-uuid-1', msisdn='263774000111', amount=Decimal('30'), currency='USD',
                                        status='SUCCESS', payment_reference='OMPAY77', debit_reference='DEB55', booking=booking)
        with self.captureOnCommitCallbacks(execute=True):
            Payment.objects.create(booking=booking, amount=Decimal('30.00'), status='successful',
                                   payment_method='omari', transaction_reference='OMPAY77')
        body = self.staff_mail()[-1].body
        for detail in ('Omari', 'OMPAY77', 'DEB55', '263774000111', 'om-uuid-1'):
            self.assertIn(detail, body)

    def test_reported_payments_ask_staff_to_verify_but_paynow_does_not(self):
        booking = self.booking()
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            Payment.objects.create(booking=booking, amount=Decimal('60.00'), status='pending', payment_method='bank_transfer')
            Payment.objects.create(booking=booking, amount=Decimal('60.00'), status='pending', payment_method='paynow_ecocash')
        subjects = [m.subject for m in self.staff_mail()]
        self.assertEqual(sum('Verify payment' in s for s in subjects), 1)

    def test_booking_lifecycle_events_once_each(self):
        booking = self.booking()
        self.save(booking, payment_status='deposit_paid')
        self.save(booking, payment_status='deposit_paid', number_of_adults=1)   # no change: no alert
        self.save(booking, payment_status='paid')
        self.save(booking, start_date=self.day + timedelta(days=7), end_date=self.day + timedelta(days=7), start_time=time(16, 0))
        self.save(booking, payment_status='cancelled')
        subjects = [m.subject.split(' · ')[0] for m in self.staff_mail()]
        self.assertEqual(subjects, ['[Kalai] New booking', '[Kalai] Booking confirmed', '[Kalai] Booking fully paid',
                                    '[Kalai] Booking date changed', '[Kalai] Booking cancelled'])
        moved = self.staff_mail()[3].body
        self.assertIn(f"From: {self.day}", moved)
        self.assertIn('16:00', moved)

    def test_unpaid_website_drafts_stay_quiet(self):
        draft = self.booking(booking_reference='PENDING-WEB-AB12')
        self.save(draft, payment_status='cancelled')   # nightly draft cleanup
        self.assertEqual(self.staff_mail(), [])


class TemplateCatalogueTests(TestCase):
    def test_every_whatsapp_template_the_code_uses_exists(self):
        from flows.management.commands.load_notification_templates import NOTIFICATION_TEMPLATES

        defined = {t['name'] for t in NOTIFICATION_TEMPLATES}
        pattern = re.compile(r"""template_name['"]?\s*[:=]\s*['"]([a-z0-9_]+)['"]""")
        used = set()
        for path in BACKEND.rglob('*.py'):
            if 'venv' in path.parts or 'migrations' in path.parts or path.name.startswith('test'):
                continue
            if path.name in LEGACY_FILES or 'scripts' in path.parts:
                continue
            used |= set(pattern.findall(path.read_text(errors='ignore')))
        self.assertEqual(sorted(used - defined), [])

    def test_alert_context_with_model_instances_is_stored(self):
        from django.contrib.auth.models import Group, User
        from notifications.models import Notification, NotificationTemplate
        from notifications.services import queue_notifications_to_users

        NotificationTemplate.objects.create(name='t_obj', message_body='Booking {{ booking.booking_reference }}')
        group = Group.objects.create(name='Ops')
        User.objects.create_user('ops', 'o@example.com', 'x').groups.add(group)
        day = timezone.localdate()
        booking = Booking.objects.create(tour_name='X', start_date=day, end_date=day, total_amount=1, booking_reference='BK-OBJ')
        queue_notifications_to_users(template_name='t_obj', group_names=['Ops'], template_context={'booking': booking, 'when': day})
        note = Notification.objects.get()
        self.assertIn('BK-OBJ', note.content)


@override_settings(STAFF_ALERT_EMAILS=[], PUBLIC_SITE_URL='https://kalaisafaris.com')
class BookingStatementTests(TestCase):
    def setUp(self):
        contact = Contact.objects.create(whatsapp_id='263771230666', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', email='ann@example.com')

    def paid_booking(self, ref, days, email_after_payment=False):
        day = timezone.localdate() + timedelta(days=days)
        booking = Booking.objects.create(customer_id=self.customer.pk, tour_name='Sunset Cruise', start_date=day, end_date=day,
                                         number_of_adults=1, total_amount=Decimal('100'), booking_reference=ref)
        Traveler.objects.create(booking=booking, name='Ann Moyo', age=30, nationality='Zimbabwean', gender='female', id_number='A1')
        Payment.objects.create(booking=booking, amount=Decimal('50'), status='successful', payment_method='omari', transaction_reference=f'OM-{ref}')
        Booking.objects.filter(pk=booking.pk).update(payment_status='deposit_paid', confirmation_email_sent_at=timezone.now() if email_after_payment else None)
        return booking

    def run_cmd(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('send_booking_statements', '--every', '0', *args, stdout=out)
        return out.getvalue()

    def test_once_per_paid_upcoming_booking(self):
        self.paid_booking('BK-NEEDS', 20)
        self.paid_booking('BK-TOLD', 20, email_after_payment=True)
        self.paid_booking('BK-PAST', -5)
        mail.outbox.clear()
        out = self.run_cmd('--dry-run')
        self.assertIn('Would queue 1', out)
        self.assertIn('already emailed after the last payment', out)
        self.assertEqual(mail.outbox, [])
        self.run_cmd()
        self.assertEqual(len(mail.outbox), 1)
        statement = mail.outbox[0]
        self.assertIn('BK-NEEDS', statement.subject)
        self.assertIn('OM-BK-NEEDS', statement.body)       # each payment listed
        self.assertIn('/manage/', statement.body)
        self.assertIn('Queued 0', self.run_cmd())          # deploying again sends nothing
        self.assertEqual(len(mail.outbox), 1)
