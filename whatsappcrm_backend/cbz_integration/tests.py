"""
Tests for CBZ/iVeri payment integration.
"""
import json

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory
from django.utils import timezone

from conversations.models import Contact
from customer_data.models import Booking, CustomerProfile

from .admin import CBZConfigAdmin, CBZConfigAdminForm
from .models import CBZConfig, CBZTransaction
from .services import IVeriClient, IVeriConfig, IVeriCertificateClient, IVeriCertificateConfig
from .views import (
    cbz_public_config_view,
    cbz_ecocash_debit_view,
    cbz_card_debit_view,
    cbz_card_3ds_complete_view,
    cbz_certificate_generate_view,
    cbz_certificate_renew_view,
)
from .constants import (
    ECOCASH_PAN_PREFIX, ECOCASH_DEFAULT_EXPIRY,
    RESULT_CODE_SUCCESS, STATUS_APPROVED,
    COMMAND_DEBIT, IVERI_API_VERSION, IVERI_QUERY_PARAM_MERCHANT_REF,
    IVERI_STATUS_MAP, IVERI_RETRIABLE_CODES, IVERI_TERMINAL_FAILURE_CODES,
)
from .gateway import PaymentGatewayFactory, IVeriGateway, PaymentProcessor
from .views import cbz_callback_view


class IVeriClientPanEncodingTest(TestCase):
    """Test EcoCash PAN encoding logic."""

    def test_pan_from_international_format(self):
        """2637XXXXXXXX → 9100120XXXXXXXXX"""
        pan = IVeriClient._format_ecocash_pan('263771234567')
        self.assertEqual(pan, f'{ECOCASH_PAN_PREFIX}0771234567')

    def test_pan_from_local_format(self):
        """07XXXXXXXX → 910012 + 07XXXXXXXX"""
        pan = IVeriClient._format_ecocash_pan('0771234567')
        self.assertEqual(pan, f'{ECOCASH_PAN_PREFIX}0771234567')

    def test_pan_from_short_format(self):
        """771234567 (9 digits, no leading 0) → 910012 + 0771234567"""
        pan = IVeriClient._format_ecocash_pan('771234567')
        self.assertEqual(pan, f'{ECOCASH_PAN_PREFIX}0771234567')


class IVeriClientPayloadTest(TestCase):
    """Test API payload construction."""

    def setUp(self):
        self.config = IVeriConfig(
            portal_url='https://portal.host.iveri.com',
            certificate_id='test-cert-id-1234',
            application_id='test-app-id-5678',
            mode='Test',
        )

    @patch('cbz_integration.services.IVeriClient._load_config_from_db', return_value=None)
    def test_build_payload_structure(self, mock_db):
        """Verify payload structure matches iVeri REST API spec."""
        client = IVeriClient(config=self.config)
        payload = client._build_payload(COMMAND_DEBIT, {
            'Currency': 'USD',
            'Amount': '1050',
            'PAN': '9100120771234567',
            'ExpiryDate': ECOCASH_DEFAULT_EXPIRY,
            'MerchantReference': 'TEST-REF-001',
        })

        self.assertEqual(payload['Version'], IVERI_API_VERSION)
        self.assertEqual(payload['CertificateID'], 'test-cert-id-1234')
        self.assertEqual(payload['Direction'], 'Request')
        self.assertEqual(payload['Transaction']['ApplicationID'], 'test-app-id-5678')
        self.assertEqual(payload['Transaction']['Command'], COMMAND_DEBIT)
        self.assertEqual(payload['Transaction']['Mode'], 'Test')
        self.assertEqual(payload['Transaction']['Amount'], '1050')
        self.assertEqual(payload['Transaction']['Currency'], 'USD')

    @patch('cbz_integration.services.IVeriClient._load_config_from_db', return_value=None)
    def test_amount_conversion_to_cents(self, mock_db):
        """Verify amount is converted to cents correctly."""
        client = IVeriClient(config=self.config)

        # Mock the _execute method to capture the payload
        with patch.object(client, '_execute') as mock_execute:
            mock_execute.return_value = {
                'Transaction': {
                    'ResultCode': '0',
                    'Status': 'Approved',
                }
            }

            client.debit_ecocash(
                mobile='0771234567',
                amount=Decimal('10.50'),
                currency='USD',
                merchant_reference='TEST-001',
            )

            # Check the payload passed to _execute
            call_payload = mock_execute.call_args[0][0]
            self.assertEqual(call_payload['Transaction']['Amount'], '1050')

    @patch('cbz_integration.services.IVeriClient._load_config_from_db', return_value=None)
    def test_query_transaction_uses_query_string(self, mock_db):
        """Status lookups are not a Command — iVeri has no Transaction:Lookup or
        Enquiry:Lookup (both rejected as "Unknown Category:Command combination").
        The query goes as a URL query-string parameter on POST /api/transactions,
        with no Command in the body — just the Legacy-auth envelope."""
        client = IVeriClient(config=self.config)

        with patch.object(client, '_execute') as mock_execute:
            mock_execute.return_value = {'Transaction': {'ResultCode': '0', 'Status': 'Approved'}}

            client.query_transaction(merchant_reference='TEST-REF-001')

            call_args, call_kwargs = mock_execute.call_args
            payload = call_args[0]
            # No command body — neither financial nor (invalid) enquiry command.
            self.assertNotIn('Transaction', payload)
            self.assertNotIn('Enquiry', payload)
            self.assertNotIn('Command', payload)
            # Legacy auth still travels in the body.
            self.assertEqual(payload['CertificateID'], 'test-cert-id-1234')
            # The transaction identifier travels in the query string instead.
            params = call_kwargs.get('params') or {}
            self.assertEqual(params[IVERI_QUERY_PARAM_MERCHANT_REF], 'TEST-REF-001')

    def test_missing_certificate_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            IVeriClient(config=IVeriConfig(
                portal_url='https://portal.host.iveri.com',
                certificate_id='',
                application_id='test-app-id-5678',
                mode='Test',
            ))

    def test_missing_application_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            IVeriClient(config=IVeriConfig(
                portal_url='https://portal.host.iveri.com',
                certificate_id='test-cert-id-1234',
                application_id='',
                mode='Test',
            ))


