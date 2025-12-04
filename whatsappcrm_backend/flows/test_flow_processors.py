"""
Tests for WhatsApp Flow Response Processors.
Validates that backend handlers correctly process flow submissions and automatic transitions.
"""

from django.test import TestCase, override_settings
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.utils import timezone

from flows.models import (
    WhatsAppFlow, WhatsAppFlowResponse, Flow, FlowStep, 
    FlowTransition, ContactFlowState
)
from flows.whatsapp_flow_response_processor import WhatsAppFlowResponseProcessor
from flows.services import process_whatsapp_flow_response
from conversations.models import Contact
from customer_data.models import (
    CustomerProfile, Booking, TourInquiry
)
from meta_integration.models import MetaAppConfig


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=False,  # Don't execute tasks at all during tests
    CELERY_TASK_EAGER_PROPAGATES=False,
    BROKER_BACKEND='memory'
)
@patch('stats.signals.update_dashboard_stats.apply_async', MagicMock(return_value=MagicMock()))
@patch('stats.signals.broadcast_activity_log.delay', MagicMock(return_value=MagicMock()))
@patch('stats.tasks.update_dashboard_stats.delay', MagicMock(return_value=MagicMock()))
class WhatsAppFlowResponseProcessorTests(TestCase):
    """Test suite for WhatsApp Flow Response Processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test contact
        self.contact = Contact.objects.create(
            whatsapp_id="+1234567890",
            name="Test User"
        )
        
        # Create a test Meta app config
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            phone_number_id="123456789",
            is_active=True
        )
        
        # Create a test traditional flow
        self.flow = Flow.objects.create(
            name="test_flow",
            friendly_name="Test Flow",
            is_active=True
        )
        
        # Create flow steps
        self.wait_step = FlowStep.objects.create(
            flow=self.flow,
            name="wait_for_flow_response",
            step_type="action",
            config={"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "awaiting_response", "value_template": True}]},
            is_entry_point=False
        )
        
        self.process_step = FlowStep.objects.create(
            flow=self.flow,
            name="process_data",
            step_type="action",
            config={"actions_to_run": []},
            is_entry_point=False
        )
        
        # Create transition
        self.transition = FlowTransition.objects.create(
            current_step=self.wait_step,
            next_step=self.process_step,
            priority=1,
            condition_config={
                "type": "whatsapp_flow_response_received",
                "variable_name": "whatsapp_flow_response_received"
            }
        )
        
        # Create a WhatsApp flow
        self.whatsapp_flow = WhatsAppFlow.objects.create(
            name="tour_inquiry_whatsapp",
            friendly_name="Tour Inquiry",
            meta_app_config=self.meta_config,
            flow_id="123456789",
            flow_json={"screens": []},
            sync_status="published",
            is_active=True
        )
    
    def test_process_response_creates_flow_response_record(self):
        """Test that processing a response creates a WhatsAppFlowResponse record."""
        # Create a flow state for the contact
        flow_state = ContactFlowState.objects.create(
            contact=self.contact,
            current_flow=self.flow,
            current_step=self.wait_step,
            flow_context_data={"awaiting_response": True}
        )
        
        response_data = {
            "flow_token": "test-token-123",
            "data": {
                "destinations": "Kenya",
                "preferred_dates": "2024-12-01",
                "number_of_travelers": 2
            }
        }
        
        result = WhatsAppFlowResponseProcessor.process_response(
            whatsapp_flow=self.whatsapp_flow,
            contact=self.contact,
            response_data=response_data
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result.get("success"))
        
        # Verify WhatsAppFlowResponse was created
        flow_response = WhatsAppFlowResponse.objects.filter(
            whatsapp_flow=self.whatsapp_flow,
            contact=self.contact
        ).first()
        
        self.assertIsNotNone(flow_response)
        self.assertEqual(flow_response.flow_token, "test-token-123")
        self.assertTrue(flow_response.is_processed)
    
    def test_process_response_updates_flow_context(self):
        """Test that processing a response updates the contact's flow context."""
        # Create a flow state for the contact
        flow_state = ContactFlowState.objects.create(
            contact=self.contact,
            current_flow=self.flow,
            current_step=self.wait_step,
            flow_context_data={"awaiting_response": True}
        )
        
        response_data = {
            "data": {
                "destinations": "Kenya",
                "preferred_dates": "2024-12-01",
                "number_of_travelers": 2
            }
        }
        
        result = WhatsAppFlowResponseProcessor.process_response(
            whatsapp_flow=self.whatsapp_flow,
            contact=self.contact,
            response_data=response_data
        )
        
        # Reload the flow state
        flow_state.refresh_from_db()
        
        # Verify the context was updated with response data
        self.assertTrue(flow_state.flow_context_data.get("whatsapp_flow_response_received"))
        self.assertEqual(flow_state.flow_context_data.get("destinations"), "Kenya")
        self.assertEqual(flow_state.flow_context_data.get("preferred_dates"), "2024-12-01")
        self.assertEqual(flow_state.flow_context_data.get("number_of_travelers"), 2)
        
        # Verify the data is also stored under the 'whatsapp_flow_data' key
        self.assertIn("whatsapp_flow_data", flow_state.flow_context_data)
        self.assertEqual(
            flow_state.flow_context_data["whatsapp_flow_data"]["destinations"],
            "Kenya"
        )
    
    def test_process_response_sets_transition_flag(self):
        """Test that the transition flag is set correctly for automatic transition."""
        # Create a flow state for the contact
        flow_state = ContactFlowState.objects.create(
            contact=self.contact,
            current_flow=self.flow,
            current_step=self.wait_step,
            flow_context_data={}
        )
        
        response_data = {
            "data": {"test_field": "test_value"}
        }
        
        result = WhatsAppFlowResponseProcessor.process_response(
            whatsapp_flow=self.whatsapp_flow,
            contact=self.contact,
            response_data=response_data
        )
        
        # Reload the flow state
        flow_state.refresh_from_db()
        
        # Verify the transition flag is set
        self.assertTrue(
            flow_state.flow_context_data.get("whatsapp_flow_response_received"),
            "The whatsapp_flow_response_received flag should be set to True"
        )
    
    def test_process_response_without_flow_state(self):
        """Test that processing fails gracefully when no flow state exists."""
        response_data = {
            "data": {"test_field": "test_value"}
        }
        
        result = WhatsAppFlowResponseProcessor.process_response(
            whatsapp_flow=self.whatsapp_flow,
            contact=self.contact,
            response_data=response_data
        )
        
        self.assertIsNotNone(result)
        self.assertFalse(result.get("success"))
        self.assertIn("No active flow state", result.get("notes", ""))
    
    def test_process_whatsapp_flow_response_identifies_flow(self):
        """Test that process_whatsapp_flow_response correctly identifies the WhatsApp flow."""
        # Create a flow state
        flow_state = ContactFlowState.objects.create(
            contact=self.contact,
            current_flow=self.flow,
            current_step=self.wait_step,
            flow_context_data={}
        )
        
        msg_data = {
            "type": "interactive",
            "interactive": {
                "type": "nfm_reply",
                "nfm_reply": {
                    "response_json": '{"destinations": "Kenya", "preferred_dates": "2024-12-01"}',
                    "flow_token": "test-token"
                }
            }
        }
        
        success, notes = process_whatsapp_flow_response(
            msg_data, self.contact, self.meta_config
        )
        
        self.assertTrue(success)
        self.assertIn("Flow context updated", notes)
        
        # Verify the flow state was updated
        flow_state.refresh_from_db()
        self.assertTrue(flow_state.flow_context_data.get("whatsapp_flow_response_received"))


