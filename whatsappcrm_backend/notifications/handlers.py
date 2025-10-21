import logging
from django.dispatch import receiver
from meta_integration.signals import message_send_failed
from .services import queue_notifications_to_users

logger = logging.getLogger(__name__)

@receiver(message_send_failed)
def handle_failed_message_notification(sender, message_instance, **kwargs):
    """
    Listens for the message_send_failed signal and queues a notification
    to the admin team.
    """
    try:
        contact = message_instance.contact
        logger.info(
            f"Signal received: Message send failed for contact '{contact.name}' ({contact.whatsapp_id}). "
            f"Queuing admin notification."
        )

        queue_notifications_to_users(
            template_name='message_send_failure',
            group_names=["Technical Admin"],
            related_contact=contact,
            template_context={'message': message_instance}
        )
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to queue notification for failed message {message_instance.id}. Error: {e}",
            exc_info=True
        )