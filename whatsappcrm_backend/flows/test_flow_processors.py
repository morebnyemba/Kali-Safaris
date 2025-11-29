"""
Tests for WhatsApp Flow Response Processors.
Validates that backend handlers correctly process flow submissions.
"""

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from flows.models import WhatsAppFlow, WhatsAppFlowResponse
from flows.whatsapp_flow_response_processor import WhatsAppFlowResponseProcessor
from conversations.models import Contact
from customer_data.models import (
    CustomerProfile, InstallationRequest, SolarCleaningRequest,
    SiteAssessmentRequest, LoanApplication, Order
)
from meta_integration.models import MetaAppConfig


class SiteInspectionProcessorTest(TestCase):
    """Test site inspection flow processor"""
    
    def setUp(self):
        # Create test meta config
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
        
        # Create test contact
        self.contact = Contact.objects.create(
            whatsapp_id="+263771234567",
            name="Test User"
        )
        
        # Create test flow
        self.flow = WhatsAppFlow.objects.create(
            name="site_inspection_whatsapp",
            friendly_name="Site Inspection",
            flow_json={"version": "7.3"},
            meta_app_config=self.meta_config,
            sync_status='published'
        )
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_site_inspection_success(self, mock_send_message):
        """Test successful site inspection processing"""
        response_data = {
            'data': {
                'assessment_full_name': 'John Doe',
                'assessment_preferred_day': 'Monday, December 25th',
                'assessment_company_name': 'Test Company',
                'assessment_address': '123 Main Street, Harare',
                'assessment_contact_info': '+263771234567'
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check flow response was created
        self.assertIsNotNone(flow_response)
        self.assertTrue(flow_response.is_processed)
        
        # Check site assessment was created
        assessment = SiteAssessmentRequest.objects.filter(
            customer__contact=self.contact
        ).first()
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.full_name, 'John Doe')
        self.assertEqual(assessment.address, '123 Main Street, Harare')
        self.assertTrue(assessment.assessment_id.startswith('SA-'))
        
        # Check confirmation message was sent
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args
        self.assertEqual(call_args[1]['to_phone_number'], '+263771234567')
        self.assertIn('John Doe', call_args[1]['data']['body'])
        self.assertIn('SA-', call_args[1]['data']['body'])
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_site_inspection_missing_fields(self, mock_send_message):
        """Test site inspection processing with missing required fields"""
        response_data = {
            'data': {
                'assessment_full_name': 'John Doe',
                # Missing address and contact_info
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check processing failed
        self.assertIsNotNone(flow_response)
        self.assertFalse(flow_response.is_processed)
        self.assertIn('Missing required fields', flow_response.processing_notes)


class LoanApplicationProcessorTest(TestCase):
    """Test loan application flow processor"""
    
    def setUp(self):
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
        
        self.contact = Contact.objects.create(
            whatsapp_id="+263771234567",
            name="Test User"
        )
        
        self.flow = WhatsAppFlow.objects.create(
            name="loan_application_whatsapp",
            friendly_name="Loan Application",
            flow_json={"version": "7.3"},
            meta_app_config=self.meta_config,
            sync_status='published'
        )
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_cash_loan_success(self, mock_send_message):
        """Test successful cash loan application processing"""
        response_data = {
            'data': {
                'loan_type': 'cash_loan',
                'loan_applicant_name': 'Jane Smith',
                'loan_national_id': '12-345678-A-12',
                'loan_employment_status': 'employed',
                'loan_monthly_income': 1500,
                'loan_request_amount': 500,
                'loan_product_interest': ''
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check flow response was created
        self.assertIsNotNone(flow_response)
        self.assertTrue(flow_response.is_processed)
        
        # Check loan application was created
        loan_app = LoanApplication.objects.filter(
            customer__contact=self.contact
        ).first()
        self.assertIsNotNone(loan_app)
        self.assertEqual(loan_app.full_name, 'Jane Smith')
        self.assertEqual(loan_app.loan_type, 'cash_loan')
        self.assertEqual(loan_app.requested_amount, Decimal('500'))
        self.assertEqual(loan_app.status, 'pending_review')
        
        # Check confirmation message was sent
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args
        self.assertIn('Jane Smith', call_args[1]['data']['body'])
        self.assertIn('Cash Loan', call_args[1]['data']['body'])
        self.assertIn('$500.00', call_args[1]['data']['body'])
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_product_loan_success(self, mock_send_message):
        """Test successful product loan application processing"""
        response_data = {
            'data': {
                'loan_type': 'product_loan',
                'loan_applicant_name': 'John Doe',
                'loan_national_id': '12-345678-A-12',
                'loan_employment_status': 'self_employed',
                'loan_monthly_income': 2000,
                'loan_request_amount': 0,
                'loan_product_interest': '5kVA Solar Kit'
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check loan application was created
        loan_app = LoanApplication.objects.filter(
            customer__contact=self.contact
        ).first()
        self.assertIsNotNone(loan_app)
        self.assertEqual(loan_app.loan_type, 'product_loan')
        self.assertEqual(loan_app.product_of_interest, '5kVA Solar Kit')
        
        # Check confirmation message includes product
        call_args = mock_send_message.call_args
        self.assertIn('Product Loan', call_args[1]['data']['body'])
        self.assertIn('5kVA Solar Kit', call_args[1]['data']['body'])


class SolarInstallationProcessorTest(TestCase):
    """Test solar installation flow processor with order verification"""
    
    def setUp(self):
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
        
        self.contact = Contact.objects.create(
            whatsapp_id="+263771234567",
            name="Test User"
        )
        
        self.customer_profile = CustomerProfile.objects.create(
            contact=self.contact,
            first_name="Test",
            last_name="Customer"
        )
        
        # Create a test order
        self.order = Order.objects.create(
            order_number="HAN-12345",
            customer=self.customer_profile,
            stage='closed_won'
        )
        
        self.flow = WhatsAppFlow.objects.create(
            name="solar_installation_whatsapp",
            friendly_name="Solar Installation",
            flow_json={"version": "7.3"},
            meta_app_config=self.meta_config,
            sync_status='published'
        )
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_with_valid_order(self, mock_send_message):
        """Test solar installation with valid order number"""
        response_data = {
            'data': {
                'installation_type': 'residential',
                'order_number': 'HAN-12345',
                'branch': 'Harare',
                'sales_person': 'John Sales',
                'full_name': 'Test Customer',
                'contact_phone': '+263771234567',
                'alt_contact_name': 'N/A',
                'alt_contact_phone': 'N/A',
                'preferred_date': '2025-12-25',
                'availability': 'morning',
                'address': '123 Main Street'
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check processing succeeded
        self.assertTrue(flow_response.is_processed)
        self.assertIn('Order HAN-12345 verified', flow_response.processing_notes)
        
        # Check installation request was created and linked to order
        install_req = InstallationRequest.objects.filter(
            customer__contact=self.contact
        ).first()
        self.assertIsNotNone(install_req)
        self.assertEqual(install_req.associated_order, self.order)
        self.assertEqual(install_req.order_number, 'HAN-12345')
        
        # Check confirmation message includes order verification
        call_args = mock_send_message.call_args
        self.assertIn('HAN-12345', call_args[1]['data']['body'])
        self.assertIn('✅', call_args[1]['data']['body'])
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_with_invalid_order(self, mock_send_message):
        """Test solar installation with invalid order number"""
        response_data = {
            'data': {
                'installation_type': 'residential',
                'order_number': 'INVALID-999',
                'branch': 'Harare',
                'sales_person': 'John Sales',
                'full_name': 'Test Customer',
                'contact_phone': '+263771234567',
                'alt_contact_name': 'N/A',
                'alt_contact_phone': 'N/A',
                'preferred_date': '2025-12-25',
                'availability': 'morning',
                'address': '123 Main Street'
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check processing failed due to invalid order
        self.assertFalse(flow_response.is_processed)
        self.assertIn('Order verification failed', flow_response.processing_notes)
        
        # Check error message was sent to user
        call_args = mock_send_message.call_args
        self.assertIn('❌', call_args[1]['data']['body'])
        self.assertIn('INVALID-999', call_args[1]['data']['body'])
        self.assertIn('not be found', call_args[1]['data']['body'])


class SolarCleaningProcessorTest(TestCase):
    """Test solar cleaning flow processor with enhanced confirmations"""
    
    def setUp(self):
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
        
        self.contact = Contact.objects.create(
            whatsapp_id="+263771234567",
            name="Test User"
        )
        
        self.flow = WhatsAppFlow.objects.create(
            name="solar_cleaning_whatsapp",
            friendly_name="Solar Cleaning",
            flow_json={"version": "7.3"},
            meta_app_config=self.meta_config,
            sync_status='published'
        )
    
    @patch('flows.whatsapp_flow_response_processor.send_whatsapp_message')
    def test_process_solar_cleaning_with_confirmation(self, mock_send_message):
        """Test solar cleaning with personalized confirmation"""
        response_data = {
            'data': {
                'full_name': 'Alice Johnson',
                'contact_phone': '+263771234567',
                'roof_type': 'tile',
                'panel_type': 'monocrystalline',
                'panel_count': 15,
                'preferred_date': '2025-12-25',
                'availability': 'morning',
                'address': '456 Solar Street, Harare'
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            self.flow, self.contact, response_data
        )
        
        # Check processing succeeded
        self.assertTrue(flow_response.is_processed)
        
        # Check cleaning request was created
        cleaning_req = SolarCleaningRequest.objects.filter(
            customer__contact=self.contact
        ).first()
        self.assertIsNotNone(cleaning_req)
        self.assertEqual(cleaning_req.panel_count, 15)
        self.assertEqual(cleaning_req.roof_type, 'tile')
        
        # Check confirmation message has all details
        call_args = mock_send_message.call_args
        message_body = call_args[1]['data']['body']
        self.assertIn('Alice Johnson', message_body)
        self.assertIn('15 panels', message_body)
        self.assertIn('Tile', message_body)
        self.assertIn('456 Solar Street', message_body)
        self.assertIn(f'#{cleaning_req.id}', message_body)
