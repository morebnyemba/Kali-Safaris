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
    @transaction.atomic
    def process_response(whatsapp_flow: WhatsAppFlow, contact: Contact, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Pure data processor: Updates the contact's flow context with WhatsApp flow response data.
        Should be called from the webhook handler when a flow response is received.
        
        This method is atomic - it either succeeds completely or rolls back all changes.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance
            contact: The contact who submitted the response
            response_data: The response payload from Meta
        Returns:
            Dict with status and notes, or None if failed
        """
        try:
            # Save the flow response for audit/history
            WhatsAppFlowResponse.objects.create(
                whatsapp_flow=whatsapp_flow,
                contact=contact,
                flow_token=response_data.get('flow_token', ''),
                response_data=response_data,
                is_processed=True
            )
            logger.info(f"Saved WhatsAppFlowResponse for contact {contact.id} and flow {whatsapp_flow.name}.")

            # Update the flow context for the contact (if in a flow)
            from .models import ContactFlowState
            flow_state = ContactFlowState.objects.select_for_update().filter(contact=contact).first()
            
            if not flow_state:
                logger.warning(f"No active flow state for contact {contact.id} when processing WhatsApp flow response.")
                return {"success": False, "notes": "No active flow state for contact."}
            
            # Merge WhatsApp flow data into the flow context
            context = flow_state.flow_context_data or {}
            wa_data = response_data.get('data', response_data)
            
            # Merge at top level for easy access
            context.update(wa_data)
            
            # Also keep under a subkey for backward compatibility
            context['whatsapp_flow_data'] = wa_data
            
            # Set the flag for transition condition - this is critical for automatic transition
            context['whatsapp_flow_response_received'] = True
            
            # Update the flow state with the new context
            flow_state.flow_context_data = context
            flow_state.last_updated_at = timezone.now()
            flow_state.save(update_fields=["flow_context_data", "last_updated_at"])
            
            logger.info(
                f"Successfully updated flow context for contact {contact.id} with WhatsApp flow data. "
                f"Set whatsapp_flow_response_received=True. Current step: {flow_state.current_step.name}"
            )
            
            return {
                "success": True, 
                "notes": "Flow context updated with WhatsApp flow data and response flag set."
            }
            
        except Exception as e:
            logger.error(
                f"Error processing WhatsApp flow response for contact {contact.id}: {e}", 
                exc_info=True
            )
            # Transaction will be rolled back automatically due to @transaction.atomic
            return None

