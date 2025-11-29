"""
Unit tests for WhatsAppFlowService update_flow_json fix.
Tests that the file parameter is correctly sent as multipart/form-data.
"""
import json
from unittest.mock import Mock, patch
from django.test import TestCase
from flows.whatsapp_flow_service import WhatsAppFlowService
from flows.models import WhatsAppFlow
from meta_integration.models import MetaAppConfig


class WhatsAppFlowServiceUpdateFlowJsonTest(TestCase):
    """Test the update_flow_json method uses multipart/form-data correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meta_config = Mock(spec=MetaAppConfig)
        self.meta_config.access_token = "test_access_token"
        self.meta_config.api_version = "v23.0"
        self.meta_config.waba_id = "1234567890"
        
        self.service = WhatsAppFlowService(self.meta_config)
        
        # Create a mock WhatsAppFlow
        self.whatsapp_flow = Mock(spec=WhatsAppFlow)
        self.whatsapp_flow.flow_id = "test_flow_id_123"
        self.whatsapp_flow.name = "test_flow"
        self.whatsapp_flow.friendly_name = "Test Flow"
        self.whatsapp_flow.flow_json = {
            "version": "3.0",
            "screens": [
                {
                    "id": "WELCOME",
                    "title": "Welcome"
                }
            ]
        }
        self.whatsapp_flow.sync_status = 'draft'
        self.whatsapp_flow.save = Mock()
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_sends_file_parameter(self, mock_post):
        """Test that update_flow_json sends file as multipart/form-data"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.service.update_flow_json(self.whatsapp_flow)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify requests.post was called
        self.assertTrue(mock_post.called)
        
        # Get the call arguments
        call_args = mock_post.call_args
        
        # Verify the URL
        expected_url = f"https://graph.facebook.com/v23.0/{self.whatsapp_flow.flow_id}/assets"
        self.assertEqual(call_args[0][0], expected_url)
        
        # Verify headers (should NOT include Content-Type for multipart)
        headers = call_args[1]['headers']
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], 'Bearer test_access_token')
        self.assertNotIn('Content-Type', headers)
        
        # Verify data parameter (form fields)
        data = call_args[1]['data']
        self.assertIn('name', data)
        self.assertEqual(data['name'], 'Test Flow')
        self.assertIn('asset_type', data)
        self.assertEqual(data['asset_type'], 'FLOW_JSON')
        
        # Verify files parameter (the file upload)
        files = call_args[1]['files']
        self.assertIn('file', files)
        
        # Verify the file tuple structure: (filename, content, content_type)
        file_tuple = files['file']
        self.assertEqual(len(file_tuple), 3)
        self.assertEqual(file_tuple[0], 'flow.json')  # filename
        self.assertEqual(file_tuple[2], 'application/json')  # content type
        
        # Verify the file content is valid JSON
        file_content = file_tuple[1]
        parsed_json = json.loads(file_content)
        self.assertEqual(parsed_json['version'], '3.0')
        self.assertIn('screens', parsed_json)
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_without_flow_id(self, mock_post):
        """Test that update_flow_json fails gracefully without flow_id"""
        self.whatsapp_flow.flow_id = None
        
        result = self.service.update_flow_json(self.whatsapp_flow)
        
        # Should return False
        self.assertFalse(result)
        
        # Should not call requests.post
        self.assertFalse(mock_post.called)
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_handles_api_error(self, mock_post):
        """Test that update_flow_json handles API errors properly"""
        # Setup mock response with error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {
                'message': 'Bad request',
                'type': 'OAuthException',
                'code': 100
            }
        }
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response
        
        result = self.service.update_flow_json(self.whatsapp_flow)
        
        # Should return False on error
        self.assertFalse(result)
        
        # Verify sync_status was set to 'error'
        # Last save call should have set sync_status to 'error'
        self.assertEqual(self.whatsapp_flow.sync_status, 'error')
