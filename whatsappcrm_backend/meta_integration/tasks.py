# whatsappcrm_backend/meta_integration/tasks.py

import logging
import tempfile
import os
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .utils import send_whatsapp_message, send_read_receipt_api, download_whatsapp_media
from .models import MetaAppConfig
from .signals import message_send_failed
from conversations.models import Message, Contact # To update message status

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=10, default_retry_delay=3) # bind=True gives access to self, retry settings
def send_whatsapp_message_task(self, outgoing_message_id: int, active_config_id: int):
    """
    Celery task to send a WhatsApp message asynchronously.
    Updates the Message object's status based on the outcome.

    Args:
        outgoing_message_id (int): The ID of the outgoing Message object to send.
        active_config_id (int): The ID of the active MetaAppConfig to use for sending.
    """
    try:
        outgoing_msg = Message.objects.select_related('contact').get(pk=outgoing_message_id)
        active_config = MetaAppConfig.objects.get(pk=active_config_id)
    except Message.DoesNotExist:
        logger.error(f"send_whatsapp_message_task: Message with ID {outgoing_message_id} not found. Task cannot proceed.")
        return # Cannot retry if message doesn't exist
    except MetaAppConfig.DoesNotExist:
        logger.error(f"send_whatsapp_message_task: MetaAppConfig with ID {active_config_id} not found. Task cannot proceed.")
        # Update message status to failed if config is missing
        if 'outgoing_msg' in locals():
            outgoing_msg.status = 'failed'
            outgoing_msg.error_details = {'error': f'MetaAppConfig ID {active_config_id} not found for sending.'}
            outgoing_msg.status_timestamp = timezone.now()
            outgoing_msg.save(update_fields=['status', 'error_details', 'status_timestamp'])
        return

    if outgoing_msg.direction != 'out':
        logger.warning(f"send_whatsapp_message_task: Message ID {outgoing_message_id} is not an outgoing message. Skipping.")
        return

    # Avoid resending if already sent successfully or in a final failed state without retries
    if outgoing_msg.wamid and outgoing_msg.status == 'sent':
        logger.info(f"send_whatsapp_message_task: Message ID {outgoing_message_id} (WAMID: {outgoing_msg.wamid}) already marked as sent. Skipping.")
        return
    if outgoing_msg.status == 'failed' and self.request.retries >= self.max_retries:
         logger.warning(f"send_whatsapp_message_task: Message ID {outgoing_message_id} already failed and max retries reached. Skipping.")
         return

    # To ensure sequential delivery, check for preceding messages that are either:
    # 1. Still pending dispatch (these should always be sent first).
    # 2. Were sent recently but not yet confirmed as delivered. We'll wait for a short period
    #    (e.g., 2 minutes) for the delivery receipt. This prevents sending a new message
    #    before the previous one is confirmed delivered by WhatsApp's servers.
    stale_threshold = timezone.now() - timedelta(seconds=20)

    # NEW: Add a threshold for stale pending messages to prevent deadlocks.
    # If a message has been pending for more than 5 minutes, assume it's stuck and proceed.
    stale_pending_threshold = timezone.now() - timedelta(minutes=1)

    # Find the specific message causing the halt for better logging
    # A message is halting if it's a preceding message for the same contact AND
    # 1. It is still pending dispatch (must wait for it to be sent).
    # OR
    # 2. It was sent very recently, and we are waiting for a delivery receipt to ensure order.
    halting_message = Message.objects.filter(
        Q(contact=outgoing_msg.contact),
        Q(direction='out'),
        Q(id__lt=outgoing_msg.id),
        (
            Q(status='pending_dispatch', timestamp__gte=stale_pending_threshold) | # Only wait for RECENTLY created pending messages.
            Q(status='sent', status_timestamp__gte=stale_threshold) # Wait for recently sent messages to be delivered.
        )
    ).order_by('-id').first() # Get the most recent one for logging

    if halting_message:
        logger.warning(
            f"send_whatsapp_message_task: Halting message ID {outgoing_message_id} for contact "
            f"{outgoing_msg.contact.whatsapp_id}. Waiting for preceding message ID {halting_message.id} "
            f"(Status: {halting_message.status}, Status Time: {halting_message.status_timestamp}, "
            f"Created: {halting_message.timestamp}). Retrying."
        )
        try:
            raise self.retry() # Uses the task's default_retry_delay
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for message {outgoing_message_id} while waiting. Marking as failed.")
            outgoing_msg.status = 'failed'
            outgoing_msg.error_details = {'error': 'Max retries exceeded while waiting for preceding message.'}
            outgoing_msg.status_timestamp = timezone.now()
            outgoing_msg.save(update_fields=['status', 'error_details', 'status_timestamp'])
            message_send_failed.send(sender=self.__class__, message_instance=outgoing_msg)
            return

    logger.info(f"Task send_whatsapp_message_task started for Message ID: {outgoing_message_id}, Contact: {outgoing_msg.contact.whatsapp_id}")

    try:
        # content_payload should contain the 'data' part for send_whatsapp_message
        # and message_type should be the Meta API message type
        if not isinstance(outgoing_msg.content_payload, dict):
            raise ValueError("Message content_payload is not a valid dictionary for sending.")

        api_response = send_whatsapp_message(
            to_phone_number=outgoing_msg.contact.whatsapp_id,
            message_type=outgoing_msg.message_type, # This should be 'text', 'template', 'interactive'
            data=outgoing_msg.content_payload, # This is the actual data for the type
            config=active_config
        )

        if api_response and api_response.get('messages') and api_response['messages'][0].get('id'):
            outgoing_msg.wamid = api_response['messages'][0]['id']
            outgoing_msg.status = 'sent' # Successfully handed off to Meta
            outgoing_msg.error_details = None # Clear previous errors if any
            logger.info(f"Message ID {outgoing_message_id} sent successfully via Meta API. WAMID: {outgoing_msg.wamid}")
        else:
            # Handle failure from Meta API
            error_info = api_response or {'error': 'Meta API call failed or returned unexpected response.'}
            logger.error(f"Failed to send Message ID {outgoing_message_id} via Meta API. Response: {error_info}")
            outgoing_msg.status = 'failed'
            outgoing_msg.error_details = error_info
            raise ValueError("Meta API call failed or returned unexpected response.")

    except Exception as e:
        logger.error(f"Exception in send_whatsapp_message_task for Message ID {outgoing_message_id}: {e}", exc_info=True)
        outgoing_msg.status = 'failed'
        outgoing_msg.error_details = {'error': str(e), 'type': type(e).__name__}
        try:
            # Retry the task if it's a network issue or a temporary problem
            # Celery will automatically retry based on max_retries and default_retry_delay.
            raise self.retry(exc=e) # Re-raise to trigger Celery's retry mechanism
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for sending Message ID {outgoing_message_id}.")
            # This is a permanent failure. Save the final state and send the notification signal.
            outgoing_msg.status_timestamp = timezone.now()
            outgoing_msg.save(update_fields=['status', 'error_details', 'status_timestamp'])
            message_send_failed.send(sender=self.__class__, message_instance=outgoing_msg)
            return # Exit after handling permanent failure

    # This block is now only reached on success or during retries (before an exception is raised).
    outgoing_msg.status_timestamp = timezone.now()
    outgoing_msg.save(update_fields=['wamid', 'status', 'error_details', 'status_timestamp'])


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_read_receipt_task(self, wamid: str, config_id: int, show_typing_indicator: bool = False):
    """
    Celery task to send a read receipt for a given message ID.
    """
    logger.info(f"Task send_read_receipt_task started for WAMID: {wamid} (Typing: {show_typing_indicator})")
    try:
        active_config = MetaAppConfig.objects.get(pk=config_id)
    except MetaAppConfig.DoesNotExist:
        logger.error(f"send_read_receipt_task: MetaAppConfig with ID {config_id} not found. Task cannot proceed.")
        return  # Cannot retry if config is missing

    try:
        api_response = send_read_receipt_api(wamid=wamid, config=active_config, show_typing_indicator=show_typing_indicator)
        # The read receipt API returns {"success": true}. If the response is None or 'success' is not true, it's a failure.
        if not api_response or not api_response.get('success'):
            # The utility function has already logged the specific error. We raise an exception to trigger a retry.
            raise ValueError(f"API call to send read receipt failed for WAMID {wamid}. Response: {api_response}")

    except Exception as e:
        logger.warning(f"Exception in send_read_receipt_task for WAMID {wamid}, will retry. Error: {e}")
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for sending read receipt for WAMID {wamid}.")


@shared_task(name="meta_integration.download_whatsapp_media_task")
def download_whatsapp_media_task(media_id: str, config_id: int) -> str | None:
    """
    Downloads media from WhatsApp and saves it to a temporary file.
    Returns the path to the temporary file, or None on failure.
    """
    log_prefix = f"[Media Download Task - Media ID: {media_id}]"
    try:
        config = MetaAppConfig.objects.get(pk=config_id)
        # The download_whatsapp_media function returns a tuple or None.
        download_result = download_whatsapp_media(media_id, config)

        if download_result is None:
            logger.error(f"{log_prefix} download_whatsapp_media utility returned None. Download failed.")
            return None
        media_content, mime_type = download_result

        if media_content and mime_type:
            # Determine a file extension from the mime type
            suffix = f".{mime_type.split('/')[-1].split(';')[0]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(media_content)
                logger.info(f"{log_prefix} Media saved to temporary file: {temp_file.name}")
                return temp_file.name
        else:
            logger.error(f"{log_prefix} Failed to download media content from WhatsApp.")
            return None
    except MetaAppConfig.DoesNotExist:
        logger.error(f"{log_prefix} MetaAppConfig with ID {config_id} not found.") # type: ignore
        return None
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during media download: {e}", exc_info=True)
        return None
