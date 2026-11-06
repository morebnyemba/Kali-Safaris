"""Branded email layer: rendering, dedupe/logging, loop protection, and the autoresponders built on it."""
import email
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.core import mail
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from conversations.models import Contact
from customer_data.models import Booking, CustomerProfile, Payment, Traveler

from .emailing import is_automated_message, send_branded_email
from .models import EmailLog


@override_settings(PUBLIC_SITE_URL='https://kalaisafaris.com')
class SendBrandedEmailTests(TestCase):
    def send(self, **extra):
        return send_branded_email(template='document_duplicate', to='Ann <ann@example.com>', subject='Hello',
                                  context={'filename': 'x.pdf', 'booking_reference': 'BK-1'}, **extra)

    def test_branded_html_and_text_with_loop_safe_headers(self):
        log = self.send(key='k1', auto_reply=True)
        self.assertEqual(log.status, 'sent')
        message = mail.outbox[0]
        html = message.alternatives[0][0]
        self.assertIn('https://kalaisafaris.com/images/kalailogo.png', html)
        self.assertIn('#C8102E', html)
        self.assertIn('BK-1', message.body)
        self.assertEqual(message.to, ['ann@example.com'])
        self.assertEqual(message.extra_headers['Auto-Submitted'], 'auto-replied')
        self.assertEqual(message.extra_headers['X-Auto-Response-Suppress'], 'All')
        self.assertEqual(message.reply_to, ['reservation@kalaisafaris.com'])

    def test_same_key_sends_once_but_a_failure_is_retried(self):
        self.send(key='once')
        self.assertIsNone(self.send(key='once'))
        self.assertEqual(len(mail.outbox), 1)
        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('smtp down')):
            with self.assertRaises(OSError):
                self.send(key='flaky')
        self.assertEqual(EmailLog.objects.get(key='flaky').status, 'failed')
        self.assertEqual(self.send(key='flaky').status, 'sent')

    def test_no_address_is_skipped_quietly(self):
        self.assertIsNone(send_branded_email(template='document_duplicate', to='', subject='x', context={}))
        self.assertEqual(EmailLog.objects.count(), 0)

    def test_every_template_renders_without_leftovers(self):
        with tempfile.TemporaryDirectory() as out:
            call_command('preview_emails', out=out, stdout=open('/dev/null', 'w'))
            files = list(Path(out).glob('*.html')) + list(Path(out).glob('*.txt'))
            self.assertGreaterEqual(len(files), 20)
            for f in files:
                text = f.read_text()
                self.assertNotIn('{{', text, f.name)
                self.assertNotIn('{%', text, f.name)


class AutomatedSenderTests(TestCase):
    def msg(self, **headers):
        raw = '\n'.join(f'{k}: {v}' for k, v in {'From': 'ann@example.com', 'Subject': 'hi', **headers}.items())
        return email.message_from_string(raw + '\n\nbody')

    def test_people_get_replies_machines_do_not(self):
        self.assertFalse(is_automated_message(self.msg()))
        self.assertFalse(is_automated_message(self.msg(**{'Auto-Submitted': 'no'})))
        for headers in (
            {'Auto-Submitted': 'auto-replied'}, {'Precedence': 'bulk'}, {'List-Id': '<news.example.com>'},
            {'X-Autoreply': 'yes'}, {'Return-Path': '<>'}, {'From': 'MAILER-DAEMON@mx.example.com'},
            {'From': 'No Reply <no-reply@bank.example>'}, {'From': 'noreply@example.com'},
        ):
            with self.subTest(headers=headers):
                self.assertTrue(is_automated_message(self.msg(**headers)))


