# whatsappcrm_backend/flows/whatsapp_flow_response_processor.py
"""
Service for processing WhatsApp Flow responses and mapping them to existing models.
Handles the conversion of flow response data into TourInquiry and Booking objects.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from .models import WhatsAppFlow, WhatsAppFlowResponse
from conversations.models import Contact
from customer_data.models import CustomerProfile, Booking, TourInquiry
from meta_integration.utils import send_whatsapp_message

logger = logging.getLogger(__name__)

class WhatsAppFlowResponseProcessor:
    """
    Processes WhatsApp Flow responses and creates appropriate business entities.
    """
    
    @staticmethod
    def process_response(whatsapp_flow: WhatsAppFlow, contact: Contact, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Pure data processor: Updates the contact's flow context with WhatsApp flow response data.
        Should be called as a task from services.py when a flow response is received.
        Args:
            whatsapp_flow: The WhatsAppFlow instance
            contact: The contact who submitted the response
            response_data: The response payload from Meta
        Returns:
            Dict with status and notes, or None if failed
        """
        try:
            # Save the flow response for audit/history
            with transaction.atomic():
                WhatsAppFlowResponse.objects.create(
                    whatsapp_flow=whatsapp_flow,
                    contact=contact,
                    flow_token=response_data.get('flow_token', ''),
                    response_data=response_data,
                    is_processed=True
                )

            # Update the flow context for the contact (if in a flow)
            from .models import ContactFlowState
            flow_state = ContactFlowState.objects.filter(contact=contact).first()
            if flow_state:
                # Merge WhatsApp flow data into the flow context (top-level and under a subkey for compatibility)
                context = flow_state.flow_context_data or {}
                wa_data = response_data.get('data', response_data)
                # Merge at top level
                context.update(wa_data)
                # Also keep under a subkey for backward compatibility
                context['whatsapp_flow_data'] = wa_data
                # Set the flag for transition condition
                context['whatsapp_flow_response_received'] = True
                flow_state.flow_context_data = context
                flow_state.last_updated_at = timezone.now()
                flow_state.save(update_fields=["flow_context_data", "last_updated_at"])
                logger.info(f"Updated flow context for contact {contact.id} with WhatsApp flow data and set whatsapp_flow_response_received=True.")
                return {"success": True, "notes": "Flow context updated with WhatsApp flow data and response flag set."}
            else:
                logger.info(f"No active flow state for contact {contact.id} when processing WhatsApp flow response.")
                return {"success": False, "notes": "No active flow state for contact."}
        except Exception as e:
            logger.error(f"Error processing WhatsApp flow response: {e}", exc_info=True)
            return None