class IVeriClientResponseTest(TestCase):
    """Test response parsing."""

    def test_is_approved_success(self):
        response = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': STATUS_APPROVED,
            }
        }
        self.assertTrue(IVeriClient.is_approved(response))

    def test_is_approved_declined(self):
        response = {
            'Transaction': {
                'ResultCode': '05',
                'Status': 'Declined',
            }
        }
        self.assertFalse(IVeriClient.is_approved(response))

    def test_is_pending_successful_non_approved_response(self):
        response = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': 'Pending',
            }
        }
        self.assertTrue(IVeriClient.is_pending(response))
        self.assertFalse(IVeriClient.is_approved(response))

    def test_is_pending_when_transaction_index_present_without_status(self):
        response = {
            'Transaction': {
                'TransactionIndex': '6A00B3A1-1B5F-4221-81BF-6BD700548AD1',
                'ResultCode': None,
                'Status': None,
            }
        }
        self.assertTrue(IVeriClient.is_pending(response))
        self.assertFalse(IVeriClient.is_approved(response))

    def test_get_result_extracts_fields(self):
        response = {
            'Transaction': {
                'ResultCode': '0',
                'ResultDescription': 'Success',
                'Status': 'Approved',
                'TransactionIndex': 'TXN-INDEX-123',
                'AuthorisationCode': 'AUTH-456',
                'MerchantReference': 'REF-789',
                'Amount': '1050',
                'Currency': 'USD',
                'RequestID': 'REQ-001',
            }
        }
        result = IVeriClient.get_result(response)
        self.assertEqual(result['result_code'], '0')
        self.assertEqual(result['transaction_index'], 'TXN-INDEX-123')
        self.assertEqual(result['authorisation_code'], 'AUTH-456')
        self.assertEqual(result['merchant_reference'], 'REF-789')

    def test_is_3ds_required_detects_common_challenge_fields(self):
        response = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': 'Pending',
                'ACSURL': 'https://acs.example/challenge',
                'PaReq': 'pareq-data',
            }
        }

        self.assertTrue(IVeriClient.is_3ds_required(response))
        challenge = IVeriClient.get_3ds_challenge_data(response)
        self.assertEqual(challenge['ACSURL'], 'https://acs.example/challenge')
        self.assertEqual(challenge['PaReq'], 'pareq-data')


