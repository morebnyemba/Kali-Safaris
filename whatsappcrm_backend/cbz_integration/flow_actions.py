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

    # Get booking (scoped to customer to handle multiple bookings with same reference)
    try:
        booking = Booking.objects.get(booking_reference=booking_ref, customer=contact.customer_profile)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_ref} not found for CBZ payment | contact={contact.id}")
        return [{'type': 'send_text', 'text': f'❌ Booking {booking_ref} not found. Please verify your reference.'}]
    except Booking.MultipleObjectsReturned:
        logger.error(f"Multiple bookings found for {booking_ref} and customer {contact.customer_profile.id}")
        return [{'type': 'send_text', 'text': f'❌ Payment system error. Please contact support.'}]

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
        flow_context['cbz_payment_status'] = 'failed'
        flow_context['cbz_payment_error_message'] = f'Payment service error: {str(exc)}'
        return []

    if result['success']:
        ref = result.get('reference', 'N/A')
        status = result.get('status', 'approved')

        flow_context['cbz_payment_reference'] = ref
        flow_context['cbz_payment_status'] = status

        if result.get('is_pending'):
            flow_context.pop('cbz_payment_success', None)
            logger.info(
                "initiate_cbz_ecocash action PENDING | contact=%s booking_ref=%s ref=%s",
                contact.id, booking_ref, ref,
            )
        else:
            logger.info(
                "initiate_cbz_ecocash action SUCCESS | contact=%s booking_ref=%s ref=%s",
                contact.id, booking_ref, ref,
            )
            flow_context['cbz_payment_success'] = True

        flow_context.pop('cbz_payment_error_message', None)
        flow_context.pop('cbz_payment_result_code', None)
        return []
    else:
        error_msg = result.get('message') or 'Payment was not approved.'
        result_code = result.get('result_code', '')

        logger.warning(
            "initiate_cbz_ecocash action FAILED | contact=%s booking_ref=%s code=%s msg=%s",
            contact.id, booking_ref, result_code, error_msg,
        )
        flow_context['cbz_payment_status'] = result.get('status', 'failed')
        flow_context['cbz_payment_error_message'] = error_msg
        flow_context['cbz_payment_result_code'] = result_code
        if result.get('reference'):
            flow_context['cbz_payment_reference'] = result['reference']
        flow_context.pop('cbz_payment_success', None)
        return []


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
    if result.get('is_pending'):
        flow_context['cbz_payment_status'] = 'pending'
        return [{'type': 'send_text', 'text': f'⏳ Payment {reference} is still awaiting confirmation.'}]
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
