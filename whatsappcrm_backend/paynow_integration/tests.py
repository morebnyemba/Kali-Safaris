from django.test import TestCase, override_settings
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import date

from customer_data.models import Booking, Payment, CustomerProfile, TourInquiry
from conversations.models import Contact
from products_and_services.models import Tour
from .services import PaynowService
from .models import PaynowConfig


class PaynowServiceTestCase(TestCase):
    """Test cases for PaynowService"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test contact and customer profile
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer_profile = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@example.com'
        )
        
        # Create a test tour
        self.tour = Tour.objects.create(
            name='Test Safari Tour',
            duration_days=3,
            base_price=Decimal('500.00')
        )
        
        # Create a test booking
        self.booking = Booking.objects.create(
            customer=self.customer_profile,
            tour=self.tour,
            tour_name='Test Safari Tour',
            start_date=date.today(),
            end_date=date.today(),
            number_of_adults=2,
            number_of_children=0,
            total_amount=Decimal('1000.00'),
            payment_status=Booking.PaymentStatus.PENDING,
            source=Booking.BookingSource.WHATSAPP
        )
        
        # Create PaynowConfig
        self.paynow_config = PaynowConfig.objects.create(
            integration_id='test_integration_id',
            integration_key='test_integration_key'
        )
    
    @patch('paynow_integration.services.PaynowSDK')
    def test_initiate_payment_success(self, mock_sdk):
        """Test successful payment initiation"""
        # Mock the SDK response
        mock_instance = MagicMock()
        mock_instance.initiate_express_checkout.return_value = {
            'success': True,
            'paynow_reference': 'PAY-12345',
            'poll_url': 'https://paynow.co.zw/poll/12345',
            'instructions': 'Check your phone for payment prompt'
        }
        mock_sdk.return_value = mock_instance
        
        # Initialize service and initiate payment
        service = PaynowService(ipn_callback_url='/crm-api/paynow/ipn/')
        result = service.initiate_payment(
            booking=self.booking,
            amount=Decimal('500.00'),
            phone_number='263771234567',
            email='test@example.com',
            payment_method='ecocash',
            description='Test payment'
        )
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['paynow_reference'], 'PAY-12345')
        
        # Verify payment record was created
        payment = Payment.objects.filter(booking=self.booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, Payment.PaymentMethod.PAYNOW_ECOCASH)
        self.assertEqual(payment.amount, Decimal('500.00'))
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)
    
    @patch('paynow_integration.services.PaynowSDK')
    def test_initiate_payment_failure(self, mock_sdk):
        """Test payment initiation failure"""
        # Mock the SDK response
        mock_instance = MagicMock()
        mock_instance.initiate_express_checkout.return_value = {
            'success': False,
            'message': 'Invalid phone number'
        }
        mock_sdk.return_value = mock_instance
        
        # Initialize service and initiate payment
        service = PaynowService(ipn_callback_url='/crm-api/paynow/ipn/')
        result = service.initiate_payment(
            booking=self.booking,
            amount=Decimal('500.00'),
            phone_number='invalid',
            email='test@example.com',
            payment_method='ecocash',
            description='Test payment'
        )
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('Invalid phone number', result['message'])
        
        # Verify payment record was created and marked as failed
        payment = Payment.objects.filter(booking=self.booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, Payment.PaymentStatus.FAILED)
    
    def test_payment_method_mapping(self):
        """Test that payment methods are correctly mapped"""
        service = PaynowService(ipn_callback_url='/crm-api/paynow/ipn/')
        
        # Test with mock to avoid actual API calls
        with patch('paynow_integration.services.PaynowSDK') as mock_sdk:
            mock_instance = MagicMock()
            mock_instance.initiate_express_checkout.return_value = {
                'success': True,
                'paynow_reference': 'PAY-12345',
                'poll_url': 'https://paynow.co.zw/poll/12345',
                'instructions': 'Check your phone'
            }
            mock_sdk.return_value = mock_instance
            
            # Test ecocash
            service.initiate_payment(
                booking=self.booking,
                amount=Decimal('100.00'),
                phone_number='263771234567',
                email='test@example.com',
                payment_method='ecocash'
            )
            payment = Payment.objects.filter(
                booking=self.booking,
                payment_method=Payment.PaymentMethod.PAYNOW_ECOCASH
            ).first()
            self.assertIsNotNone(payment)
            
            # Test innbucks
            service.initiate_payment(
                booking=self.booking,
                amount=Decimal('100.00'),
                phone_number='263771234567',
                email='test@example.com',
                payment_method='innbucks'
            )
            payment = Payment.objects.filter(
                booking=self.booking,
                payment_method=Payment.PaymentMethod.PAYNOW_INNBUCKS
            ).first()
            self.assertIsNotNone(payment)
            
            # Test onemoney
            service.initiate_payment(
                booking=self.booking,
                amount=Decimal('100.00'),
                phone_number='263771234567',
                email='test@example.com',
                payment_method='onemoney'
            )
            payment = Payment.objects.filter(
                booking=self.booking,
                payment_method=Payment.PaymentMethod.PAYNOW_ONEMONEY
            ).first()
            self.assertIsNotNone(payment)


class PaymentModelTestCase(TestCase):
    """Test cases for Payment model with Paynow methods"""
    
    def test_paynow_payment_methods_exist(self):
        """Test that Paynow payment method choices exist"""
        choices = dict(Payment.PaymentMethod.choices)
        
        self.assertIn('paynow_ecocash', choices)
        self.assertIn('paynow_innbucks', choices)
        self.assertIn('paynow_onemoney', choices)
        
        self.assertEqual(choices['paynow_ecocash'], 'Paynow - Ecocash')
        self.assertEqual(choices['paynow_innbucks'], 'Paynow - Innbucks')
        self.assertEqual(choices['paynow_onemoney'], 'Paynow - OneMoney')