class CBZConfigModelTest(TestCase):
    """Test CBZConfig model."""

    def test_create_config(self):
        config = CBZConfig.objects.create(
            name='Test Config',
            portal_url='https://portal.host.iveri.com',
            certificate_id='test-cert-id',
            application_id='test-app-id',
            mode='Test',
            is_active=True,
        )
        self.assertTrue(config.is_active)
        self.assertIn('Test Config', str(config))

    def test_only_one_active_config(self):
        CBZConfig.objects.create(
            name='Config 1',
            portal_url='https://portal.host.iveri.com',
            certificate_id='cert-1',
            application_id='app-1',
            mode='Test',
            is_active=True,
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            CBZConfig.objects.create(
                name='Config 2',
                portal_url='https://portal.host.iveri.com',
                certificate_id='cert-2',
                application_id='app-2',
                mode='Test',
                is_active=True,
            )

    def test_get_active_config(self):
        CBZConfig.objects.create(
            name='Active Config',
            portal_url='https://portal.host.iveri.com',
            certificate_id='cert-active',
            application_id='app-active',
            mode='Test',
            is_active=True,
        )
        active = CBZConfig.get_active_config()
        self.assertIsNotNone(active)
        self.assertEqual(active.name, 'Active Config')


class CBZConfigAdminLifecycleTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CBZConfigAdmin(CBZConfig, self.site)
        self.factory = RequestFactory()

    @patch.object(CBZConfigAdmin, 'message_user')
    @patch('cbz_integration.admin.build_certificate_client_from_settings')
    def test_admin_can_generate_certificate_on_save(self, mock_build_client, mock_message_user):
        mock_client = MagicMock()
        mock_client.generate_certificate_id.return_value = {
            'certificate_id': 'cert-generated',
            'raw': {},
        }
        mock_build_client.return_value = mock_client

        form = CBZConfigAdminForm(data={
            'name': 'Generated Config',
            'portal_url': 'https://portal.host.iveri.com',
            'certificate_id': '',
            'application_id': 'test-app-id',
            'mode': 'Test',
            'is_active': 'on',
            'callback_url': '',
            'auto_generate_certificate': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)

        obj = form.save(commit=False)
        request = self.factory.post('/admin/cbz_integration/cbzconfig/add/')
        self.admin.save_model(request, obj, form, change=False)

        obj.refresh_from_db()
        self.assertEqual(obj.certificate_id, 'cert-generated')
        mock_client.generate_certificate_id.assert_called_once_with()
        mock_message_user.assert_called_once()

    @patch.object(CBZConfigAdmin, 'message_user')
    @patch('cbz_integration.admin.build_certificate_client_from_settings')
    def test_admin_can_renew_certificate_on_save(self, mock_build_client, mock_message_user):
        mock_client = MagicMock()
        mock_client.renew_certificate_id.return_value = {
            'certificate_id': 'cert-renewed',
            'previous_certificate_id': 'cert-old',
            'raw': {},
        }
        mock_build_client.return_value = mock_client

        config = CBZConfig.objects.create(
            name='Renew Config',
            portal_url='https://portal.host.iveri.com',
            certificate_id='cert-old',
            application_id='test-app-id',
            mode='Test',
            is_active=True,
        )

        form = CBZConfigAdminForm(data={
            'name': 'Renew Config',
            'portal_url': 'https://portal.host.iveri.com',
            'certificate_id': 'cert-old',
            'application_id': 'test-app-id',
            'mode': 'Test',
            'is_active': 'on',
            'callback_url': '',
            'auto_renew_certificate': 'on',
        }, instance=config)
        self.assertTrue(form.is_valid(), form.errors)

        obj = form.save(commit=False)
        request = self.factory.post(f'/admin/cbz_integration/cbzconfig/{config.pk}/change/')
        self.admin.save_model(request, obj, form, change=True)

        config.refresh_from_db()
        self.assertEqual(config.certificate_id, 'cert-renewed')
        mock_client.renew_certificate_id.assert_called_once_with(certificate_id='cert-old')
        mock_message_user.assert_called_once()

    def test_admin_form_disallows_generate_and_renew_together(self):
        form = CBZConfigAdminForm(data={
            'name': 'Invalid Config',
            'portal_url': 'https://portal.host.iveri.com',
            'certificate_id': 'cert-old',
            'application_id': 'test-app-id',
            'mode': 'Test',
            'is_active': 'on',
            'callback_url': '',
            'auto_generate_certificate': 'on',
            'auto_renew_certificate': 'on',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('Select only one certificate action per save.', form.non_field_errors())


class CBZTransactionModelTest(TestCase):
    """Test CBZTransaction model."""

    def test_create_ecocash_transaction(self):
        txn = CBZTransaction.objects.create(
            merchant_reference='KS-TEST001',
            payment_type=CBZTransaction.PaymentType.ECOCASH,
            msisdn='263771234567',
            amount=Decimal('10.50'),
            currency='USD',
            command='Debit',
        )
        self.assertEqual(txn.status, CBZTransaction.TransactionStatus.INITIATED)
        self.assertFalse(txn.is_successful)

    def test_create_card_transaction(self):
        txn = CBZTransaction.objects.create(
            merchant_reference='KS-TEST002',
            payment_type=CBZTransaction.PaymentType.CARD,
            masked_pan='5413****0020',
            amount=Decimal('150.00'),
            currency='USD',
            command='Debit',
        )
        self.assertEqual(txn.payment_type, 'card')
        self.assertIsNone(txn.msisdn)

    def test_is_successful_property(self):
        txn = CBZTransaction.objects.create(
            merchant_reference='KS-TEST003',
            payment_type=CBZTransaction.PaymentType.ECOCASH,
            msisdn='263771234567',
            amount=Decimal('5.00'),
            currency='USD',
            status=CBZTransaction.TransactionStatus.APPROVED,
        )
        self.assertTrue(txn.is_successful)


class CBZFlowActionTests(TestCase):
    def setUp(self):
        today = timezone.now().date()
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='CBZ Tester',
        )
        self.customer = CustomerProfile.objects.create(contact=self.contact)
        self.booking = Booking.objects.create(
            customer=self.customer,
            booking_reference='CBZ-BOOKING-001',
            total_amount=Decimal('150.00'),
            amount_paid=Decimal('0.00'),
            payment_status='pending',
            start_date=today,
            end_date=today,
        )

    @patch('cbz_integration.flow_actions.get_cbz_payment_handler')
    def test_initiate_payment_sets_approved_context(self, mock_get_handler):
        from cbz_integration.flow_actions import initiate_cbz_ecocash_payment_action

        mock_handler = MagicMock()
        mock_handler.initiate_ecocash_payment.return_value = {
            'success': True,
            'reference': 'CBZ-REF-123',
            'status': 'approved',
        }
        mock_get_handler.return_value = mock_handler

        flow_context = {'payment_phone': '263771234567'}
        params = {
            'booking_reference': 'CBZ-BOOKING-001',
            'amount': '150.00',
            'currency': 'USD',
            'msisdn': '263771234567',
        }

        result = initiate_cbz_ecocash_payment_action(self.contact, flow_context, params)

        self.assertEqual(result, [])
        self.assertEqual(flow_context['cbz_payment_status'], 'approved')
        self.assertTrue(flow_context['cbz_payment_success'])
        self.assertEqual(flow_context['cbz_payment_reference'], 'CBZ-REF-123')

    @patch('cbz_integration.flow_actions.get_cbz_payment_handler')
    def test_initiate_payment_sets_pending_context(self, mock_get_handler):
        from cbz_integration.flow_actions import initiate_cbz_ecocash_payment_action

        mock_handler = MagicMock()
        mock_handler.initiate_ecocash_payment.return_value = {
            'success': True,
            'reference': 'CBZ-REF-PENDING',
            'status': 'pending',
            'is_pending': True,
            'message': 'Awaiting customer confirmation',
        }
        mock_get_handler.return_value = mock_handler

        flow_context = {'payment_phone': '263771234567'}
        params = {
            'booking_reference': 'CBZ-BOOKING-001',
            'amount': '150.00',
            'currency': 'USD',
            'msisdn': '263771234567',
        }

        result = initiate_cbz_ecocash_payment_action(self.contact, flow_context, params)

        self.assertEqual(result, [])
        self.assertEqual(flow_context['cbz_payment_status'], 'pending')
        self.assertNotIn('cbz_payment_success', flow_context)
        self.assertEqual(flow_context['cbz_payment_reference'], 'CBZ-REF-PENDING')

    @patch('cbz_integration.flow_actions.CBZConfig.get_active_config')
    @patch('cbz_integration.flow_actions.get_cbz_payment_handler')
    def test_initiate_payment_test_mode_uses_configured_msisdn(self, mock_get_handler, mock_get_active_config):
        from cbz_integration.flow_actions import initiate_cbz_ecocash_payment_action

        mock_get_active_config.return_value = CBZConfig(mode='Test', application_id='app-id')
        mock_handler = MagicMock()
        mock_handler.initiate_ecocash_payment.return_value = {
            'success': True,
            'reference': 'CBZ-REF-TEST-001',
            'status': 'pending',
            'is_pending': True,
        }
        mock_get_handler.return_value = mock_handler

        flow_context = {'payment_phone': '263799999999'}
        params = {
            'booking_reference': 'CBZ-BOOKING-001',
            'amount': '150.00',
            'currency': 'USD',
            'msisdn': '263799999999',
        }

        with self.settings(CBZ_TEST_ECOCASH_MSISDNS='263771234567,0773501244'):
            initiate_cbz_ecocash_payment_action(self.contact, flow_context, params)

        called_kwargs = mock_handler.initiate_ecocash_payment.call_args.kwargs
        self.assertEqual(called_kwargs['msisdn'], '263771234567')
        self.assertEqual(flow_context['cbz_test_msisdn_used'], '263771234567')

    def test_booking_flow_routes_ecocash_to_cbz_action(self):
        from flows.definitions.booking_flow import BOOKING_FLOW

        process_step = next(
            step for step in BOOKING_FLOW['steps']
            if step['name'] == 'process_payment_flow_response'
        )
        cbz_step = next(
            step for step in BOOKING_FLOW['steps']
            if step['name'] == 'initiate_cbz_payment_api'
        )

        self.assertEqual(
            process_step['transitions'][0]['to_step'],
            'initiate_cbz_payment_api',
        )
        self.assertEqual(
            process_step['transitions'][0]['condition_config']['value'],
            'ecocash',
        )
        self.assertEqual(
            cbz_step['config']['actions_to_run'][0]['action_type'],
            'initiate_cbz_ecocash_payment',
        )


class CBZEcoCashViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('cbz_integration.views._get_active_config')
    def test_public_config_view_exposes_mode_and_test_msisdns(self, mock_get_active_config):
        mock_get_active_config.return_value = CBZConfig(mode='Test', application_id='app-id')

        with self.settings(CBZ_TEST_ECOCASH_MSISDNS='263771234567,0773501244'):
            request = self.factory.get('/crm-api/payments/cbz/config/')
            response = cbz_public_config_view(request)

        payload = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['config']['mode'], 'Test')
        self.assertEqual(payload['config']['ecocash']['accepted_formats'], ['2637XXXXXXXX', '07XXXXXXXX'])
        self.assertEqual(payload['config']['ecocash']['test_msisdns'], ['263771234567', '0773501244'])

    @patch('cbz_integration.views._build_client')
    def test_ecocash_debit_view_marks_pending_transactions(self, mock_build_client):
        mock_client = MagicMock()
        mock_client.debit_ecocash.return_value = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': 'Pending',
                'ResultDescription': 'Awaiting customer confirmation',
                'MerchantReference': 'KS-PENDING-001',
            }
        }
        mock_build_client.return_value = mock_client

        request = self.factory.post(
            '/crm-api/payments/cbz/ecocash/debit/',
            data='{"msisdn": "263771234567", "amount": "10.50", "currency": "USD"}',
            content_type='application/json',
        )

        response = cbz_ecocash_debit_view(request)
        payload = json.loads(response.content.decode('utf-8'))
        txn = CBZTransaction.objects.get(merchant_reference=payload['merchant_reference'])

        self.assertEqual(response.status_code, 202)
        self.assertTrue(payload['success'])
        self.assertTrue(payload['pending'])
        self.assertEqual(txn.status, CBZTransaction.TransactionStatus.PENDING)

    @patch('cbz_integration.views._build_client')
    def test_ecocash_debit_creates_and_links_website_booking(self, mock_build_client):
        mock_client = MagicMock()
        mock_client.debit_ecocash.return_value = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': 'Pending',
                'ResultDescription': 'Awaiting customer confirmation',
                'MerchantReference': 'KS-PENDING-WEB-001',
            }
        }
        mock_build_client.return_value = mock_client

        request = self.factory.post(
            '/crm-api/payments/cbz/ecocash/debit/',
            data=json.dumps({
                'msisdn': '263771234567',
                'amount': '10.50',
                'currency': 'USD',
                'booking_details': {
                    'tour_name': 'Jetty Usage',
                    'selected_date': '2026-05-05',
                    'number_of_people': 2,
                },
            }),
            content_type='application/json',
        )

        response = cbz_ecocash_debit_view(request)
        payload = json.loads(response.content.decode('utf-8'))
        txn = CBZTransaction.objects.get(merchant_reference=payload['merchant_reference'])

        self.assertEqual(response.status_code, 202)
        self.assertTrue(payload['success'])
        self.assertIsNotNone(payload.get('booking_reference'))
        self.assertIsNotNone(txn.booking)
        self.assertEqual(txn.booking.tour_name, 'Jetty Usage')


