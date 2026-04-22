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
    cbz_ecocash_debit_view,
    cbz_card_debit_view,
    cbz_card_3ds_complete_view,
    cbz_certificate_generate_view,
    cbz_certificate_renew_view,
)
from .constants import (
    ECOCASH_PAN_PREFIX, ECOCASH_DEFAULT_EXPIRY,
    RESULT_CODE_SUCCESS, STATUS_APPROVED,
    COMMAND_DEBIT, IVERI_API_VERSION,
)


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
