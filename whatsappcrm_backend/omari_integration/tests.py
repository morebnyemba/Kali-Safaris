"""
Basic smoke tests for Omari integration.
Run with: python manage.py test omari_integration.tests
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from .models import OmariTransaction
from .services import OmariClient, OmariConfig


class OmariClientTests(TestCase):
    """Test OmariClient methods."""

    def setUp(self):
        self.config = OmariConfig(
            base_url='https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment',
            merchant_key='test-key-123'
        )
        self.client = OmariClient(self.config)

    @patch('requests.Session.post')
    def test_auth_request_format(self, mock_post):
        """Test auth() sends correct payload and headers."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': False,
            'message': 'Auth Success',
            'responseCode': '000',
            'otpReference': 'ETDC'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.auth(
            msisdn='263774975187',
            reference='test-uuid-123',
            amount=3.50,
            currency='USD',
            channel='WEB'
        )

        # Verify request was made with correct URL and headers
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/auth', args[0])
        self.assertEqual(kwargs['json']['msisdn'], '263774975187')
        self.assertEqual(kwargs['json']['amount'], 3.50)
        self.assertEqual(kwargs['json']['currency'], 'USD')
        
        # Verify response
        self.assertFalse(result['error'])
        self.assertEqual(result['responseCode'], '000')

    @patch('requests.Session.post')
    def test_request_otp_validation(self, mock_post):
        """Test request() sends OTP correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': False,
            'message': 'Payment Success',
            'responseCode': '000',
            'paymentReference': 'H5PSKURANNR1LKS7AJ0KV50KZG',
            'debitReference': 'bc54b38257cf'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.request(
            msisdn='263774975187',
            reference='test-uuid-123',
            otp='123456'
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/request', args[0])
        self.assertEqual(kwargs['json']['otp'], '123456')
        self.assertEqual(result['paymentReference'], 'H5PSKURANNR1LKS7AJ0KV50KZG')

    @patch('requests.Session.get')
    def test_query_transaction(self, mock_get):
        """Test query() fetches transaction status."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': False,
            'status': 'Success',
            'responseCode': '000',
            'reference': 'test-uuid-123',
            'amount': 3.50
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.client.query('test-uuid-123')

        mock_get.assert_called_once()
        args, _ = mock_get.call_args
        self.assertIn('/query/test-uuid-123', args[0])
        self.assertEqual(result['status'], 'Success')

    @patch('requests.Session.post')
    def test_void_transaction(self, mock_post):
        """Test void() cancels a pending transaction."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': False,
            'message': 'Transaction voided successfully',
            'responseCode': '000'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.void('test-uuid-123')

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/void', args[0])
        self.assertEqual(kwargs['json']['reference'], 'test-uuid-123')
        self.assertFalse(result['error'])
        self.assertEqual(result['responseCode'], '000')


class OmariViewTests(TestCase):
    """Test Omari Django views."""

    def setUp(self):
        self.http_client = Client()

    @patch('omari_integration.views.OmariClient.auth')
    def test_auth_view_creates_transaction(self, mock_auth):
        """Test auth view creates database record."""
        mock_auth.return_value = {
            'error': False,
            'message': 'Auth Success',
            'responseCode': '000',
            'otpReference': 'ETDC'
        }

        response = self.http_client.post(
            reverse('omari_integration:auth'),
            data=json.dumps({
                'msisdn': '263774975187',
                'amount': 3.50,
                'currency': 'USD'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['error'])
        self.assertIn('reference', data)
        
        # Verify transaction was created
        txn = OmariTransaction.objects.filter(reference=data['reference']).first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.status, 'OTP_SENT')
        self.assertEqual(txn.otp_reference, 'ETDC')

    @patch('omari_integration.views.OmariClient.request')
    def test_request_view_updates_transaction(self, mock_request):
        """Test request view updates transaction on payment completion."""
        # Create initial transaction
        txn = OmariTransaction.objects.create(
            reference='test-uuid-456',
            msisdn='263774975187',
            amount=3.50,
            currency='USD',
            status='OTP_SENT',
            otp_reference='ETDC'
        )

        mock_request.return_value = {
            'error': False,
            'message': 'Payment Success',
            'responseCode': '000',
            'paymentReference': 'H5PSKURANNR1LKS7AJ0KV50KZG',
            'debitReference': 'bc54b38257cf'
        }

        response = self.http_client.post(
            reverse('omari_integration:request'),
            data=json.dumps({
                'msisdn': '263774975187',
                'reference': 'test-uuid-456',
                'otp': '123456'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        
        # Verify transaction was updated
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'SUCCESS')
        self.assertEqual(txn.payment_reference, 'H5PSKURANNR1LKS7AJ0KV50KZG')
        self.assertIsNotNone(txn.completed_at)

    @patch('omari_integration.views.OmariClient.request')
    def test_request_view_creates_payment_record(self, mock_request):
        """Test request view creates Payment record and updates booking when payment succeeds."""
        from customer_data.models import Booking, CustomerProfile, Payment
        from django.utils import timezone
        from datetime import timedelta
        
        # Create test customer and booking
        customer = CustomerProfile.objects.create(
            email='test@example.com',
            first_name='Test',
            last_name='Customer'
        )
        
        today = timezone.now().date()
        booking = Booking.objects.create(
            customer=customer,
            booking_reference='TEST-BOOKING-456',
            tour_name='Test Safari',
            start_date=today + timedelta(days=7),
            end_date=today + timedelta(days=10),
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('0.00'),
            payment_status=Booking.PaymentStatus.PENDING
        )
        
        # Create initial transaction linked to booking
        txn = OmariTransaction.objects.create(
            reference='test-uuid-789',
            msisdn='263774975187',
            amount=Decimal('50.00'),
            currency='USD',
            status='OTP_SENT',
            otp_reference='ETDC',
            booking=booking
        )

        mock_request.return_value = {
            'error': False,
            'message': 'Payment Success',
            'responseCode': '000',
            'paymentReference': 'OMARI-PAY-REF-123',
            'debitReference': 'DEBIT-REF-456'
        }

        response = self.http_client.post(
            reverse('omari_integration:request'),
            data=json.dumps({
                'msisdn': '263774975187',
                'reference': 'test-uuid-789',
                'otp': '123456'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        
        # Verify transaction was updated
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'SUCCESS')
        
        # Verify Payment record was created
        payment = Payment.objects.filter(booking=booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal('50.00'))
        self.assertEqual(payment.currency, 'USD')
        self.assertEqual(payment.status, Payment.PaymentStatus.SUCCESSFUL)
        self.assertEqual(payment.payment_method, Payment.PaymentMethod.OMARI)
        self.assertEqual(payment.transaction_reference, 'OMARI-PAY-REF-123')
        self.assertIn('DEBIT-REF-456', payment.notes)
        
        # Verify booking was updated
        booking.refresh_from_db()
        self.assertEqual(booking.amount_paid, Decimal('50.00'))
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.DEPOSIT_PAID)

    def test_query_view_returns_status(self):
        """Test query view endpoint."""
        # Create transaction
        txn = OmariTransaction.objects.create(
            reference='test-uuid-789',
            msisdn='263774975187',
            amount=3.50,
            currency='USD',
            status='SUCCESS',
            payment_reference='H5PSKURANNR1LKS7AJ0KV50KZG'
        )

        with patch('omari_integration.views.OmariClient.query') as mock_query:
            mock_query.return_value = {
                'error': False,
                'status': 'Success',
                'responseCode': '000',
                'reference': 'test-uuid-789',
                'amount': 3.50,
                'paymentReference': 'H5PSKURANNR1LKS7AJ0KV50KZG'
            }

            response = self.http_client.get(
                reverse('omari_integration:query', args=['test-uuid-789'])
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'Success')
            self.assertEqual(data['reference'], 'test-uuid-789')

    @patch('omari_integration.views.OmariClient.void')
    def test_void_view_cancels_transaction(self, mock_void):
        """Test void view cancels a pending transaction."""
        # Create initial transaction
        txn = OmariTransaction.objects.create(
            reference='test-uuid-999',
            msisdn='263774975187',
            amount=3.50,
            currency='USD',
            status='OTP_SENT',
            otp_reference='ETDC'
        )

        mock_void.return_value = {
            'error': False,
            'message': 'Transaction voided successfully',
            'responseCode': '000'
        }

        response = self.http_client.post(
            reverse('omari_integration:void'),
            data=json.dumps({
                'reference': 'test-uuid-999'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['error'])
        
        # Verify transaction was updated to VOIDED
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'VOIDED')


class OmariFlowActionsTests(TestCase):
    """Test Omari flow actions with proper exception handling."""

    def setUp(self):
        """Set up test contact and booking."""
        from conversations.models import Contact
        from customer_data.models import Booking, CustomerProfile
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test customer profile
        self.customer = CustomerProfile.objects.create(
            email='customer@test.com',
            first_name='Test',
            last_name='Customer'
        )
        
        # Create test contact
        self.contact = Contact.objects.create(
            whatsapp_id='263774975187',
            name='Test Contact',
            profile_name='Test',
        )
        
        # Use dynamic dates for booking
        today = timezone.now().date()
        start_date = today + timedelta(days=7)
        end_date = start_date + timedelta(days=4)
        
        # Create test booking
        self.booking = Booking.objects.create(
            customer=self.customer,
            booking_reference='TEST-BOOKING-123',
            total_amount=Decimal('50.00'),
            amount_paid=Decimal('0.00'),
            payment_status='pending',
            start_date=start_date,
            end_date=end_date,
        )

    @patch('omari_integration.flow_actions.get_payment_handler')
    def test_initiate_payment_handles_exception(self, mock_get_handler):
        """Test that initiate_omari_payment_action handles exceptions gracefully."""
        from omari_integration.flow_actions import initiate_omari_payment_action
        
        # Mock handler to raise an exception
        mock_handler = MagicMock()
        mock_handler.initiate_payment.side_effect = Exception('Network error')
        mock_get_handler.return_value = mock_handler
        
        # Call action
        flow_context = {
            'payment_phone': '263774975187',
            'amount_to_pay': 50.0
        }
        params = {
            'booking_reference': 'TEST-BOOKING-123',
            'amount': '50.00',
            'currency': 'USD',
            'channel': 'WEB',
            'msisdn': '263774975187'
        }
        
        result = initiate_omari_payment_action(self.contact, flow_context, params)
        
        # Verify error message is returned
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'send_text')
        self.assertIn('Payment service error', result[0]['text'])
        self.assertIn('Network error', result[0]['text'])

    @patch('omari_integration.flow_actions.get_payment_handler')
    def test_initiate_payment_success(self, mock_get_handler):
        """Test successful payment initiation."""
        from omari_integration.flow_actions import initiate_omari_payment_action
        
        # Mock successful handler response
        mock_handler = MagicMock()
        mock_handler.initiate_payment.return_value = {
            'success': True,
            'otp_reference': 'TEST-OTP-REF',
            'reference': 'test-uuid-123',
            'message': 'OTP sent successfully'
        }
        mock_get_handler.return_value = mock_handler
        
        # Call action
        flow_context = {
            'payment_phone': '263774975187',
            'amount_to_pay': 50.0
        }
        params = {
            'booking_reference': 'TEST-BOOKING-123',
            'amount': '50.00',
            'currency': 'USD',
            'channel': 'WEB',
            'msisdn': '263774975187'
        }
        
        result = initiate_omari_payment_action(self.contact, flow_context, params)
        
        # Verify success message is returned
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'send_text')
        self.assertIn('Payment Initiated', result[0]['text'])
        self.assertIn('TEST-OTP-REF', result[0]['text'])
        
        # Verify context was updated
        self.assertEqual(flow_context['omari_otp_reference'], 'TEST-OTP-REF')
        self.assertEqual(flow_context['_payment_reference'], 'test-uuid-123')

    @patch('omari_integration.flow_actions.get_payment_handler')
    def test_process_otp_success_sets_context_variable(self, mock_get_handler):
        """Test that process_otp_action sets omari_payment_success in context on success."""
        from omari_integration.flow_actions import process_otp_action
        
        # Mock successful OTP processing
        mock_handler = MagicMock()
        mock_handler.process_otp_input.return_value = {
            'success': True,
            'payment_reference': 'PAY-REF-123',
            'booking': self.booking,
            'message': 'Payment successful'
        }
        mock_get_handler.return_value = mock_handler
        
        # Call action
        flow_context = {}
        params = {'otp': '123456'}
        
        result = process_otp_action(self.contact, flow_context, params)
        
        # Verify success message is returned
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'send_text')
        self.assertIn('Payment Successful', result[0]['text'])
        self.assertIn('PAY-REF-123', result[0]['text'])
        
        # Verify context was updated with success flag
        self.assertEqual(flow_context['omari_payment_success'], True)

    @patch('omari_integration.flow_actions.get_payment_handler')
    def test_process_otp_failure_does_not_set_context_variable(self, mock_get_handler):
        """Test that process_otp_action does not set omari_payment_success on failure."""
        from omari_integration.flow_actions import process_otp_action
        
        # Mock failed OTP processing
        mock_handler = MagicMock()
        mock_handler.process_otp_input.return_value = {
            'success': False,
            'message': 'Invalid OTP',
            'response_code': '001'
        }
        mock_get_handler.return_value = mock_handler
        
        # Call action
        flow_context = {}
        params = {'otp': '999999'}
        
        result = process_otp_action(self.contact, flow_context, params)
        
        # Verify error message is returned
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'send_text')
        self.assertIn('Payment Failed', result[0]['text'])
        self.assertIn('Invalid OTP', result[0]['text'])
        
        # Verify context was NOT updated with success flag
        self.assertNotIn('omari_payment_success', flow_context)


class WhatsAppPaymentHandlerTests(TestCase):
    """Test WhatsAppPaymentHandler payment processing with booking updates."""

    def setUp(self):
        """Set up test data."""
        from conversations.models import Contact
        from customer_data.models import Booking, CustomerProfile
        from django.utils import timezone
        from datetime import timedelta
        
        # Create test customer
        self.customer = CustomerProfile.objects.create(
            email='test@example.com',
            first_name='Test',
            last_name='Customer'
        )
        
        # Create test contact
        self.contact = Contact.objects.create(
            whatsapp_id='263774975187',
            name='Test Contact',
            profile_name='Test',
        )
        
        # Create test booking
        today = timezone.now().date()
        self.booking = Booking.objects.create(
            customer=self.customer,
            booking_reference='TEST-BOOKING-WA-001',
            tour_name='Test Safari',
            start_date=today + timedelta(days=7),
            end_date=today + timedelta(days=10),
            total_amount=Decimal('200.00'),
            amount_paid=Decimal('0.00'),
            payment_status=Booking.PaymentStatus.PENDING
        )

    @patch('omari_integration.whatsapp_handler.OmariClient')
    def test_process_otp_creates_payment_record(self, mock_client_class):
        """Test that process_otp_input creates Payment record and updates booking."""
        from omari_integration.whatsapp_handler import WhatsAppPaymentHandler
        from customer_data.models import Payment
        import uuid
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.request.return_value = {
            'error': False,
            'message': 'Payment Success',
            'responseCode': '000',
            'paymentReference': 'WA-PAY-REF-999',
            'debitReference': 'WA-DEBIT-999'
        }
        mock_client_class.return_value = mock_client
        
        # Create handler and initiate payment state
        handler = WhatsAppPaymentHandler()
        reference = str(uuid.uuid4())
        
        # Create transaction
        txn = OmariTransaction.objects.create(
            reference=reference,
            msisdn='263774975187',
            amount=Decimal('100.00'),
            currency='USD',
            status='OTP_SENT',
            otp_reference='WA-OTP-REF',
            booking=self.booking
        )
        
        # Set payment state on contact
        handler._set_payment_state(self.contact, {
            'reference': reference,
            'otp_reference': 'WA-OTP-REF',
            'booking_id': self.booking.id,
            'amount': '100.00',
            'currency': 'USD',
            'awaiting_otp': True,
        })
        
        # Process OTP
        result = handler.process_otp_input(self.contact, '123456')
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_reference'], 'WA-PAY-REF-999')
        
        # Verify Payment record was created
        payment = Payment.objects.filter(booking=self.booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal('100.00'))
        self.assertEqual(payment.currency, 'USD')
        self.assertEqual(payment.status, Payment.PaymentStatus.SUCCESSFUL)
        self.assertEqual(payment.payment_method, Payment.PaymentMethod.OMARI)
        self.assertEqual(payment.transaction_reference, 'WA-PAY-REF-999')
        self.assertIn('WA-DEBIT-999', payment.notes)
        
        # Verify booking was updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.amount_paid, Decimal('100.00'))
        self.assertEqual(self.booking.payment_status, Booking.PaymentStatus.DEPOSIT_PAID)
        
        # Verify transaction was updated
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'SUCCESS')
        self.assertIsNotNone(txn.completed_at)

    @patch('omari_integration.whatsapp_handler.OmariClient')
    def test_process_otp_marks_booking_paid_when_full_amount(self, mock_client_class):
        """Test that booking is marked as PAID when full amount is paid."""
        from omari_integration.whatsapp_handler import WhatsAppPaymentHandler
        import uuid
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.request.return_value = {
            'error': False,
            'message': 'Payment Success',
            'responseCode': '000',
            'paymentReference': 'FULL-PAY-REF',
            'debitReference': 'FULL-DEBIT'
        }
        mock_client_class.return_value = mock_client
        
        # Create handler
        handler = WhatsAppPaymentHandler()
        reference = str(uuid.uuid4())
        
        # Create transaction for full amount
        txn = OmariTransaction.objects.create(
            reference=reference,
            msisdn='263774975187',
            amount=Decimal('200.00'),  # Full amount
            currency='USD',
            status='OTP_SENT',
            otp_reference='FULL-OTP',
            booking=self.booking
        )
        
        # Set payment state
        handler._set_payment_state(self.contact, {
            'reference': reference,
            'otp_reference': 'FULL-OTP',
            'booking_id': self.booking.id,
            'amount': '200.00',
            'currency': 'USD',
            'awaiting_otp': True,
        })
        
        # Process OTP
        result = handler.process_otp_input(self.contact, '123456')
        
        # Verify success
        self.assertTrue(result['success'])
        
        # Verify booking was marked as PAID
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.amount_paid, Decimal('200.00'))
        self.assertEqual(self.booking.payment_status, Booking.PaymentStatus.PAID)