class CBZCard3DSViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('cbz_integration.views._build_client')
    def test_card_debit_returns_3ds_challenge_payload(self, mock_build_client):
        mock_client = MagicMock()
        mock_client.debit_card.return_value = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': 'Pending',
                'ResultDescription': '3DS authentication required',
                'MerchantReference': 'IGNORED-IN-TEST',
                'ACSURL': 'https://acs.iveri.example/challenge',
                'PaReq': 'pareq-token',
                'MD': 'merchant-session',
            }
        }
        mock_build_client.return_value = mock_client

        request = self.factory.post(
            '/crm-api/payments/cbz/card/debit/',
            data=json.dumps({
                'pan': '5413330089020020',
                'expiry_date': '0228',
                'cvv': '123',
                'amount': '150.00',
                'currency': 'USD',
            }),
            content_type='application/json',
        )

        response = cbz_card_debit_view(request)
        payload = json.loads(response.content.decode('utf-8'))
        txn = CBZTransaction.objects.get(merchant_reference=payload['merchant_reference'])

        self.assertEqual(response.status_code, 202)
        self.assertTrue(payload['success'])
        self.assertTrue(payload['requires_3ds'])
        self.assertEqual(payload['challenge']['ACSURL'], 'https://acs.iveri.example/challenge')
        self.assertEqual(txn.status, CBZTransaction.TransactionStatus.PENDING)

    @patch('cbz_integration.views._build_client')
    def test_card_3ds_complete_marks_approved_transaction(self, mock_build_client):
        txn = CBZTransaction.objects.create(
            merchant_reference='KS-3DS-COMPLETE-001',
            payment_type=CBZTransaction.PaymentType.CARD,
            masked_pan='5413****0020',
            amount=Decimal('150.00'),
            currency='USD',
            command='Debit',
            status=CBZTransaction.TransactionStatus.PENDING,
        )

        mock_client = MagicMock()
        mock_client.query_transaction.return_value = {
            'Transaction': {
                'ResultCode': RESULT_CODE_SUCCESS,
                'Status': STATUS_APPROVED,
                'MerchantReference': txn.merchant_reference,
                'TransactionIndex': 'TXN-3DS-001',
                'AuthorisationCode': 'AUTH-3DS-001',
            }
        }
        mock_build_client.return_value = mock_client

        request = self.factory.post(
            '/crm-api/payments/cbz/card/3ds/complete/',
            data=json.dumps({'merchant_reference': txn.merchant_reference}),
            content_type='application/json',
        )

        response = cbz_card_3ds_complete_view(request)
        payload = json.loads(response.content.decode('utf-8'))
        txn.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(txn.status, CBZTransaction.TransactionStatus.APPROVED)
        self.assertEqual(txn.transaction_index, 'TXN-3DS-001')


