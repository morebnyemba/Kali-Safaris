"""
Custom flow actions for Omari payment integration.

Register with: from omari_integration.flow_actions import register_payment_actions
Then call: register_payment_actions()
"""
import logging
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any

from conversations.models import Contact
from customer_data.models import Booking
from .whatsapp_handler import get_payment_handler


logger = logging.getLogger(__name__)


def initiate_omari_payment_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to initiate Omari payment through WhatsApp.
    
    Params expected:
        - booking_reference: str (required) - Booking reference to pay for
        - amount: str/float (optional) - Amount to charge, defaults to booking balance
        - currency: str (optional) - 'USD' or 'ZWG', defaults to 'USD'
        - channel: str (optional) - 'WEB' or 'POS', defaults to 'WEB'
    
    Returns actions to send OTP instructions to customer.
    """
    booking_ref = params.get('booking_reference')
    if not booking_ref:
        # Try to get from flow context
        booking_ref = flow_context.get('booking_reference')
    
    if not booking_ref:
        logger.error(f"initiate_omari_payment action: missing booking_reference for contact {contact.id}")
        return [{
            'type': 'send_text',
            'text': '❌ Payment initiation failed: No booking found. Please contact support.'
        }]
    
    logger.info(
        "initiate_omari_payment action start | contact=%s booking_ref=%s amount_param=%s currency=%s channel=%s",
        contact.id,
        booking_ref,
        params.get('amount'),
        params.get('currency'),
        params.get('channel'),
    )

    # Get booking
    try:
        booking = Booking.objects.get(booking_reference=booking_ref)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_ref} not found for payment initiation")
        return [{
            'type': 'send_text',
            'text': f'❌ Booking {booking_ref} not found. Please verify your booking reference.'
        }]
    
    # Determine amount
    amount_str = params.get('amount')
    if amount_str:
        try:
            amount = Decimal(str(amount_str))
        except (InvalidOperation, ValueError, TypeError):
            logger.error(f"Invalid amount '{amount_str}' for payment")
            amount = booking.total_amount - booking.amount_paid
    else:
        # Default to remaining balance
        amount = booking.total_amount - booking.amount_paid
    
    if amount <= 0:
        logger.info("initiate_omari_payment action: booking %s already paid for contact %s", booking_ref, contact.id)
        return [{
            'type': 'send_text',
            'text': f'✅ Booking {booking_ref} is already paid in full!'
        }]
    
    currency = params.get('currency', 'USD')
    channel = params.get('channel', 'WEB')
    
    # Get payment phone from flow context (user-entered phone), fallback to contact phone
    payment_phone = params.get('msisdn') or flow_context.get('payment_phone', contact.whatsapp_id)
    
    # Initiate payment with exception handling
    handler = get_payment_handler()
    try:
        result = handler.initiate_payment(
            contact=contact,
            booking=booking,
            amount=amount,
            currency=currency,
            channel=channel,
            msisdn=payment_phone
        )
    except Exception as exc:
        logger.error(
            "initiate_omari_payment action: payment handler exception | contact=%s booking_ref=%s error=%s",
            contact.id,
            booking_ref,
            exc,
            exc_info=True,
        )
        return [{
            'type': 'send_text',
            'text': f'❌ Payment service error: {str(exc)}\\nPlease try again or contact support.'
        }]
    
    if result['success']:
        otp_ref = result.get('otp_reference', 'N/A')
        logger.info(
            "initiate_omari_payment action success | contact=%s booking_ref=%s reference=%s otp_ref=%s amount=%s %s",
            contact.id,
            booking_ref,
            result.get('reference'),
            otp_ref,
            amount,
            currency,
        )
        message = (
            f"💳 *Payment Initiated*\\n\\n"
            f"Booking: {booking.booking_reference}\\n"
            f"Amount: {currency} {amount}\\n\\n"
            f"🔐 *OTP Reference: {otp_ref}*\\n\\n"
            f"Please check your phone for an OTP code via SMS/Email.\\n"
            f"Reply with your OTP code to complete the payment."
        )
        
        # Store in context for next step
        # CRITICAL: flow transition checks for variable_exists omari_otp_reference
        flow_context['omari_otp_reference'] = result.get('otp_reference')
        flow_context['_payment_reference'] = result['reference']
        
        return [{
            'type': 'send_text',
            'text': message
        }]
    else:
        error_msg = result.get('message', 'Unknown error')
        logger.error(
            "Payment initiation failed for booking %s contact=%s reference=%s: %s",
            booking_ref,
            contact.id,
            result.get('reference'),
            error_msg,
        )
        return [{
            'type': 'send_text',
            'text': f'❌ Payment initiation failed: {error_msg}\\nPlease try again or contact support.'
        }]


def verify_omari_user_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to verify if the current contact is an eligible Omari user.
    Sets flow_context['is_omari_user'] to True/False. Returns no messages.
    """
    handler = get_payment_handler()
    logger.info("verify_omari_user action start | contact=%s", contact.id)
    try:
        eligibility = handler.is_omari_user(contact)  # 'true' or 'unknown'
        flow_context['is_omari_user'] = eligibility
        logger.info("verify_omari_user action result | contact=%s eligibility=%s", contact.id, eligibility)
    except Exception as exc:  # pragma: no cover - defensive
        flow_context['is_omari_user'] = 'unknown'
        logger.error("verify_omari_user action failed | contact=%s error=%s", contact.id, exc, exc_info=True)
    return []

def set_omari_not_eligible_message_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """Set a shared message explaining Omari eligibility requirements."""
    flow_context['omari_not_eligible_message'] = (
        "Omari payments are available to Omari users only. It looks like your number isn't "
        "linked to an Omari account. Please choose another payment method (e.g., Ecocash/"
        "Innbucks via Paynow) or link your Omari account first."
    )
    return []


