"""
Tests for CBZ/iVeri payment integration.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory

from .models import CBZConfig, CBZTransaction
from .services import IVeriClient, IVeriConfig
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