@override_settings(PUBLIC_SITE_URL='https://kalaisafaris.com')
class CustomerEmailTests(TestCase):
    def setUp(self):
        contact = Contact.objects.create(whatsapp_id='263771239001', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', last_name='Moyo', email='ann@example.com')
        self.customer.refresh_from_db()
        day = timezone.localdate() + timedelta(days=40)
        self.booking = Booking.objects.create(customer=self.customer, tour_name='Sunset Cruise', start_date=day, end_date=day,
                                              number_of_adults=1, total_amount=Decimal('100.00'), booking_reference='BK-EMAIL-1')
        Traveler.objects.create(booking=self.booking, name='Ann Moyo', age=30, nationality='Zimbabwean', gender='female', id_number='AB1')

    def pay(self, amount):
        with self.captureOnCommitCallbacks(execute=True):
            payment = Payment.objects.create(booking=self.booking, amount=Decimal(amount), status='successful', payment_method='omari')
            booking = Booking.objects.get(pk=self.booking.pk)
            booking.payment_status = 'deposit_paid' if booking.amount_paid < booking.total_amount else 'paid'
            booking.save()
        return payment

    def test_first_payment_confirms_later_payments_get_receipts(self):
        self.pay('50.00')
        self.assertEqual([m.subject.split(':')[0] for m in mail.outbox], ['Booking confirmed'])
        self.pay('30.00')
        receipt = mail.outbox[-1]
        self.assertTrue(receipt.subject.startswith('Payment received: $30.00'))
        self.assertIn('$20.00', receipt.body)           # balance left
        self.pay('20.00')
        self.assertIn('fully paid', mail.outbox[-1].body)
        logs = list(self.booking.email_logs.values_list('template', 'status'))
        self.assertEqual(sorted(logs), sorted([('booking_confirmation', 'sent'), ('payment_receipt', 'sent'), ('payment_receipt', 'sent')]))

    @patch('meta_integration.utils.send_whatsapp_message', return_value={'ok': True})
    def test_rejected_manual_payment_is_emailed(self, _wa):
        from customer_data.payment_review import reject_payment

        payment = Payment.objects.create(booking=self.booking, amount=Decimal('50.00'), status='pending', payment_method='bank_transfer')
        with self.captureOnCommitCallbacks(execute=True):
            reject_payment(payment.pk, None, reason='Not in our account yet')
        message = mail.outbox[-1]
        self.assertIn("couldn't verify", message.subject)
        self.assertIn('Not in our account yet', message.body)

    def test_staff_see_the_email_history(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient

        self.pay('50.00')
        api = APIClient()
        api.force_authenticate(get_user_model().objects.create_user('ops', 'o@example.com', 'x', is_staff=True))
        rows = api.get(f'/crm-api/customer-data/bookings/{self.booking.pk}/emails/').json()
        self.assertEqual([(r['label'], r['status'], r['to']) for r in rows], [('Booking confirmation', 'sent', 'ann@example.com')])


@override_settings(PUBLIC_SITE_URL='https://kalaisafaris.com')
class InboundAutoReplyTests(TestCase):
    def attachment(self, name, sender='Ann <ann@example.com>', message_id='<m1@example.com>', automated=False):
        from email_integration.models import EmailAttachment
        return EmailAttachment.objects.create(file=ContentFile(b'%PDF-1.4', name=f'attachments/{name}'), filename=name,
                                              sender=sender, subject='Booking for 3', message_id=message_id, is_automated=automated)

    def test_one_reply_per_email_listing_all_attachments(self):
        from email_integration.tasks import send_receipt_confirmation_email

        first, second = self.attachment('booking.pdf'), self.attachment('passports.jpg')
        send_receipt_confirmation_email.delay(first.pk)
        send_receipt_confirmation_email.delay(second.pk)
        self.assertEqual(len(mail.outbox), 1)
        reply = mail.outbox[0]
        self.assertEqual(reply.subject, 'Re: Booking for 3')
        self.assertIn('booking.pdf', reply.body)
        self.assertIn('passports.jpg', reply.body)
        self.assertEqual(reply.extra_headers['Auto-Submitted'], 'auto-replied')

    def test_never_replies_to_automated_senders(self):
        from email_integration.tasks import send_duplicate_invoice_email, send_receipt_confirmation_email

        bounce = self.attachment('bounce.pdf', sender='MAILER-DAEMON@mx.example.com', message_id='<b@x>', automated=True)
        send_receipt_confirmation_email.delay(bounce.pk)
        send_duplicate_invoice_email.delay(bounce.pk, 'BK-1')
        self.assertEqual(mail.outbox, [])
