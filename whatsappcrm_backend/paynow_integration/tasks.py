# paynow_integration/tasks.py
import logging
from typing import Optional
from celery import shared_task
import random
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from .services import PaynowService
from meta_integration.utils import send_whatsapp_message, create_text_message_data
from customer_data.models import Payment, Order

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def _fail_payment_in_db(payment_obj: Payment, reason: str) -> Optional[Payment]:
    """
    Internal helper to mark a Payment as FAILED in the database.
    This is NOT a Celery task. It returns the failed payment on success, or None.
    """
    log_prefix = f"[DB Fail Helper - Ref: {payment_obj.id}]"
    logger.warning(f"{log_prefix} Attempting to fail payment in DB. Reason: {reason}")

    payment_to_fail = None
    try:
        with transaction.atomic():
            # Atomically fetch and lock the payment ONLY if it's still PENDING.
            payment_to_fail = Payment.objects.select_for_update().get(
                pk=payment_obj.pk,
                status='pending'
            )
            
            payment_to_fail.status = 'failed'
            payment_to_fail.notes = (payment_to_fail.notes or "") + f"\nFailure reason: {reason[:255]}"
            payment_to_fail.save(update_fields=['status', 'notes', 'updated_at'])
            logger.info(f"{log_prefix} Successfully marked payment as FAILED in the database.")
            
    except Payment.DoesNotExist:
        # This is not an error. It means the payment was already processed.
        logger.info(
            f"{log_prefix} Payment was not in PENDING state "
            "when attempting to fail. It was likely already processed. No action taken."
        )
        return None

    return payment_to_fail

def _fail_payment_and_notify_user(payment_obj: Payment, reason: str):
    """
    Marks a payment as failed in the DB and sends a notification to the user.
    """
    log_prefix = f"[Fail & Notify - Ref: {payment_obj.id}]"
    failed_payment = _fail_payment_in_db(payment_obj, reason)
    
    if failed_payment and failed_payment.contact:
        # If the payment was successfully marked as failed, notify the user.
        send_payment_failure_notification_task.delay(str(failed_payment.id))
    elif not failed_payment:
        logger.info(f"{log_prefix} Payment was not failed in DB (likely already processed), so no notification will be sent.")
    elif not payment_obj.contact:
        logger.warning(f"{log_prefix} Payment was failed in DB, but no contact is associated to send notification.")

# --- Celery Tasks ---

@shared_task(name="paynow_integration.send_payment_failure_notification_task")
def send_payment_failure_notification_task(payment_id: str):
    """
    Sends a WhatsApp message to the user notifying them of a failed payment.
    """
    log_prefix = f"[Failure Notif Task - Ref: {payment_id}]"
    logger.info(f"{log_prefix} Preparing to send failure notification.")
    try:
        # Eager load related objects to avoid extra queries
        payment = Payment.objects.select_related('contact', 'member').get(id=payment_id)
        contact_to_notify = payment.contact
        
        if not contact_to_notify:
            logger.error(f"{log_prefix} Could not find contact associated with payment to send failure notification.")
            return

        # Personalize the greeting
        full_name = payment.member.get_full_name() if payment.member and payment.member.get_full_name() else payment.contact.name
        recipient_name = full_name or 'church member'
        admin_contact_number = settings.ADMIN_WHATSAPP_NUMBER
        contact_info = f"You can reach us on WhatsApp at: wa.me/{admin_contact_number.replace('+', '')}" if admin_contact_number else "Please visit the church office for assistance."

        failure_message = (
            f"Greetings {recipient_name},\n\n"
            f"We encountered an issue while processing your contribution of *{payment.currency} {payment.amount:.2f}*.\n\n"
            "Please don't worry, no funds have been deducted for this attempt. If you'd like to try again or need help, our team is here to assist.\n\n"
            f"{contact_info}\n\n"
            "\"The Lord is my strength and my shield; in him my heart trusts, and I am helped.\" - Psalm 28:7\n\n"
            "Blessings,\n"
            "The Church Accounts Team"
        )
        message_data = create_text_message_data(text_body=failure_message)
        send_whatsapp_message(to_phone_number=contact_to_notify.whatsapp_id, message_type='text', data=message_data)
        logger.info(f"{log_prefix} Successfully sent failure notification to user {contact_to_notify.whatsapp_id}.")
    except Payment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find payment to send failure notification.")
    except Exception as e:
        logger.error(f"{log_prefix} Error sending failure notification: {e}", exc_info=True)