def process_otp_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to process OTP input from customer.
    
    This should be called when customer sends a message while awaiting OTP.
    Params expected:
        - otp: str (required) - The OTP code from user input
    
    Returns actions to confirm payment or show error.
    """
    logger.info(
        "process_otp_action called | contact=%s params=%s otp_input_var=%s",
        contact.id,
        params,
        flow_context.get('otp_input', '<not set>')
    )
    
    otp = params.get('otp')
    if not otp:
        # Try to get from flow context (captured from user message)
        otp = flow_context.get('user_message', '').strip()
    
    logger.info(
        "process_otp_action: resolved OTP | contact=%s otp=%s",
        contact.id,
        '***' + otp[-2:] if otp and len(otp) >= 2 else '<empty>'
    )
    
    if not otp:
        logger.warning("process_otp_action: no OTP provided | contact=%s", contact.id)
        return [{
            'type': 'send_text',
            'text': '❌ Please provide your OTP code to complete the payment.'
        }]
    
    handler = get_payment_handler()
    result = handler.process_otp_input(contact, otp)
    
    logger.info(
        "process_otp_action: handler result | contact=%s success=%s message=%s",
        contact.id,
        result.get('success'),
        result.get('message', 'N/A')
    )
    
    if result['success']:
        booking = result.get('booking')
        payment_ref = result.get('payment_reference', 'N/A')
        
        logger.info(
            "process_otp_action: payment successful | contact=%s payment_ref=%s booking_id=%s",
            contact.id,
            payment_ref,
            booking.id if booking else 'N/A'
        )
        
        message = (
            f"✅ *Payment Successful!*\\n\\n"
            f"Payment Reference: {payment_ref}\\n"
        )
        
        if booking:
            message += (
                f"Booking: {booking.booking_reference}\\n"
                f"Status: {booking.get_payment_status_display()}\\n"
                f"Amount Paid: {booking.currency if hasattr(booking, 'currency') else 'USD'} {booking.amount_paid}\\n"
                f"Total: {booking.currency if hasattr(booking, 'currency') else 'USD'} {booking.total_amount}"
            )
        
        message += "\\n\\nThank you for your payment! 🎉"
        
        # Set success flag for flow transition
        flow_context['omari_payment_success'] = True
        logger.info(
            "process_otp_action: set context variable | contact=%s omari_payment_success=True",
            contact.id
        )
        
        # Clear payment state from context
        flow_context.pop('_payment_initiated', None)
        flow_context.pop('_payment_reference', None)
        
        return [{
            'type': 'send_text',
            'text': message
        }]
    else:
        error_msg = result.get('message', 'Payment processing failed')
        response_code = result.get('response_code', '')
        
        logger.warning(
            "process_otp_action: payment failed | contact=%s error=%s response_code=%s",
            contact.id,
            error_msg,
            response_code
        )
        
        message = f"❌ *Payment Failed*\\n\\n{error_msg}"
        if response_code and response_code != '000':
            message += f"\\nError Code: {response_code}"
        message += "\\n\\nPlease try again or contact support."
        
        return [{
            'type': 'send_text',
            'text': message
        }]


def cancel_payment_action(contact: Contact, flow_context: dict, params: dict) -> List[Dict[str, Any]]:
    """
    Flow action to cancel pending payment.
    """
    handler = get_payment_handler()
    handler.cancel_payment(contact)
    
    # Clear from context
    flow_context.pop('_payment_initiated', None)
    flow_context.pop('_payment_reference', None)
    
    return [{
        'type': 'send_text',
        'text': '❌ Payment cancelled. You can initiate a new payment anytime.'
    }]


def validate_omari_phone_action(contact: Contact, flow_context: dict, params: dict) -> Dict[str, Any]:
    """
    Validate phone number format for Omari payment.
    
    Params expected:
        - phone_variable: str - Name of context variable containing phone number
    
    Returns context update with 'payment_phone_valid' if valid, otherwise empty dict.
    """
    import re
    
    phone_var = params.get('phone_variable', 'payment_phone')
    phone = flow_context.get(phone_var, '').strip()
    
    # Zimbabwe mobile format: 2637XXXXXXXX (12 digits total)
    PHONE_REGEX = r'^2637[0-9]{8}$'
    
    if not phone:
        logger.warning(
            "validate_omari_phone: no phone number in context | contact=%s variable=%s",
            contact.id,
            phone_var
        )
        return {}
    
    if re.match(PHONE_REGEX, phone):
        logger.info(
            "validate_omari_phone: valid format | contact=%s phone=***%s",
            contact.id,
            phone[-4:] if len(phone) >= 4 else "****"
        )
        # Return context update to set validation flag
        return {'payment_phone_valid': True}
    else:
        logger.warning(
            "validate_omari_phone: invalid format | contact=%s phone=***%s expected_format=2637XXXXXXXX",
            contact.id,
            phone[-4:] if len(phone) >= 4 else "****"
        )
        return {}


def register_payment_actions():
    """Register Omari payment actions with the flow action registry."""
    from flows.services import flow_action_registry

    flow_action_registry.register('initiate_omari_payment', initiate_omari_payment_action)
    flow_action_registry.register('verify_omari_user', verify_omari_user_action)
    flow_action_registry.register('set_omari_not_eligible_message', set_omari_not_eligible_message_action)
    flow_action_registry.register('process_otp', process_otp_action)
    flow_action_registry.register('cancel_payment', cancel_payment_action)
    flow_action_registry.register('validate_omari_phone', validate_omari_phone_action)

    logger.info("Registered Omari payment flow actions")