class IVeriCertificateClientTests(TestCase):
    def setUp(self):
        self.config = IVeriCertificateConfig(
            soap_url='https://portal.host.iveri.com/soap/certificates',
            soap_namespace='http://schemas.iveri.example/certificates',
            soap_username='merchant-user',
            soap_password='merchant-pass',
            application_id='app-123',
            terminal_id='terminal-456',
            certificate_id='cert-789',
            mode='Test',
        )

    def test_generate_certificate_envelope_contains_operation_and_credentials(self):
        client = IVeriCertificateClient(self.config)
        envelope = client._build_envelope('GenerateCertificateID', {})
        xml = envelope.decode('utf-8')

        self.assertIn('GenerateCertificateID', xml)
        self.assertIn('merchant-user', xml)
        self.assertIn('app-123', xml)
        self.assertIn('terminal-456', xml)

    def test_generate_certificate_parses_certificate_id(self):
        client = IVeriCertificateClient(self.config)
        with patch.object(client, '_execute', return_value={'CertificateID': 'cert-new-001'}) as mock_execute:
            result = client.generate_certificate_id()

        self.assertEqual(result['certificate_id'], 'cert-new-001')
        mock_execute.assert_called_once()


class CBZCertificateLifecycleViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.config = CBZConfig.objects.create(
            name='Active Config',
            portal_url='https://portal.host.iveri.com',
            certificate_id='cert-old',
            application_id='app-active',
            mode='Test',
            is_active=True,
        )

    @patch('cbz_integration.views._build_certificate_client')
    def test_generate_view_updates_active_config_certificate_id(self, mock_build_client):
        mock_client = MagicMock()
        mock_client.generate_certificate_id.return_value = {
            'certificate_id': 'cert-new',
            'raw': {'CertificateID': 'cert-new'},
        }
        mock_build_client.return_value = mock_client

        request = self.factory.post(
            '/crm-api/payments/cbz/certificates/generate/',
            data='{}',
            content_type='application/json',
        )

        response = cbz_certificate_generate_view(request)
        self.config.refresh_from_db()
        payload = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['certificate_id'], 'cert-new')
        self.assertEqual(self.config.certificate_id, 'cert-new')

    @patch('cbz_integration.views._build_certificate_client')
    def test_renew_view_updates_active_config_certificate_id(self, mock_build_client):
        mock_client = MagicMock()
        mock_client.renew_certificate_id.return_value = {
            'certificate_id': 'cert-renewed',
            'previous_certificate_id': 'cert-old',
            'raw': {'CertificateID': 'cert-renewed'},
        }
        mock_build_client.return_value = mock_client

        request = self.factory.post(
            '/crm-api/payments/cbz/certificates/renew/',
            data='{}',
            content_type='application/json',
        )

        response = cbz_certificate_renew_view(request)
        self.config.refresh_from_db()
        payload = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['certificate_id'], 'cert-renewed')
        self.assertEqual(self.config.certificate_id, 'cert-renewed')