@shared_task(name="paynow_integration.send_giving_confirmation_whatsapp")
def send_giving_confirmation_whatsapp(payment_id: str):
    """
    Sends a WhatsApp message to the user confirming their successful contribution.
    """
    log_prefix = f"[Giving Confirm Task - Ref: {payment_id}]"
    logger.info(f"{log_prefix} Preparing to send giving confirmation.")
    try:
        # Eager load related objects
        payment = Payment.objects.select_related('contact', 'member').get(id=payment_id, status='completed')
        contact_to_notify = payment.contact

        if not contact_to_notify:
            logger.error(f"{log_prefix} Could not find contact associated with payment to send confirmation.")
            return

        # Personalize the greeting
        full_name = payment.member.get_full_name() if payment.member and payment.member.get_full_name() else payment.contact.name
        recipient_name = full_name or 'church member'

        confirmation_message = (
            f"Dear {recipient_name},\n\n"
            f"Praise God! We confirm with thanks the receipt of your contribution of *{payment.currency} {payment.amount:.2f}*.\n\n"
            "Your faithfulness and generosity are a blessing to the ministry. We pray for God's abundant blessings upon you and your family.\n\n"
            "\"Each of you should give what you have decided in your heart to give, not reluctantly or under compulsion, for God loves a cheerful giver.\" - 2 Corinthians 9:7\n\n"
            "In His Grace,\n"
            "The Church Accounts Team"
        )
        message_data = create_text_message_data(text_body=confirmation_message)
        send_whatsapp_message(to_phone_number=contact_to_notify.whatsapp_id, message_type='text', data=message_data)
        logger.info(f"{log_prefix} Successfully sent giving confirmation to user {contact_to_notify.whatsapp_id}.")
    except Payment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find completed payment to send confirmation.")
    except Exception as e:
        logger.error(f"{log_prefix} Error sending giving confirmation: {e}", exc_info=True)

@shared_task(name="paynow_integration.poll_paynow_transaction_status", bind=True, max_retries=10, default_retry_delay=120)
def poll_paynow_transaction_status(self, payment_id: str):
    """
    Polls Paynow to get the transaction status and updates the Payment record accordingly.
    """
    log_prefix = f"[Poll Task - Ref: {payment_id}]"
    logger.info(f"{log_prefix} Polling Paynow status. Attempt {self.request.retries + 1}/{self.max_retries + 1}.")
    try:
        with transaction.atomic():
            # Lock the Payment row to prevent race conditions from IPNs or other tasks.
            pending_payment = Payment.objects.select_for_update().get(id=payment_id, status='pending')
            
            # FIX: The PaynowService requires the IPN callback URL for initialization.
            try:
                ipn_url = reverse('customer_data_api:paynow-ipn-webhook')
                paynow_service = PaynowService(ipn_callback_url=ipn_url)
            except Exception as e:
                logger.error(f"{log_prefix} Failed to initialize PaynowService. Error: {e}", exc_info=True)
                _fail_payment_and_notify_user(pending_payment, "Could not initialize payment service for polling.")
                return # Stop execution

            poll_url = pending_payment.external_data.get('poll_url')
            if not poll_url:
                logger.error(f"{log_prefix} Poll URL not found. Failing payment.")
                _fail_payment_and_notify_user(pending_payment, "Could not poll status: Poll URL missing.")
                return # Stop execution

            logger.debug(f"{log_prefix} Checking poll URL: {poll_url}")
            status_response = paynow_service.check_transaction_status(poll_url)
            
            if status_response['success']:
                paynow_status = status_response.get('status', 'unknown').lower()
                logger.info(f"{log_prefix} Paynow status received: '{paynow_status}'.")

                if paynow_status == 'paid':
                    pending_payment.status = 'completed'
                    pending_payment.notes = (pending_payment.notes or "") + f"\nPaynow Ref: {pending_payment.transaction_reference}"
                    pending_payment.save(update_fields=['status', 'notes', 'updated_at'])
                    
                    # --- NEW: Update associated order status ---
                    if pending_payment.order:
                        pending_payment.order.payment_status = Order.PaymentStatus.PAID
                        pending_payment.order.save(update_fields=['payment_status', 'updated_at'])
                        logger.info(f"{log_prefix} Updated order {pending_payment.order.id} payment_status to PAID.")
                    
                    logger.info(f"{log_prefix} Successfully processed payment {pending_payment.id}. Amount: {pending_payment.amount}.")
                    
                    # Send confirmation to user
                    send_giving_confirmation_whatsapp.delay(payment_id=str(pending_payment.id))
                    return # Task is complete

                elif paynow_status in ['cancelled', 'failed', 'disputed']:
                    reason = f"Paynow transaction status was '{paynow_status}'."
                    logger.warning(f"{log_prefix} Failing payment due to status: '{paynow_status}'.")
                    _fail_payment_and_notify_user(pending_payment, reason)
                    return # Task is complete

                else: # 'pending', 'created', 'sent', etc.
                    # Implement exponential backoff with jitter to reduce load on Paynow's servers.
                    retry_delay = 60 * (2 ** self.request.retries)
                    retry_delay_with_jitter = retry_delay + random.randint(0, 15)
                    logger.info(f"{log_prefix} Transaction is still pending with status '{paynow_status}'. Retrying in {retry_delay_with_jitter} seconds.")
                    self.retry(exc=Exception(f"Transaction is still pending. Current status: {paynow_status}"), countdown=retry_delay_with_jitter)
            else:
                error_msg = status_response.get('message', 'Unknown API error')
                logger.error(f"{log_prefix} Failed to get Paynow status: {error_msg}. Retrying task.")
                self.retry(exc=Exception(f"Failed to get Paynow status: {error_msg}"))

    except Payment.DoesNotExist:
        logger.info(f"{log_prefix} Payment not found or not PENDING. It was likely processed by another task. Stopping poll.")
    except Exception as e:
        logger.error(f"{log_prefix} Unhandled error during polling: {e}", exc_info=True)
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"{log_prefix} Max retries exceeded. Attempting to fail payment.")
            try:
                payment_to_fail = Payment.objects.get(id=payment_id, status='pending')
                _fail_payment_and_notify_user(payment_to_fail, f"Polling failed after max retries: {str(e)[:100]}")
            except Payment.DoesNotExist:
                logger.warning(f"{log_prefix} Could not find payment to fail after max retries (it might have been processed or failed already).")
            except Exception as final_fail_exc:
                logger.critical(f"{log_prefix} Could not fail payment after max retries: {final_fail_exc}")

