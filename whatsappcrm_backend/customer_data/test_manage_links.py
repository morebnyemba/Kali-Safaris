"""Secure 'manage booking' links: ID uploads, instalments, WhatsApp pay-balance flow."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from conversations.models import Contact

from .manage_links import issue_token, manage_url, resolve_token, revoke_links
from .models import Booking, CustomerProfile, Traveler

JPEG = b'\xff\xd8\xff\xe0' + b'0' * 64
PDF = b'%PDF-1.4 ' + b'0' * 64


@override_settings(PUBLIC_SITE_URL='https://kalaisafaris.com')
class ManageLinkTests(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(whatsapp_id='263771234000', name='Ann Moyo')
        self.customer, _ = CustomerProfile.objects.get_or_create(contact=self.contact)
        CustomerProfile.objects.filter(pk=self.customer.pk).update(first_name='Ann', last_name='Moyo')
        self.customer.refresh_from_db()
        self.day = timezone.localdate() + timedelta(days=7)
        self.booking = Booking.objects.create(
            customer=self.customer, tour_name='Sunset Cruise', start_date=self.day, end_date=self.day,
            number_of_adults=2, total_amount=Decimal('200.00'), amount_paid=Decimal('100.00'), payment_status='deposit_paid',
        )
        self.ann = Traveler.objects.create(booking=self.booking, name='Ann Moyo', age=30, nationality='Zimbabwean',
                                           gender='female', id_number='AB123456')
        self.tom = Traveler.objects.create(booking=self.booking, name='Tom Moyo', age=8, nationality='Zimbabwean', gender='male')
        self.token = issue_token(self.booking)
        self.api = APIClient()

    def url(self, suffix=''):
        return f'/crm-api/customer-data/manage/{self.token}/{suffix}'

    # --- tokens ---

    def test_token_resolves_and_can_be_revoked(self):
        self.assertEqual(resolve_token(self.token), self.booking)
        self.assertTrue(manage_url(self.booking).startswith('https://kalaisafaris.com/manage/'))
        self.assertIsNone(resolve_token(self.token[:-2] + 'xx'))           # tampered
        self.assertIsNone(resolve_token('garbage'))
        revoke_links(self.booking)
        self.assertIsNone(resolve_token(self.token))
        self.assertEqual(self.api.get(self.url()).status_code, 404)

    def test_summary_never_exposes_id_numbers_or_documents(self):
        res = self.api.get(self.url())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Cache-Control'], 'no-store')
        data = res.json()
        self.assertEqual(data['balance_due'], '100.00')
        self.assertTrue(data['can_pay'])
        self.assertNotIn('AB123456', res.content.decode())
        ann = next(t for t in data['travelers'] if t['name'] == 'Ann Moyo')
        self.assertEqual((ann['has_id_number'], ann['has_document'], ann['needs_id']), (True, False, True))
        tom = next(t for t in data['travelers'] if t['name'] == 'Tom Moyo')
        self.assertFalse(tom['needs_id'])  # under 12

    # --- ID uploads ---

    def test_upload_adds_missing_document_once(self):
        doc = SimpleUploadedFile('passport.jpg', JPEG, content_type='image/jpeg')
        res = self.api.post(self.url(f'travelers/{self.ann.pk}/id/'), {'document': doc}, format='multipart')
        self.assertEqual(res.status_code, 200, res.content)
        self.ann.refresh_from_db()
        self.assertTrue(self.ann.id_document.name.endswith('.jpg'))
        again = SimpleUploadedFile('other.pdf', PDF, content_type='application/pdf')
        res = self.api.post(self.url(f'travelers/{self.ann.pk}/id/'), {'document': again}, format='multipart')
        self.assertEqual(res.status_code, 400)
        self.assertIn('already have', res.json()['detail'])

    def test_upload_rejects_non_images_whatever_the_declared_type(self):
        fake = SimpleUploadedFile('x.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
        res = self.api.post(self.url(f'travelers/{self.ann.pk}/id/'), {'document': fake}, format='multipart')
        self.assertEqual(res.status_code, 400)
        self.ann.refresh_from_db()
        self.assertFalse(self.ann.id_document)

    def test_missing_id_number_confirms_held_booking(self):
        held = Booking.objects.create(
            customer=self.customer, tour_name='Lunch Cruise', start_date=self.day, end_date=self.day,
            number_of_adults=1, total_amount=Decimal('50.00'), amount_paid=Decimal('50.00'), payment_status='paid',
        )
        Traveler.objects.create(booking=held, name='Sam Ncube', age=40, nationality='Zambian', gender='male')
        held.save()  # re-evaluates: incomplete -> held
        held.refresh_from_db()
        self.assertEqual(held.payment_status, 'awaiting_details')
        sam = held.travelers.get()
        res = self.api.post(f'/crm-api/customer-data/manage/{issue_token(held)}/travelers/{sam.pk}/id/', {'id_number': 'ZN998877'}, format='multipart')
        self.assertEqual(res.status_code, 200, res.content)
        held.refresh_from_db()
        self.assertEqual(held.payment_status, 'paid')

    def test_traveller_of_another_booking_is_rejected(self):
        other = Booking.objects.create(customer=self.customer, tour_name='X', start_date=self.day, end_date=self.day,
                                       number_of_adults=1, total_amount=Decimal('10'))
        stranger = Traveler.objects.create(booking=other, name='Zed', age=30, nationality='Zambian', gender='male')
        res = self.api.post(self.url(f'travelers/{stranger.pk}/id/'), {'id_number': 'X1'}, format='multipart')
        self.assertEqual(res.status_code, 400)

    def test_nothing_changes_after_the_trip(self):
        Booking.objects.filter(pk=self.booking.pk).update(start_date=self.day - timedelta(days=30), end_date=self.day - timedelta(days=30))
        self.assertFalse(self.api.get(self.url()).json()['can_pay'])
        res = self.api.post(self.url(f'travelers/{self.ann.pk}/id/'), {'document': SimpleUploadedFile('p.jpg', JPEG)}, format='multipart')
        self.assertEqual(res.status_code, 400)

    # --- instalments through the payment endpoints ---

    def test_payment_resolver_uses_token_and_enforces_limits(self):
        from cbz_integration.views import PricingError, _resolve_or_create_booking

        booking, amount = _resolve_or_create_booking({'manage_token': self.token}, Decimal('25.00'))
        self.assertEqual((booking, amount), (self.booking, Decimal('25.00')))
        for bad, msg in ((Decimal('150.00'), 'balance'), (Decimal('5.00'), 'smallest')):
            with self.assertRaisesMessage(PricingError, msg):
                _resolve_or_create_booking({'manage_token': self.token}, bad)
        with self.assertRaisesMessage(PricingError, 'invalid or has expired'):
            _resolve_or_create_booking({'manage_token': 'nope'}, Decimal('25.00'))

    def test_shared_reference_is_refused_for_payment(self):
        from cbz_integration.views import PricingError, _resolve_or_create_booking

        Booking.objects.filter(pk=self.booking.pk).update(booking_reference='BK-T001-SHARED')
        Booking.objects.create(customer=None, tour_name='Sunset Cruise', start_date=self.day, end_date=self.day,
                               booking_reference='BK-T001-SHARED', total_amount=Decimal('100'))
        with self.assertRaisesMessage(PricingError, 'more than one booking'):
            _resolve_or_create_booking({'booking_reference': 'BK-T001-SHARED'}, Decimal('25.00'))

    # --- staff ---

    @patch('meta_integration.utils.send_whatsapp_message', return_value={'messages': [{'id': 'x'}]})
    def test_staff_can_copy_rotate_and_send(self, send):
        staff = APIClient()
        staff.force_authenticate(get_user_model().objects.create_user('ops', 'o@example.com', 'x', is_staff=True))
        url = f'/crm-api/customer-data/bookings/{self.booking.pk}/manage-link/'
        first = staff.post(url, {}, format='json').json()['url']
        self.assertEqual(resolve_token(first.rsplit('/', 1)[1]), self.booking)
        res = staff.post(url, {'rotate': True, 'send': True}, format='json').json()
        self.assertTrue(res['sent'])
        self.assertIsNone(resolve_token(first.rsplit('/', 1)[1]))  # old link revoked
        body = send.call_args.args[2]['body']
        self.assertIn(res['url'], body)
        self.assertIn('Ann Moyo', body)          # ID still needed
        self.assertIn('$100.00', body)           # balance

    # --- WhatsApp pay-balance flow actions ---

    def test_flow_actions_only_offer_own_bookings_and_validate_amounts(self):
        from flows.actions import check_instalment_amount, load_open_bookings, select_open_booking

        stranger = Contact.objects.create(whatsapp_id='263779999999', name='Stranger')
        self.assertEqual(load_open_bookings(stranger, {}, {})['pb_state'], 'none')
        loaded = load_open_bookings(self.contact, {}, {})
        self.assertEqual(loaded['pb_state'], 'one')
        self.assertEqual(select_open_booking(stranger, {}, {'reply_id': loaded['pb_reply']}), {'pb_valid': False})
        chosen = select_open_booking(self.contact, {}, {'reply_id': loaded['pb_reply']})
        self.assertTrue(chosen['pb_valid'])
        self.assertEqual(chosen['pb_balance'], '100.00')
        self.assertEqual(chosen['pb_missing_ids'], 'Ann Moyo')
        self.assertEqual([r['id'] for r in chosen['pb_menu_rows']], ['pb_full', 'pb_part', 'pb_link'])
        self.assertTrue(all(len(r['title']) <= 24 for r in chosen['pb_menu_rows']))
        ok = check_instalment_amount(self.contact, {}, {'booking_id': chosen['pb_booking_id'], 'amount': '$40'})
        self.assertEqual((ok['pb_amount_valid'], ok['pb_amount']), (True, '40.00'))
        for amount in ('500', '2', 'lots'):
            self.assertFalse(check_instalment_amount(self.contact, {}, {'booking_id': chosen['pb_booking_id'], 'amount': amount})['pb_amount_valid'])

    def test_pay_balance_flow_definition_is_wired(self):
        from flows.definitions.pay_balance_flow import PAY_BALANCE_FLOW

        names = {s['name'] for s in PAY_BALANCE_FLOW['steps']}
        for step in PAY_BALANCE_FLOW['steps']:
            for t in step.get('transitions', []):
                self.assertIn(t['to_step'], names)
        buttons = next(s for s in PAY_BALANCE_FLOW['steps'] if s['name'] == 'ask_payment_method')['config']['message_config']['interactive']['action']['buttons']
        self.assertLessEqual(len(buttons), 3)
        self.assertTrue(all(len(b['reply']['title']) <= 20 for b in buttons))


@override_settings(PUBLIC_SITE_URL='https://kalaisafaris.com')
class PayBalanceConversationTests(TestCase):
    """Drives pay_balance_flow through the real flow engine, as WhatsApp messages would."""

    def setUp(self):
        from django.core.management import call_command
        call_command('load_flows', stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
        self.contact = Contact.objects.create(whatsapp_id='263771230001', name='Ann Moyo')
        customer, _ = CustomerProfile.objects.get_or_create(contact=self.contact)
        day = timezone.localdate() + timedelta(days=5)
        self.booking = Booking.objects.create(
            customer=customer, tour_name='Sunset Cruise', start_date=day, end_date=day, number_of_adults=1,
            total_amount=Decimal('120.00'), amount_paid=Decimal('60.00'), payment_status='deposit_paid',
        )
        Traveler.objects.create(booking=self.booking, name='Ann Moyo', age=30, nationality='Zimbabwean', gender='female', id_number='AB1')

    def say(self, text=None, reply_id=None):
        from conversations.models import Message
        from flows.services import process_message_for_flow

        if reply_id:
            data = {'type': 'interactive', 'interactive': {'type': 'list_reply', 'list_reply': {'id': reply_id, 'title': reply_id}}}
            if reply_id.startswith('pb_') and reply_id in ('pb_ecocash', 'pb_web', 'pb_cancel'):
                data = {'type': 'interactive', 'interactive': {'type': 'button_reply', 'button_reply': {'id': reply_id, 'title': reply_id}}}
        else:
            data = {'type': 'text', 'text': {'body': text}}
        msg = Message.objects.create(contact=self.contact, direction='in', message_type=data['type'],
                                     wamid=f'wamid.{Message.objects.count()}', content_payload=data)
        self.contact.refresh_from_db()
        actions = process_message_for_flow(self.contact, data, msg)
        return ' '.join(str(a) for a in actions)

    @patch('cbz_integration.flow_actions.get_cbz_payment_handler')
    def test_instalment_by_ecocash(self, handler):
        handler.return_value.initiate_ecocash_payment.return_value = {'success': True, 'reference': 'KS-1', 'status': 'pending', 'is_pending': True}
        out = self.say('pay balance')
        self.assertIn('Balance', out)
        self.assertIn('pb_part', out)
        out = self.say(reply_id='pb_part')
        self.assertIn('$10.00', out)
        out = self.say('500')
        self.assertIn('balance of $60.00', out)
        out = self.say('25')
        self.assertIn('Pay *$25.00*', out)
        self.say(reply_id='pb_ecocash')
        out = self.say('0771234567')
        self.assertIn('Approve the EcoCash prompt', out)
        kwargs = handler.return_value.initiate_ecocash_payment.call_args.kwargs
        self.assertEqual((kwargs['booking'], kwargs['amount']), (self.booking, Decimal('25.00')))

    def test_card_choice_sends_secure_link_with_amount(self):
        self.say('pay balance')
        self.say(reply_id='pb_full')
        out = self.say(reply_id='pb_web')
        self.assertIn('https://kalaisafaris.com/manage/', out)
        self.assertIn('?amount=60.00', out)
