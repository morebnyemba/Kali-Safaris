"""
Unit tests for the sync_whatsapp_flows management command.
Tests that WhatsApp Flows are properly linked to traditional flows via flow_definition FK.
"""
from unittest.mock import Mock, patch
from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from flows.models import WhatsAppFlow, Flow
from meta_integration.models import MetaAppConfig


class SyncWhatsAppFlowsCommandTest(TestCase):
    """Test the sync_whatsapp_flows command links flows correctly"""
    
    def setUp(self):
        """Create test MetaAppConfig and traditional Flow fixtures for testing WhatsApp Flow linking"""
        # Create a mock MetaAppConfig
        self.meta_config = MetaAppConfig.objects.create(
            name='Test Config',
            app_id='test_app_id',
            app_secret='test_secret',
            access_token='test_token',
            phone_number_id='test_phone_id',
            waba_id='test_waba_id',
            is_active=True
        )
        
        # Create the traditional flow that should be linked
        self.tour_inquiry_flow = Flow.objects.create(
            name='tour_inquiry_flow',
            friendly_name='Tour Inquiry Flow',
            description='Traditional tour inquiry flow',
            is_active=True
        )
    
    @patch('flows.management.commands.sync_whatsapp_flows.WhatsAppFlowService')
    def test_sync_command_links_flow_definition(self, mock_service_class):
        """Test that sync command properly links WhatsApp Flow to traditional flow"""
        # Setup mock service
        mock_service = Mock()
        mock_service.sync_flow.return_value = True
        mock_service_class.return_value = mock_service
        
        # Capture command output
        out = StringIO()
        
        # Run the sync command
        call_command('sync_whatsapp_flows', '--flow=tour_inquiry', stdout=out)
        
        # Verify WhatsApp Flow was created and linked
        whatsapp_flow = WhatsAppFlow.objects.get(name='tour_inquiry_whatsapp')
        
        # Assert flow_definition is set correctly
        self.assertIsNotNone(whatsapp_flow.flow_definition)
        self.assertEqual(whatsapp_flow.flow_definition, self.tour_inquiry_flow)
        self.assertEqual(whatsapp_flow.flow_definition.name, 'tour_inquiry_flow')
        
        # Verify output message
        output = out.getvalue()
        self.assertIn('Found traditional flow: tour_inquiry_flow', output)
    
    @patch('flows.management.commands.sync_whatsapp_flows.WhatsAppFlowService')
    def test_sync_command_handles_missing_flow_definition(self, mock_service_class):
        """Test that sync command handles case when traditional flow doesn't exist"""
        # Setup mock service
        mock_service = Mock()
        mock_service.sync_flow.return_value = True
        mock_service_class.return_value = mock_service
        
        # Delete the traditional flow to simulate missing flow
        self.tour_inquiry_flow.delete()
        
        # Capture command output
        out = StringIO()
        
        # Run the sync command - should not fail
        call_command('sync_whatsapp_flows', '--flow=tour_inquiry', stdout=out)
        
        # Verify WhatsApp Flow was created without flow_definition
        whatsapp_flow = WhatsAppFlow.objects.get(name='tour_inquiry_whatsapp')
        self.assertIsNone(whatsapp_flow.flow_definition)
        
        # Verify warning message
        output = out.getvalue()
        self.assertIn('Warning: Traditional flow "tour_inquiry_flow" not found', output)
    
    @patch('flows.management.commands.sync_whatsapp_flows.WhatsAppFlowService')
    def test_sync_command_updates_flow_definition_on_force(self, mock_service_class):
        """Test that sync command updates flow_definition when --force is used"""
        # Setup mock service
        mock_service = Mock()
        mock_service.sync_flow.return_value = True
        mock_service_class.return_value = mock_service
        
        # Create WhatsApp Flow without flow_definition
        whatsapp_flow = WhatsAppFlow.objects.create(
            name='tour_inquiry_whatsapp',
            friendly_name='Tour Inquiry WhatsApp Flow',
            description='Test',
            flow_json={'version': '7.3'},
            meta_app_config=self.meta_config,
            sync_status='draft',
            is_active=True
        )
        self.assertIsNone(whatsapp_flow.flow_definition)
        
        # Run sync with --force to update
        out = StringIO()
        call_command('sync_whatsapp_flows', '--flow=tour_inquiry', '--force', stdout=out)
        
        # Verify flow_definition was updated
        whatsapp_flow.refresh_from_db()
        self.assertIsNotNone(whatsapp_flow.flow_definition)
        self.assertEqual(whatsapp_flow.flow_definition, self.tour_inquiry_flow)
    
    @patch('flows.management.commands.sync_whatsapp_flows.WhatsAppFlowService')
    def test_date_picker_flow_has_no_flow_definition(self, mock_service_class):
        """Test that date_picker flow (reusable component) has no flow_definition"""
        # Setup mock service
        mock_service = Mock()
        mock_service.sync_flow.return_value = True
        mock_service_class.return_value = mock_service
        
        # Run the sync command for date_picker
        out = StringIO()
        call_command('sync_whatsapp_flows', '--flow=date_picker', stdout=out)
        
        # Verify WhatsApp Flow was created without flow_definition
        whatsapp_flow = WhatsAppFlow.objects.get(name='date_picker_whatsapp_flow')
        self.assertIsNone(whatsapp_flow.flow_definition)
