"""
Custom flow actions for CBZ/iVeri EcoCash payment integration.

Register with: from cbz_integration.flow_actions import register_cbz_payment_actions
Then call: register_cbz_payment_actions()
"""
import logging
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any

from conversations.models import Contact
from customer_data.models import Booking
from .whatsapp_handler import get_cbz_payment_handler


logger = logging.getLogger(__name__)


def initiate_cbz_ecocash_payment_action(
    contact: Contact, flow_context: dict, params: dict
) -> List[Dict[str, Any]]:
    """
    Flow action to initiate CBZ/iVeri EcoCash payment through WhatsApp.

    Unlike Omari, this triggers an STK Push directly — no OTP step needed.
    The customer enters their EcoCash PIN on their phone and the payment
    completes in one step.

    Params expected:
        - booking_reference: str (required) - Booking reference to pay for
        - amount: str/float (optional) - Amount to charge, defaults to booking balance
        - currency: str (optional) - 'USD' or 'ZWG', defaults to 'USD'

    Returns actions to send payment result to customer.
    """
    booking_ref = params.get('booking_reference') or flow_context.get('booking_reference')

    if not booking_ref:
        logger.error(
            "initiate_cbz_ecocash action: missing booking_reference | contact=%s",
            contact.id,
        )
        return [{'type': 'send_text', 'text': '❌ Payment failed: No booking found. Please contact support.'}]

    logger.info(
        "initiate_cbz_ecocash action start | contact=%s booking_ref=%s amount=%s currency=%s",
        contact.id, booking_ref, params.get('amount'), params.get('currency'),
    )

    # Get booking
    try:
        booking = Booking.objects.get(booking_reference=booking_ref)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_ref} not found for CBZ payment")
        return [{'type': 'send_text', 'text': f'❌ Booking {booking_ref} not found. Please verify your reference.'}]

    # Determine amount
    amount_str = params.get('amount')
    if amount_str:
        try:
            amount = Decimal(str(amount_str))
        except (InvalidOperation, ValueError, TypeError):
            amount = booking.total_amount - booking.amount_paid
    else:
        amount = booking.total_amount - booking.amount_paid

    if amount <= 0:
        return [{'type': 'send_text', 'text': f'✅ Booking {booking_ref} is already paid in full!'}]

    currency = params.get('currency', 'USD')
    payment_phone = params.get('msisdn') or flow_context.get('payment_phone', contact.whatsapp_id)

    # Send "processing" message first
    processing_msg = (
        f"💳 *Processing EcoCash Payment*\n\n"
        f"Booking: {booking.booking_reference}\n"
        f"Amount: {currency} {amount}\n\n"
        f"📱 Please check your phone for an EcoCash prompt.\n"
        f"Enter your EcoCash PIN to complete the payment."
    )

    # Initiate the payment (this triggers the STK Push)
    handler = get_cbz_payment_handler()
    try:
        result = handler.initiate_ecocash_payment(
            contact=contact,
            booking=booking,
            amount=amount,
            currency=currency,
            msisdn=payment_phone,
        )
    except Exception as exc:
        logger.error(
            "initiate_cbz_ecocash action exception | contact=%s booking_ref=%s error=%s",
            contact.id, booking_ref, exc, exc_info=True,
        )
        return [{'type': 'send_text', 'text': f'❌ Payment service error: {str(exc)}\nPlease try again or contact support.'}]

    if result['success']:
        auth_code = result.get('authorisation_code', 'N/A')
        ref = result.get('reference', 'N/A')

        logger.info(
            "initiate_cbz_ecocash action SUCCESS | contact=%s booking_ref=%s ref=%s auth=%s",
            contact.id, booking_ref, ref, auth_code,
        )

        # Set success flag for flow transitions
        flow_context['cbz_payment_success'] = True
        flow_context['cbz_payment_reference'] = ref

        success_msg = (
            f"✅ *Payment Successful!*\n\n"
            f"Booking: {booking.booking_reference}\n"
            f"Amount: {currency} {amount}\n"
            f"Reference: {ref}\n"
            f"Status: {booking.get_payment_status_display()}\n\n"
            f"Thank you for your payment! 🎉"
        )

        return [
            {'type': 'send_text', 'text': processing_msg},
            {'type': 'send_text', 'text': success_msg},
        ]
    else:
        error_msg = result.get('message', 'Payment failed')
        result_code = result.get('result_code', '')

        logger.warning(
            "initiate_cbz_ecocash action FAILED | contact=%s booking_ref=%s code=%s msg=%s",
            contact.id, booking_ref, result_code, error_msg,
        )

        fail_msg = (
            f"❌ *Payment Failed*\n\n"
            f"{error_msg}\n"
        )
        if result_code:
            fail_msg += f"Error Code: {result_code}\n"
        fail_msg += "\nPlease try again or choose another payment method."

        return [
            {'type': 'send_text', 'text': processing_msg},
            {'type': 'send_text', 'text': fail_msg},
        ]


def check_cbz_payment_status_action(
    contact: Contact, flow_context: dict, params: dict
) -> List[Dict[str, Any]]:
    """
    Flow action to check the status of a CBZ/iVeri payment.

    Params expected:
        - reference: str - Merchant reference to check

    Sets flow_context['cbz_payment_status'] with the result.
    """
    reference = params.get('reference') or flow_context.get('cbz_payment_reference')

    if not reference:
        return [{'type': 'send_text', 'text': '❌ No payment reference found to check.'}]

    handler = get_cbz_payment_handler()
    result = handler.check_payment_status(reference)

    if result.get('is_approved'):
        flow_context['cbz_payment_status'] = 'approved'
        return [{'type': 'send_text', 'text': f'✅ Payment {reference} has been approved!'}]
    else:
        status = result.get('data', {}).get('status', 'Unknown')
        flow_context['cbz_payment_status'] = status.lower()
        return [{'type': 'send_text', 'text': f'⏳ Payment {reference} status: {status}'}]


def cancel_cbz_payment_action(
    contact: Contact, flow_context: dict, params: dict
) -> List[Dict[str, Any]]:
    """Flow action to cancel pending CBZ payment."""
    handler = get_cbz_payment_handler()
    handler.cancel_payment(contact)

    flow_context.pop('cbz_payment_reference', None)
    flow_context.pop('cbz_payment_success', None)

    return [{'type': 'send_text', 'text': '❌ Payment cancelled. You can initiate a new payment anytime.'}]


def register_cbz_payment_actions():
    """Register CBZ/iVeri payment actions with the flow action registry."""
    from flows.services import flow_action_registry

    flow_action_registry.register('initiate_cbz_ecocash_payment', initiate_cbz_ecocash_payment_action)
    flow_action_registry.register('check_cbz_payment_status', check_cbz_payment_status_action)
    flow_action_registry.register('cancel_cbz_payment', cancel_cbz_payment_action)

    logger.info("Registered CBZ/iVeri payment flow actions")
