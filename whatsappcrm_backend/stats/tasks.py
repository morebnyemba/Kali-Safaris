# stats/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from django.utils import timezone
from datetime import timedelta

from . import services
from conversations.models import Contact, Message
from meta_integration.models import MetaAppConfig
from meta_integration.tasks import send_whatsapp_message_task

logger = logging.getLogger(__name__)

def _broadcast_update(update_type, payload):
    """Helper function to send updates to the dashboard group."""
    channel_layer = get_channel_layer()
    if channel_layer:
        logger.debug(f"Broadcasting update: type='{update_type}'")
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'dashboard.update',
                'update_type': update_type,
                'payload': payload
            }
        )
    else:
        logger.warning("Cannot broadcast update: Channel layer not found.")

@shared_task(name="stats.update_dashboard_stats")
def update_dashboard_stats():
    """
    A Celery task to calculate and broadcast all key dashboard statistics.
    This is designed to be 'debounced' by calling it with a countdown.
    """
    logger.info("Running scheduled dashboard stats update task.")
    
    _broadcast_update('stats_update', services.get_stats_card_data())
    _broadcast_update('chart_update_conversation_trends', services.get_conversation_trends_chart_data())
    _broadcast_update('chart_update_bot_performance', services.get_bot_performance_chart_data())

@shared_task(name="stats.broadcast_activity_log")
def broadcast_activity_log(payload):
    """Broadcasts a single activity log entry."""
    _broadcast_update('activity_log_add', payload)

@shared_task(name="stats.broadcast_human_intervention_notification")
def broadcast_human_intervention_notification(payload):
    """Broadcasts a notification for human intervention."""
    _broadcast_update('human_intervention_needed', payload)

@shared_task(name="stats.check_handover_timeout")
def check_handover_timeout(contact_id: int):
    """
    Checks if a human handover request has timed out (e.g., after 60 seconds).
    If it has, it notifies the user and resets the intervention flag.
    """
    try:
        contact = Contact.objects.get(pk=contact_id)

        # Proceed only if the flag is still set and the timestamp exists
        if contact.needs_human_intervention and contact.intervention_requested_at:
            # Check if more than 60 seconds have passed since the request
            if timezone.now() - contact.intervention_requested_at >= timedelta(seconds=60):
                logger.info(f"Human handover for contact {contact.id} has timed out. Notifying contact and resetting flag.")
                
                # Reset the flag first to prevent race conditions
                contact.needs_human_intervention = False
                contact.intervention_requested_at = None
                contact.save(update_fields=['needs_human_intervention', 'intervention_requested_at'])

                # Send a notification message to the contact
                active_config = MetaAppConfig.objects.get_active_config()
                if active_config:
                    timeout_message = Message.objects.create(
                        contact=contact,
                        app_config=active_config,
                        direction='out',
                        message_type='text',
                        content_payload={'body': "Apologies, all our agents are currently busy. Please try again in a few moments by typing 'help'."},
                        status='pending_dispatch'
                    )
                    # Send message immediately
                    send_whatsapp_message_task.delay(timeout_message.id, active_config.id)
            else:
                logger.info(f"Handover timeout check for contact {contact.id}: Timeout not yet reached or intervention already handled.")
        else:
            logger.info(f"Handover timeout check for contact {contact.id}: Intervention flag was already cleared before timeout.")
    except Contact.DoesNotExist:
        logger.warning(f"check_handover_timeout task ran for non-existent contact_id: {contact_id}")
    except MetaAppConfig.DoesNotExist:
        logger.error(f"Cannot send handover timeout message for contact {contact_id}: No active MetaAppConfig found.")
    except Exception as e:
        logger.error(f"Error in check_handover_timeout for contact {contact_id}: {e}", exc_info=True)