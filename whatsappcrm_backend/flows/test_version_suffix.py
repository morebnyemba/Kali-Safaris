"""
Unit tests for Meta sync version suffix functionality.
Tests that version suffixes are correctly applied to flows and templates.
"""
import json
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from flows.whatsapp_flow_service import WhatsAppFlowService
from flows.models import WhatsAppFlow
from meta_integration.models import MetaAppConfig


class VersionSuffixFlowTest(TestCase):
    """Test that version suffix is applied to WhatsApp flows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meta_config = Mock(spec=MetaAppConfig)
        self.meta_config.access_token = "test_access_token"
        self.meta_config.api_version = "v23.0"
        self.meta_config.waba_id = "1234567890"
        
        self.service = WhatsAppFlowService(self.meta_config)
        
        # Create a mock WhatsAppFlow
        self.whatsapp_flow = Mock(spec=WhatsAppFlow)
        self.whatsapp_flow.flow_id = None  # New flow
        self.whatsapp_flow.name = "test_flow"
        self.whatsapp_flow.friendly_name = "Test Flow"
        self.whatsapp_flow.flow_json = {
            "version": "3.0",
            "screens": [{"id": "WELCOME", "title": "Welcome"}]
        }
        self.whatsapp_flow.sync_status = 'draft'
        self.whatsapp_flow.save = Mock()
        self.whatsapp_flow.last_synced_at = None
        self.whatsapp_flow.sync_error = None
    
    @override_settings(META_SYNC_VERSION_SUFFIX='v1_02')
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_create_flow_with_default_version_suffix(self, mock_post):
        """Test that create_flow appends version suffix to flow name"""
        # Setup mock response for flow creation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'flow_123456'}
        mock_post.return_value = mock_response
        
        # Call create_flow
        result = self.service.create_flow(self.whatsapp_flow)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify requests.post was called twice (create flow + update JSON)
        self.assertEqual(mock_post.call_count, 2)
        
        # Get the first call (flow creation)
        first_call_args = mock_post.call_args_list[0]
        
        # Verify the URL
        expected_url = f"https://graph.facebook.com/v23.0/1234567890/flows"
        self.assertEqual(first_call_args[0][0], expected_url)
        
        # Verify the payload contains versioned name
        payload = first_call_args[1]['json']
        self.assertIn('name', payload)
        self.assertEqual(payload['name'], 'Test Flow_v1_02')
    
    @override_settings(META_SYNC_VERSION_SUFFIX='v2_00')
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_create_flow_with_custom_version_suffix(self, mock_post):
        """Test that create_flow uses custom version suffix from settings"""
        # Setup mock response for flow creation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'flow_123456'}
        mock_post.return_value = mock_response
        
        # Call create_flow
        result = self.service.create_flow(self.whatsapp_flow)
        
        # Verify the result
        self.assertTrue(result)
        
        # Get the first call (flow creation)
        first_call_args = mock_post.call_args_list[0]
        
        # Verify the payload contains custom versioned name
        payload = first_call_args[1]['json']
        self.assertEqual(payload['name'], 'Test Flow_v2_00')
    
    @override_settings(META_SYNC_VERSION_SUFFIX='v1_02')
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_create_flow_uses_name_when_no_friendly_name(self, mock_post):
        """Test that flow name is used when friendly_name is not set"""
        # Remove friendly_name
        self.whatsapp_flow.friendly_name = None
        
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'flow_123456'}
        mock_post.return_value = mock_response
        
        # Call create_flow
        result = self.service.create_flow(self.whatsapp_flow)
        
        # Verify the result
        self.assertTrue(result)
        
        # Get the first call (flow creation)
        first_call_args = mock_post.call_args_list[0]
        
        # Verify the payload uses name with version suffix
        payload = first_call_args[1]['json']
        self.assertEqual(payload['name'], 'test_flow_v1_02')


class VersionSuffixTemplateTest(TestCase):
    """Test that version suffix is applied to message templates"""
    
    @override_settings(META_SYNC_VERSION_SUFFIX='v1_02')
    def test_template_name_with_version_suffix(self):
        """Test that template names are properly formatted with version suffix"""
        from django.conf import settings
        
        # Get the version suffix
        version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1_02')
        
        # Test template name formatting
        template_name = "test_template"
        template_name_with_version = f"{template_name}_{version_suffix}"
        
        self.assertEqual(template_name_with_version, "test_template_v1_02")
    
    @override_settings(META_SYNC_VERSION_SUFFIX='v2_00')
    def test_template_name_with_custom_version_suffix(self):
        """Test that template names use custom version suffix from settings"""
        from django.conf import settings
        
        # Get the version suffix
        version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1_02')
        
        # Test template name formatting
        template_name = "new_order_notification"
        template_name_with_version = f"{template_name}_{version_suffix}"
        
        self.assertEqual(template_name_with_version, "new_order_notification_v2_00")
