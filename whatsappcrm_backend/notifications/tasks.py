import logging
from celery import shared_task
import re
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.conf import settings

from meta_integration.models import MetaAppConfig
from meta_integration.tasks import send_whatsapp_message_task
from conversations.models import Message, Contact
from .models import Notification, NotificationTemplate
from .utils import render_template_string

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def dispatch_notification_task(self, notification_id: int):
    """
    Fetches a Notification object and attempts to send it via its specified channel.
    Updates the notification status based on the outcome.
    """
    try:
        notification = Notification.objects.select_related('recipient', 'recipient__whatsapp_contact').get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"Notification with ID {notification_id} not found. Aborting task.")
        return

    if notification.status != 'pending':
        logger.warning(f"Notification {notification_id} is not in 'pending' state (state is '{notification.status}'). Skipping.")
        return

    recipient = notification.recipient
    if not hasattr(recipient, 'whatsapp_contact') or not recipient.whatsapp_contact:
        error_msg = f"User '{recipient.username}' has no linked WhatsApp contact."
        logger.warning(f"Cannot send notification {notification.id}: {error_msg}")
        notification.status = 'failed'
        notification.error_message = error_msg
        notification.save(update_fields=['status', 'error_message'])
        return

    if notification.channel == 'whatsapp':
        try:
            active_config = MetaAppConfig.objects.get_active_config()
            content_payload = {}

            # --- MODIFICATION: Always use template messages for notifications ---
            # This logic now runs regardless of the 24-hour window status.
            if notification.template_name:
                # --- NEW LOGIC: Window is closed, so we MUST use a pre-approved template. ---
                logger.info(f"Attempting to send notification {notification.id} as a template message.")
                
                if not notification.template_name:
                    error_msg = f"Cannot send notification {notification.id}: 24-hour window is closed and no template_name is set on the notification."
                    logger.error(f"Cannot send notification {notification.id}: {error_msg}")
                    notification.status = 'failed'
                    notification.error_message = error_msg
                    notification.save(update_fields=['status', 'error_message'])
                    return

                message_type = 'template'
                template_context = notification.template_context or {}
                # Create a copy to avoid modifying the stored context
                render_context = template_context.copy()
                render_context['recipient'] = recipient
                
                # --- FIX: Fetch the original template to get the correct variable structure ---
                try:
                    template_model = NotificationTemplate.objects.get(name=notification.template_name)
                    original_template_body = template_model.message_body
                except NotificationTemplate.DoesNotExist:
                    error_msg = f"Cannot send template notification {notification.id}: Template '{notification.template_name}' not found in database."
                    logger.error(error_msg)
                    notification.status = 'failed'
                    notification.error_message = error_msg
                    notification.save(update_fields=['status', 'error_message'])
                    return

                # 2. Find all the Jinja2 variables/expressions from the *original* template content.
                jinja_parts = re.findall(r'(\{%\s*(?:if|for).*?%\}[\s\S]*?\{%\s*end(?:if|for)\s*%\}|\{\{.*?\}\})', original_template_body)
                
                parameters = []
                for idx, part in enumerate(jinja_parts):
                    # 3. Render each individual part to get its final value.
                    rendered_value = render_template_string(part, render_context)
                    parameters.append({"type": "text", "text": str(rendered_value)})
                # --- END FIX ---

                components = []
                if parameters:
                    components.append({"type": "body", "parameters": parameters})

                content_payload = {
                    "name": notification.template_name,
                    "language": {"code": "en_US"},
                    "components": components
                }
                logger.info(f"Dispatching template '{notification.template_name}' with payload: {content_payload}")
            else:
                # This case handles notifications that were queued without a template.
                # They cannot be sent as templates, so we fail them with a clear error.
                error_msg = f"Cannot send notification {notification.id}: No 'template_name' was provided, and all notifications must now use templates."
                logger.error(error_msg)
                notification.status = 'failed'
                notification.error_message = error_msg
                notification.save(update_fields=['status', 'error_message'])
                return

            with transaction.atomic():
                message = Message.objects.create(
                    contact=recipient.whatsapp_contact, app_config=active_config, direction='out',
                    message_type=message_type,
                    content_payload=content_payload,
                    status='pending_dispatch',
                    is_system_notification=True # Flag this as a system notification
                )

                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save(update_fields=['status', 'sent_at'])
                transaction.on_commit(lambda: send_whatsapp_message_task.delay(message.id, active_config.id))
            logger.info(f"Successfully dispatched notification {notification.id} as Message {message.id}.")
        except Exception as e:
            logger.error(f"Failed to dispatch notification {notification.id} for user '{recipient.username}'. Error: {e}", exc_info=True)
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save(update_fields=['status', 'error_message'])
            self.retry(exc=e)

@shared_task
def check_and_send_24h_window_reminders():
    """
    A scheduled task to find admin users whose 24-hour interaction window is about to close and
    send them a reminder to interact with the bot to keep the window open.
    This task is idempotent and will not re-notify a user within a 23-hour period.
    """
    logger.info("Running scheduled task: check_and_send_24h_window_reminders")
    
    window_start = timezone.now() - timedelta(hours=24)
    window_end = timezone.now() - timedelta(hours=23)

    potential_users_to_remind = User.objects.filter(
        groups__name__in=['Technical Admin', 'Pastoral Team'],
        whatsapp_contact__isnull=False,
        whatsapp_contact__last_seen__gte=window_start,
        whatsapp_contact__last_seen__lt=window_end
    ).distinct()

    if not potential_users_to_remind.exists():
        logger.info("No admin users found with expiring 24-hour windows.")
        return "No users to remind."

    from .services import queue_notifications_to_users # Local import to avoid circular dependency issues at module level
    
    user_ids_to_remind = list(potential_users_to_remind.values_list('id', flat=True))
    if user_ids_to_remind:
        queue_notifications_to_users(
            template_name='admin_24h_window_reminder',
            user_ids=user_ids_to_remind
        )
        dispatched_count = len(user_ids_to_remind)
        for user_id in user_ids_to_remind:
            logger.info(f"Queued 24h window reminder for User ID: {user_id}.")
        
    return f"Successfully dispatched {dispatched_count} window expiry reminder(s)."