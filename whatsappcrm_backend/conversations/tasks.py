# conversations/tasks.py
from celery import shared_task
import logging
from django.utils import timezone
from django.db import transaction

from .models import Broadcast, BroadcastRecipient, Contact, Message
from meta_integration.models import MetaAppConfig
from meta_integration.tasks import send_whatsapp_message_task
# from flows.services import _resolve_value # For advanced personalization

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def dispatch_broadcast_task(self, broadcast_id, contact_ids, language_code, components_template):
    """
    Celery task to fetch a broadcast, create individual messages for each recipient,
    and queue them for sending.
    """
    try:
        with transaction.atomic():
            broadcast = Broadcast.objects.get(pk=broadcast_id)
            if broadcast.status not in ['pending', 'failed']:
                logger.warning(f"Broadcast {broadcast_id} is already in progress or completed. Skipping.")
                return

            broadcast.status = 'in_progress'
            broadcast.save(update_fields=['status'])

            active_config = MetaAppConfig.objects.get_active_config()
            contacts = Contact.objects.filter(id__in=contact_ids)
            
            logger.info(f"Starting broadcast {broadcast_id} for {contacts.count()} recipients.")

            messages_to_create = []

            for contact in contacts:
                # TODO: Implement advanced personalization using a service like _resolve_value
                # from flows.services if you need to substitute variables like {{name}}.
                content_payload = {
                    "name": broadcast.template_name,
                    "language": {"code": language_code},
                    "components": components_template or []
                }

                message = Message(
                    contact=contact,
                    app_config=active_config,
                    direction='out',
                    message_type='template',
                    content_payload=content_payload,
                    status='pending_dispatch',
                    timestamp=timezone.now(),
                )
                messages_to_create.append(message)

            created_messages = Message.objects.bulk_create(messages_to_create)
            
            broadcast_recipients = [BroadcastRecipient(broadcast=broadcast, contact=msg.contact, message=msg) for msg in created_messages]
            BroadcastRecipient.objects.bulk_create(broadcast_recipients)

            for message in created_messages:
                send_whatsapp_message_task.delay(message.id, active_config.id)

            broadcast.status = 'completed'
            broadcast.pending_dispatch_count = contacts.count()
            broadcast.save(update_fields=['status', 'pending_dispatch_count'])
            logger.info(f"All messages for broadcast {broadcast_id} have been queued.")

    except Broadcast.DoesNotExist:
        logger.warning(f"Broadcast with ID {broadcast_id} was not found. Task will not be retried.")
    except MetaAppConfig.DoesNotExist:
        logger.error(f"No active MetaAppConfig found for broadcast {broadcast_id}. Aborting and marking as failed.")
        Broadcast.objects.filter(pk=broadcast_id).update(status='failed')
    except Exception as exc:
        logger.error(f"Error dispatching broadcast {broadcast_id}: {exc}. Retrying...")
        Broadcast.objects.filter(pk=broadcast_id).update(status='failed')
        raise self.retry(exc=exc, countdown=60)