# ─── Phase 2+ Tests: IVERI_STATUS_MAP, idempotency, callback, factory ───


class IVeriStatusMapConstantsTest(TestCase):
    """Verify the authoritative IVERI_STATUS_MAP constants are correct."""

    def test_success_code(self):
        self.assertEqual(IVERI_STATUS_MAP["0"], "SUCCESS")

    def test_error_code_is_retriable(self):
        self.assertEqual(IVERI_STATUS_MAP["1"], "ERROR")
        self.assertIn("1", IVERI_RETRIABLE_CODES)
        self.assertNotIn("1", IVERI_TERMINAL_FAILURE_CODES)

    def test_declined_code(self):
        self.assertEqual(IVERI_STATUS_MAP["4"], "DECLINED")
        self.assertIn("4", IVERI_TERMINAL_FAILURE_CODES)
        self.assertNotIn("4", IVERI_RETRIABLE_CODES)

    def test_invalid_card_code(self):
        self.assertEqual(IVERI_STATUS_MAP["255"], "INVALID_CARD")
        self.assertIn("255", IVERI_TERMINAL_FAILURE_CODES)

    def test_unknown_code_fallback(self):
        self.assertIsNone(IVERI_STATUS_MAP.get("999"))


class IVeriClientGetResultEnhancedTest(TestCase):
    """get_result() must now return status_label and supplemental fields."""

    def _make_response(self, result_code, extra=None):
        txn = {
            "ResultCode": result_code,
            "ResultDescription": "Test",
            "Status": "Approved" if result_code == "0" else "Declined",
            "TransactionIndex": "TX-001",
            "AuthorisationCode": "AUTH-001",
            "MerchantReference": "KS-ABC",
            "Amount": "1000",
            "Currency": "USD",
            "RequestID": "REQ-001",
        }
        if extra:
            txn.update(extra)
        return {"Transaction": txn}

    def test_success_result_has_status_label(self):
        result = IVeriClient.get_result(self._make_response("0"))
        self.assertEqual(result["status_label"], "SUCCESS")
        self.assertFalse(result["is_retriable"])
        self.assertFalse(result["is_terminal_failure"])

    def test_error_code_is_retriable(self):
        result = IVeriClient.get_result(self._make_response("1"))
        self.assertEqual(result["status_label"], "ERROR")
        self.assertTrue(result["is_retriable"])

    def test_declined_code_is_terminal(self):
        result = IVeriClient.get_result(self._make_response("4"))
        self.assertEqual(result["status_label"], "DECLINED")
        self.assertTrue(result["is_terminal_failure"])
        self.assertFalse(result["is_retriable"])

    def test_invalid_card_code_is_terminal(self):
        result = IVeriClient.get_result(self._make_response("255"))
        self.assertEqual(result["status_label"], "INVALID_CARD")
        self.assertTrue(result["is_terminal_failure"])

    def test_bank_reference_extracted(self):
        result = IVeriClient.get_result(
            self._make_response("0", {"BankReference": "BANK-REF-999"})
        )
        self.assertEqual(result["bank_reference"], "BANK-REF-999")

    def test_consumer_order_id_extracted(self):
        result = IVeriClient.get_result(
            self._make_response("0", {"ConsumerOrderID": "CON-001"})
        )
        self.assertEqual(result["consumer_order_id"], "CON-001")

    def test_card_bin_extracted(self):
        result = IVeriClient.get_result(
            self._make_response("0", {"CardBin": "541333"})
        )
        self.assertEqual(result["card_bin"], "541333")