@shared_task(name="paynow_integration.process_paynow_ipn_task")
def process_paynow_ipn_task(ipn_data: dict):
    """
    Processes a Paynow IPN message. It verifies the IPN hash, then updates
    the payment status directly. This is the primary confirmation method.
    """
    reference = ipn_data.get('reference')
    if not reference:
        logger.error("[IPN Task] Received IPN data without a reference. Cannot process.")
        return

    log_prefix = f"[IPN Task - Ref: {reference}]"
    logger.info(f"{log_prefix} Starting to process IPN data: {ipn_data}")

    # The service needs a URL for init, even if we're just verifying a hash.
    try:
        ipn_url = reverse('customer_data_api:paynow-ipn-webhook')
        paynow_service = PaynowService(ipn_callback_url=ipn_url)
    except Exception as e:
        logger.error(f"{log_prefix} Failed to initialize PaynowService for IPN processing. Error: {e}", exc_info=True)
        return # Cannot proceed without the service

    if not paynow_service.verify_ipn_hash(ipn_data):
        logger.error(f"{log_prefix} IPN hash verification failed. Discarding message.")
        return

    logger.info(f"{log_prefix} IPN hash verified successfully.")
    paynow_status = ipn_data.get('status', 'unknown').lower()

    try:
        with transaction.atomic():
            # Lock the payment record to prevent race conditions with polling tasks.
            payment_to_update = Payment.objects.select_for_update().get(pk=reference, status='pending')

            if paynow_status == 'paid':
                payment_to_update.status = 'completed'
                payment_to_update.transaction_reference = ipn_data.get('paynowreference')
                payment_to_update.notes = (payment_to_update.notes or "") + f"\nConfirmed via IPN. Paynow Ref: {payment_to_update.transaction_reference}"
                payment_to_update.save(update_fields=['status', 'transaction_reference', 'notes', 'updated_at'])

                # --- NEW: Update associated order status ---
                if payment_to_update.order:
                    payment_to_update.order.payment_status = Order.PaymentStatus.PAID
                    payment_to_update.order.save(update_fields=['payment_status', 'updated_at'])
                    logger.info(f"{log_prefix} Updated order {payment_to_update.order.id} payment_status to PAID.")
                
                logger.info(f"{log_prefix} Successfully processed payment. Amount: {payment_to_update.amount}.")
                send_giving_confirmation_whatsapp.delay(payment_id=str(payment_to_update.id))
            
            elif paynow_status in ['cancelled', 'failed', 'disputed']:
                reason = f"Paynow IPN reported status: '{paynow_status}'."
                logger.warning(f"{log_prefix} Failing payment due to IPN status: '{paynow_status}'.")
                _fail_payment_and_notify_user(payment_to_update, reason)
            
            else:
                logger.info(f"{log_prefix} Received non-final IPN status '{paynow_status}'. No action taken, polling will handle it.")

    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred while processing the IPN: {e}", exc_info=True)
