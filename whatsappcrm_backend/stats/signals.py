# stats/signals.py
from django.db import transaction  # Import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
import logging

from conversations.models import Contact, Message
from flows.models import Flow
from customer_data.models import Order
from .tasks import (
    update_dashboard_stats,
    broadcast_activity_log,
    broadcast_human_intervention_notification,
    check_handover_timeout
)

logger = logging.getLogger(__name__)

# A debounce delay in seconds to prevent flooding the system with stat updates.
# During a burst of messages, this will trigger one update after the burst.
DEBOUNCE_DELAY = 10


@receiver(post_save, sender=Message)
def on_new_message(sender, instance, created, **kwargs):
    """
    When a new message is created, schedule a debounced task to update all dashboard stats.
    """
    if created:
        logger.debug(f"New message {instance.id}: Scheduling dashboard stats update.")
        update_dashboard_stats.apply_async(countdown=DEBOUNCE_DELAY)


@receiver(post_save, sender=Contact)
def on_contact_change(sender, instance, created, **kwargs):
    """
    When a contact is created or updated, trigger relevant dashboard updates.
    """
    logger.debug(f"Contact changed {instance.id}, created={created}: Scheduling updates.")

    # --- Schedule a full stats update ---
    update_dashboard_stats.apply_async(countdown=DEBOUNCE_DELAY)

    # --- Handle specific real-time events ---
    if created:
        activity_payload = {
            "id": f"contact_new_{instance.id}",
            "text": f"New contact: {instance.name or instance.whatsapp_id}",
            "timestamp": instance.first_seen.isoformat(),
            "iconName": "FiUsers",
            "iconColor": "text-emerald-500"
        }
        broadcast_activity_log.delay(activity_payload)

    # Check for human intervention flag changes
    update_fields = kwargs.get('update_fields') or set()
    if instance.needs_human_intervention and ('needs_human_intervention' in update_fields or created):
        logger.info(f"Human intervention needed for contact {instance.id}. Broadcasting notification.")

        # --- UI Notification (existing) ---
        notification_payload = {
            "contact_id": instance.id,
            "name": instance.name or instance.whatsapp_id,
            "message": f"Contact '{instance.name or instance.whatsapp_id}' requires human assistance."
        }
        broadcast_human_intervention_notification.delay(notification_payload)

        # --- WhatsApp Notification (NEW) ---
        from notifications.services import queue_notifications_to_users
        queue_notifications_to_users(
            template_name='human_handover_flow',
            group_names=["Technical Admin"],
            related_contact=instance
        )

        # --- NEW: Schedule the timeout check task ---
        logger.info(f"Scheduling handover timeout check for contact {instance.id} in 60 seconds.")
        check_handover_timeout.apply_async(args=[instance.id], countdown=60)


@receiver(post_save, sender=Flow)
def on_flow_change(sender, instance, created, **kwargs):
    """When a flow is updated, send an activity log entry."""
    if not created:
        logger.debug(f"Flow updated {instance.id}: Broadcasting activity log.")
        activity_payload = {
            "id": f"flow_update_{instance.id}_{instance.updated_at.timestamp()}",
            "text": f"Flow '{instance.name}' was updated.",
            "timestamp": instance.updated_at.isoformat(),
            "iconName": "FiZap",
            "iconColor": "text-purple-500"
        }
        broadcast_activity_log.delay(activity_payload)


@receiver(post_save, sender=Order)
def on_order_change(sender, instance, created, **kwargs):
    """
    When an order is created or its stage changes, update dashboard stats
    and, if created, schedule a notification to be sent AFTER the transaction commits.
    """
    logger.debug(f"Order changed {instance.pk}, created={created}: Scheduling updates.")
    update_dashboard_stats.apply_async(countdown=DEBOUNCE_DELAY)

    if created:
        # --- MODIFIED: Only send generic notification if the source is NOT an email import ---
        # The email import task now sends its own, more descriptive notification.
        if instance.source != Order.Source.EMAIL_IMPORT and \
           instance.customer and \
           hasattr(instance.customer, 'contact') and \
           instance.customer.contact:
            # Prepare data for the notification template.
            order_data = {
                'id': str(instance.pk),
                'name': instance.name,
                'order_number': instance.order_number,
                'amount': float(instance.amount) if instance.amount else 0.0,
            }
            customer_data = {
                'id': str(instance.customer.pk),
                'full_name': instance.customer.get_full_name(),
                'contact_name': getattr(instance.customer.contact, 'name', 'N/A'),
            }
            # --- FIX: Flatten the context to match the template's expectations ---
            template_context = {
                'order': instance,
                'customer': instance.customer,
            }
            from notifications.services import queue_notifications_to_users
            queue_notifications_to_users(
                template_name='new_order_created',
                group_names=["System Admins", "Sales Team"],
                related_contact=instance.customer.contact,
                template_context=template_context
            )
            logger.info(f"Queued 'new_order_created' notification for Order ID {instance.pk}.")

            # The activity log is a simple Celery task and less likely to fail.
            activity_payload = {
                "id": f"order_new_{instance.pk}",
                "text": f"New Order: '{instance.name}' for {instance.customer}",
                "timestamp": instance.created_at.isoformat(),
                "iconName": "FiShoppingCart",
                "iconColor": "text-blue-500"
            }
            broadcast_activity_log.delay(activity_payload)

        else:
            # Handle placeholder orders
            activity_payload = {
                "id": f"order_new_{instance.pk}",
                "text": f"New Placeholder Order: '{instance.name or instance.order_number}' created.",
                "timestamp": instance.created_at.isoformat(),
                "iconName": "FiShoppingCart",
                "iconColor": "text-gray-500"
            }
            broadcast_activity_log.delay(activity_payload)
            logger.info(f"Logged creation of placeholder order ID {instance.pk} (no customer attached).")