class CBZTransactionNewFieldsTest(TestCase):
    """CBZTransaction new model fields must be saveable and queryable."""

    def setUp(self):
        self.txn = CBZTransaction.objects.create(
            merchant_reference="KS-TEST-NEW-FIELDS",
            payment_type=CBZTransaction.PaymentType.CARD,
            amount=Decimal("100.00"),
            currency="USD",
            command="Debit",
            status=CBZTransaction.TransactionStatus.INITIATED,
        )

    def test_bank_reference_persists(self):
        self.txn.bank_reference = "BANK-123"
        self.txn.save(update_fields=["bank_reference"])
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.bank_reference, "BANK-123")

    def test_consumer_order_id_persists(self):
        self.txn.consumer_order_id = "CON-456"
        self.txn.save(update_fields=["consumer_order_id"])
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.consumer_order_id, "CON-456")

    def test_card_bin_persists(self):
        self.txn.card_bin = "541333"
        self.txn.save(update_fields=["card_bin"])
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.card_bin, "541333")

    def test_gateway_response_persists(self):
        payload = {"Transaction": {"ResultCode": "0"}}
        self.txn.gateway_response = payload
        self.txn.save(update_fields=["gateway_response"])
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.gateway_response["Transaction"]["ResultCode"], "0")

    def test_idempotency_key_unique(self):
        from django.db import IntegrityError
        self.txn.idempotency_key = "unique-key-abc"
        self.txn.save(update_fields=["idempotency_key"])

        with self.assertRaises(IntegrityError):
            CBZTransaction.objects.create(
                merchant_reference="KS-DUP-IDEM",
                payment_type=CBZTransaction.PaymentType.CARD,
                amount=Decimal("50.00"),
                currency="USD",
                command="Debit",
                status=CBZTransaction.TransactionStatus.INITIATED,
                idempotency_key="unique-key-abc",  # duplicate
            )


