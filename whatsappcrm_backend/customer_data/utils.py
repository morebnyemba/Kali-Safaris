# whatsappcrm_backend/customer_data/utils.py

import logging
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone

from conversations.models import Contact
from .models import MemberProfile, Payment, PaymentHistory, PrayerRequest
from .tasks import process_proof_of_payment_image

logger = logging.getLogger(__name__)

def record_payment(
    contact: Contact,
    amount_str: str,
    payment_type: str,
    currency: str = 'USD',
    payment_method: str = 'whatsapp_flow',
    transaction_ref: str = None,
    notes: str = None,
    proof_of_payment_wamid: str = None,
    status: str = None
) -> tuple[Payment | None, dict | None]:
    """
    Creates a Payment record for a contact and an associated history entry.

    Args:
        contact: The Contact object making the payment.
        amount_str: The amount of the payment as a string.
        payment_type: The type of payment (e.g., 'tithe', 'offering').
        currency: The currency code (e.g., 'USD').
        payment_method: The method of payment.
        transaction_ref: An optional external transaction reference.
        notes: Optional internal notes for the payment.
        proof_of_payment_wamid: Optional WAMID of an uploaded proof of payment image.
        status: Optional status to set for the payment. If not provided, it's inferred.

    Returns:
        A tuple of (Payment object, confirmation_action_dict), or (None, None) if an error occurred.
    """
    logger.info(
        f"Attempting to record payment for contact {contact.id} ({contact.whatsapp_id}). "
        f"Amount: '{amount_str}', Type: '{payment_type}', Method: '{payment_method}', "
        f"Status: '{status}', WAMID: '{proof_of_payment_wamid}'"
    )
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            logger.warning(f"Attempted to record a non-positive payment amount ({amount}) for contact {contact.id} ({contact.whatsapp_id}). Aborting.")
            return None, None
    except (InvalidOperation, TypeError):
        logger.error(f"Invalid amount '{amount_str}' provided for payment for contact {contact.id} ({contact.whatsapp_id}). Cannot convert to Decimal.")
        return None, None

    valid_payment_types = [choice[0] for choice in Payment.PAYMENT_TYPE_CHOICES]
    if payment_type not in valid_payment_types:
        logger.warning(f"Invalid payment_type '{payment_type}' for contact {contact.id} ({contact.whatsapp_id}). Defaulting to 'other'.")
        payment_type = 'other'

    try:
        with transaction.atomic():
            member_profile = MemberProfile.objects.filter(contact=contact).first()

            # Determine status and confirmation message based on payment method
            payment_status = status
            is_manual_payment = payment_method == 'manual_payment'
            if not payment_status:
                if proof_of_payment_wamid:
                    payment_status = 'pending_verification'
                else:
                    payment_status = 'pending' if is_manual_payment else 'completed'

            logger.debug(
                f"Creating Payment object for contact {contact.id} with: "
                f"Amount={amount}, Currency={currency}, Type={payment_type}, "
                f"Method={payment_method}, Status={payment_status}"
            )
            payment = Payment.objects.create(
                contact=contact, member=member_profile, amount=amount, currency=currency,
                payment_type=payment_type, payment_method=payment_method,
                status=payment_status, transaction_reference=transaction_ref, notes=notes
            )
            history_note = f"Payment recorded via flow for contact {contact.whatsapp_id}."
            if payment_status == 'pending_verification':
                history_note = f"Manual payment with proof submitted via flow for contact {contact.whatsapp_id}. Awaiting verification."
            elif is_manual_payment:
                history_note = f"Manual payment initiated via flow for contact {contact.whatsapp_id}. Awaiting confirmation."

            PaymentHistory.objects.create(payment=payment, status=payment_status, notes=history_note)
            
            # If proof of payment is provided, trigger the background download task
            if proof_of_payment_wamid and payment:
                # Use transaction.on_commit to ensure the task runs only after the payment record is committed to the DB.
                # This prevents a race condition where the Celery worker picks up the task before the transaction is complete.
                transaction.on_commit(
                    lambda: process_proof_of_payment_image.delay(payment_id=str(payment.id), wamid=proof_of_payment_wamid)
                )
                logger.info(f"Scheduled background task to download proof of payment for payment {payment.id}.")

            # Create confirmation message action
            if payment_status == 'pending_verification':
                confirmation_message_text = (
                    f"Thank you! We have received your proof of payment for *{amount} {currency}* "
                    f"and will verify it shortly. God bless you! 🙏"
                )
            elif is_manual_payment:
                ref_text = f" using reference: *{transaction_ref}*" if transaction_ref else ""
                confirmation_message_text = (
                    f"Thank you for your pledge! 🙏\n\n"
                    f"We have recorded your pending contribution of *{amount} {currency}* for *{payment.get_payment_type_display()}*{ref_text}.\n\n"
                    f"Our bookkeeper will confirm your payment shortly. You will receive a final confirmation once it's processed."
                )
            else:
                confirmation_message_text = (
                    f"Thank you for your contribution! 🙏\n\n"
                    f"We have successfully recorded your payment of *{amount} {currency}* for *{payment.get_payment_type_display()}*.\n\n"
                    f"Your transaction ID is: {payment.id}"
                )
            
            confirmation_action = {
                'type': 'send_whatsapp_message',
                'recipient_wa_id': contact.whatsapp_id,
                'message_type': 'text',
                'data': {'body': confirmation_message_text}
            }

            logger.info(f"Successfully recorded payment {payment.id} of {amount} {currency} for contact {contact.id} ({contact.whatsapp_id}). Status: {payment_status}")
            return payment, confirmation_action
    except Exception as e:
        logger.error(f"Failed to record payment for contact {contact.id} ({contact.whatsapp_id}). Error: {e}", exc_info=True)
        return None, None

def record_prayer_request(
    contact: Contact,
    request_text: str,
    category: str,
    is_anonymous: bool,
    submitted_as_member: bool = False
) -> PrayerRequest | None:
    """
    Creates a PrayerRequest record for a contact.

    Args:
        contact: The Contact object submitting the request.
        request_text: The text content of the prayer request.
        category: The category of the prayer request.
        is_anonymous: Boolean indicating if the request is anonymous.
        submitted_as_member: Boolean indicating if the user identified as a member.

    Returns:
        The created PrayerRequest object, or None if an error occurred.
    """
    if not request_text or not request_text.strip():
        logger.warning(f"Attempted to record an empty prayer request for contact {contact.id}. Aborting.")
        return None

    valid_categories = [choice[0] for choice in PrayerRequest.REQUEST_CATEGORY_CHOICES]
    if category not in valid_categories:
        logger.warning(f"Invalid prayer request category '{category}' for contact {contact.id}. Setting to 'other'.")
        category = 'other'

    try:
        with transaction.atomic():
            member_profile = MemberProfile.objects.filter(contact=contact).first()
            
            prayer_request = PrayerRequest.objects.create(
                contact=contact, member=member_profile, request_text=request_text,
                category=category, is_anonymous=is_anonymous,
                submitted_as_member=submitted_as_member, status='submitted'
            )
            logger.info(f"Successfully recorded prayer request {prayer_request.id} for contact {contact.id}.")
            return prayer_request
    except Exception as e:
        logger.error(f"Failed to record prayer request for contact {contact.id}. Error: {e}", exc_info=True)
        return None