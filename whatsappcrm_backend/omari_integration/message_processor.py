"""
Message processor for handling Omari payment OTP flow in WhatsApp.

This processor intercepts messages when a payment is pending and processes OTP inputs.
"""
import logging
import re

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from conversations.models import Contact, Message
from .whatsapp_handler import get_payment_handler

logger = logging.getLogger(__name__)

try:
    from flows.models import ContactFlowState
    FLOW_STATE_AVAILABLE = True
except ImportError:
    FLOW_STATE_AVAILABLE = False
    logger.warning("ContactFlowState not available - flow-based OTP handling check will be skipped")

# Flow step names where OTP collection is handled by the flow system
FLOW_OTP_COLLECTION_STEPS = ['omari_payment_initiated', 'omari_payment_failed']


def process_payment_message(contact: Contact, message: Message) -> bool:
    """
    Process incoming message for payment flow.
    
    Returns True if message was handled as payment OTP, False otherwise.
    """
    # Only process incoming text messages
    if message.direction != 'in' or message.message_type != 'text':
        return False
    
    handler = get_payment_handler()
    
    # Check if contact is awaiting OTP
    if not handler.is_awaiting_otp(contact):
        return False
    
    # Check if contact is in a flow step that handles OTP collection
    # If so, let the flow handle the message instead of intercepting it here
    if FLOW_STATE_AVAILABLE:
        try:
            contact_flow_state = ContactFlowState.objects.select_related('current_step').filter(contact=contact).first()
            if contact_flow_state and contact_flow_state.current_step:
                # If contact is in a flow OTP collection step, let the flow handle it
                step_name = contact_flow_state.current_step.name
                if step_name in FLOW_OTP_COLLECTION_STEPS:
                    logger.debug(f"Contact {contact.id} is in flow step '{step_name}' - letting flow handle OTP input")
                    return False
        except (ObjectDoesNotExist, DatabaseError) as e:
            logger.error(f"Database error checking contact flow state in payment processor: {e}", exc_info=True)
            # Continue with message processing on database errors
        except Exception as e:
            logger.warning(f"Unexpected error checking contact flow state in payment processor: {e}")
    
    text = (message.text_content or '').strip()
    
    # Check for cancellation keywords
    if text.lower() in ['cancel', 'cancel payment', 'stop', 'quit']:
        handler.cancel_payment(contact)
        _send_whatsapp_message(contact, '❌ Payment cancelled. You can initiate a new payment anytime.')
        return True
    
    # Extract OTP - typically 4-6 digit code
    otp_match = re.search(r'\\b\\d{4,6}\\b', text)
    if otp_match:
        otp = otp_match.group(0)
        
        # Process OTP
        result = handler.process_otp_input(contact, otp)
        
        if result['success']:
            booking = result.get('booking')
            payment_ref = result.get('payment_reference', 'N/A')
            
            msg = (
                f"✅ *Payment Successful!*\\n\\n"
                f"Payment Reference: {payment_ref}\\n"
            )
            
            if booking:
                msg += (
                    f"Booking: {booking.booking_reference}\\n"
                    f"Status: {booking.get_payment_status_display()}\\n"
                    f"Amount Paid: USD {booking.amount_paid}\\n"
                    f"Total: USD {booking.total_amount}"
                )
            
            msg += "\\n\\nThank you for your payment! 🎉"
            _send_whatsapp_message(contact, msg)
        else:
            error_msg = result.get('message', 'Payment processing failed')
            msg = f"❌ *Payment Failed*\\n\\n{error_msg}\\n\\nPlease check your OTP and try again, or type 'cancel' to cancel this payment."
            _send_whatsapp_message(contact, msg)
        
        return True
    else:
        # No valid OTP found, ask again
        payment_state = handler.get_pending_payment(contact)
        otp_ref = payment_state.get('otp_reference', 'N/A') if payment_state else 'N/A'
        
        msg = (
            f"🔐 *Awaiting OTP*\\n\\n"
            f"OTP Reference: {otp_ref}\\n\\n"
            f"Please reply with your 4-6 digit OTP code to complete the payment.\\n"
            f"Type 'cancel' to cancel this payment."
        )
        _send_whatsapp_message(contact, msg)
        return True


def _send_whatsapp_message(contact: Contact, text: str) -> None:
    """Send a WhatsApp message to contact."""
    try:
        from meta_integration.utils import send_whatsapp_message
        send_whatsapp_message(
            to_phone_number=contact.whatsapp_id,
            message_type='text',
            data={'body': text}
        )
    except Exception as e:
        logger.exception(f"Failed to send WhatsApp message to {contact.whatsapp_id}")