class CBZCallbackViewStatusMapTest(TestCase):
    """Callback view must handle all IVERI_STATUS_MAP codes correctly."""

    factory = RequestFactory()

    def setUp(self):
        self.txn = CBZTransaction.objects.create(
            merchant_reference="KS-CB-TEST",
            payment_type=CBZTransaction.PaymentType.ECOCASH,
            amount=Decimal("25.00"),
            currency="USD",
            command="Debit",
            status=CBZTransaction.TransactionStatus.PENDING,
        )

    def _post_callback(self, result_code, status_text=""):
        payload = {
            "Transaction": {
                "MerchantReference": "KS-CB-TEST",
                "ResultCode": result_code,
                "ResultDescription": f"Test code {result_code}",
                "Status": status_text,
            }
        }
        request = self.factory.post(
            "/crm-api/payments/cbz/callback/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        return cbz_callback_view(request)

    def test_success_code_0_approves_transaction(self):
        response = self._post_callback("0", STATUS_APPROVED)
        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, CBZTransaction.TransactionStatus.APPROVED)

    def test_error_code_1_leaves_transaction_pending(self):
        """Code "1" is a retriable timeout — must NOT set DECLINED."""
        response = self._post_callback("1", "Error")
        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, CBZTransaction.TransactionStatus.PENDING)

    def test_declined_code_4_sets_declined(self):
        response = self._post_callback("4", "Declined")
        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, CBZTransaction.TransactionStatus.DECLINED)

    def test_invalid_card_code_255_sets_declined(self):
        response = self._post_callback("255", "Invalid")
        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, CBZTransaction.TransactionStatus.DECLINED)

    def test_callback_stores_gateway_response(self):
        self._post_callback("0", STATUS_APPROVED)
        self.txn.refresh_from_db()
        self.assertIsNotNone(self.txn.gateway_response)

    def test_callback_idempotent_on_double_approval(self):
        """Calling the callback twice for the same approval must not raise or double-record."""
        self._post_callback("0", STATUS_APPROVED)
        self.txn.refresh_from_db()
        first_completed = self.txn.completed_at

        # second identical callback
        self._post_callback("0", STATUS_APPROVED)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.completed_at, first_completed)

    def test_callback_missing_merchant_reference_returns_400(self):
        payload = {"Transaction": {"ResultCode": "0"}}
        request = self.factory.post(
            "/crm-api/payments/cbz/callback/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = cbz_callback_view(request)
        self.assertEqual(response.status_code, 400)

    def test_callback_unknown_merchant_reference_returns_404(self):
        payload = {"Transaction": {"MerchantReference": "KS-DOESNOTEXIST", "ResultCode": "0"}}
        request = self.factory.post(
            "/crm-api/payments/cbz/callback/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = cbz_callback_view(request)
        self.assertEqual(response.status_code, 404)


class PaymentGatewayFactoryTest(TestCase):
    """PaymentGatewayFactory must register and resolve gateways correctly."""

    def test_get_iveri_gateway(self):
        gateway = PaymentGatewayFactory.get_gateway("IVERI")
        self.assertIsInstance(gateway, IVeriGateway)
        self.assertIsInstance(gateway, PaymentProcessor)

    def test_get_cbz_alias(self):
        gateway = PaymentGatewayFactory.get_gateway("CBZ")
        self.assertIsInstance(gateway, IVeriGateway)

    def test_get_cbz_card_alias(self):
        gateway = PaymentGatewayFactory.get_gateway("CBZ_CARD")
        self.assertIsInstance(gateway, IVeriGateway)

    def test_get_cbz_ecocash_alias(self):
        gateway = PaymentGatewayFactory.get_gateway("CBZ_ECOCASH")
        self.assertIsInstance(gateway, IVeriGateway)

    def test_unknown_gateway_raises_key_error(self):
        with self.assertRaises(KeyError):
            PaymentGatewayFactory.get_gateway("NONEXISTENT_GW")

    def test_case_insensitive_lookup(self):
        gateway = PaymentGatewayFactory.get_gateway("iveri")
        self.assertIsInstance(gateway, IVeriGateway)

    def test_register_custom_gateway(self):
        class DummyGateway(PaymentProcessor):
            def initiate_payment(self, **kwargs):
                return {}
            def verify_payment(self, **kwargs):
                return {}
            def handle_callback(self, **kwargs):
                return {}
            def refund(self, **kwargs):
                return {}

        PaymentGatewayFactory.register("DUMMY_GW", DummyGateway)
        gw = PaymentGatewayFactory.get_gateway("DUMMY_GW")
        self.assertIsInstance(gw, DummyGateway)

    def test_register_non_processor_raises_type_error(self):
        class NotAGateway:
            pass
        with self.assertRaises(TypeError):
            PaymentGatewayFactory.register("BAD_GW", NotAGateway)

    def test_available_gateways_lists_registered_keys(self):
        keys = PaymentGatewayFactory.available_gateways()
        self.assertIn("IVERI", keys)
        self.assertIn("CBZ", keys)

    def test_handle_callback_normalises_success(self):
        gateway = PaymentGatewayFactory.get_gateway("IVERI")
        result = gateway.handle_callback(payload={
            "Transaction": {
                "MerchantReference": "KS-NORM",
                "ResultCode": "0",
                "ResultDescription": "OK",
            }
        })
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["status_label"], "SUCCESS")

    def test_handle_callback_normalises_retriable_error(self):
        gateway = PaymentGatewayFactory.get_gateway("IVERI")
        result = gateway.handle_callback(payload={
            "Transaction": {
                "MerchantReference": "KS-ERR",
                "ResultCode": "1",
                "ResultDescription": "Timeout",
            }
        })
        self.assertEqual(result["status"], "retriable_error")

    def test_handle_callback_normalises_declined(self):
        gateway = PaymentGatewayFactory.get_gateway("IVERI")
        result = gateway.handle_callback(payload={
            "Transaction": {
                "MerchantReference": "KS-DEC",
                "ResultCode": "4",
                "ResultDescription": "Declined",
            }
        })
        self.assertEqual(result["status"], "declined")


class ScruPCIFieldsTest(TestCase):
    """_scrub_pci_fields must redact sensitive keys and preserve safe keys."""

    def test_redacts_pan(self):
        from cbz_integration.views import _scrub_pci_fields
        response = {"Transaction": {"PAN": "4111111111111111", "Amount": "100"}}
        scrubbed = _scrub_pci_fields(response)
        self.assertEqual(scrubbed["Transaction"]["PAN"], "[REDACTED]")
        self.assertEqual(scrubbed["Transaction"]["Amount"], "100")

    def test_redacts_nested_token(self):
        from cbz_integration.views import _scrub_pci_fields
        response = {"data": {"Token": "secret-tok", "MerchantRef": "KS-1"}}
        scrubbed = _scrub_pci_fields(response)
        self.assertEqual(scrubbed["data"]["Token"], "[REDACTED]")
        self.assertEqual(scrubbed["data"]["MerchantRef"], "KS-1")

    def test_handles_non_dict_gracefully(self):
        from cbz_integration.views import _scrub_pci_fields
        self.assertEqual(_scrub_pci_fields("plain-string"), "plain-string")


class ReconcilePaymentsCommandTest(TestCase):
    """Management command reconcile_payments must find and update pending transactions."""

    def setUp(self):
        from django.utils import timezone
        from datetime import timedelta
        CBZTransaction.objects.create(
            merchant_reference="KS-RECON-1",
            payment_type=CBZTransaction.PaymentType.ECOCASH,
            amount=Decimal("50.00"),
            currency="USD",
            command="Debit",
            status=CBZTransaction.TransactionStatus.PENDING,
        )
        # Make it look old enough for reconciliation
        CBZTransaction.objects.filter(merchant_reference="KS-RECON-1").update(
            created_at=timezone.now() - timedelta(minutes=10)
        )

    @patch("cbz_integration.management.commands.reconcile_payments.Command._get_client", create=True)
    @patch("cbz_integration.views._build_client")
    def test_dry_run_does_not_change_status(self, mock_build_client, *args):
        from django.core.management import call_command
        from io import StringIO
        mock_client = MagicMock()
        mock_client.query_transaction.return_value = {
            "Transaction": {
                "ResultCode": "0",
                "Status": "Approved",
                "TransactionIndex": "TX-001",
                "AuthorisationCode": "AUTH-001",
            }
        }
        mock_build_client.return_value = mock_client

        out = StringIO()
        call_command(
            "reconcile_payments",
            "--min-age-minutes=5",
            "--dry-run",
            stdout=out,
        )

        txn = CBZTransaction.objects.get(merchant_reference="KS-RECON-1")
        self.assertEqual(txn.status, CBZTransaction.TransactionStatus.PENDING)
        self.assertIn("DRY RUN", out.getvalue())
