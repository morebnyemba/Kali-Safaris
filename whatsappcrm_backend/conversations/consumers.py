# whatsappcrm_backend/conversations/consumers.py
import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import Contact, Message
from .serializers import ContactDetailSerializer, MessageSerializer
from meta_integration.tasks import send_whatsapp_message_task
from meta_integration.models import MetaAppConfig

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_contact_for_user(contact_id, user):
    """
    Fetches a contact if it exists.
    In a multi-tenant or permissioned system, you would also check
    if `user` has permission to access this contact.
    """
    try:
        return Contact.objects.get(pk=contact_id)
    except Contact.DoesNotExist:
        return None

@database_sync_to_async
def create_and_dispatch_message(contact, user, message_text):
    """
    Creates an outgoing message and schedules it for sending.
    """
    try:
        active_config = MetaAppConfig.objects.get_active_config()
        if not active_config:
            logger.error(f"No active MetaAppConfig found. Cannot send message from user {user.id} to contact {contact.id}.")
            return None
        
        message = Message.objects.create(
            contact=contact,
            direction='out',
            message_type='text',
            content_payload={'body': message_text},
            status='pending_dispatch',
        )
        # The post_save signal on the Message model will broadcast this.
        # We can also explicitly trigger the send task here.
        send_whatsapp_message_task.delay(message.id, active_config.id)
        return message
    except Exception as e:
        logger.error(f"Error creating/dispatching message from user {user.id} to contact {contact.id}: {e}", exc_info=True)
        return None

@database_sync_to_async
def toggle_intervention_status(contact_id: int):
    """
    Toggles the 'needs_human_intervention' flag for a contact and returns the updated, serialized object.
    """
    try:
        contact = Contact.objects.get(pk=contact_id)
        contact.needs_human_intervention = not contact.needs_human_intervention
        if not contact.needs_human_intervention:
            contact.intervention_requested_at = None
        else:
            # Set the timestamp when intervention is requested
            contact.intervention_requested_at = timezone.now()
        contact.save(update_fields=['needs_human_intervention', 'intervention_requested_at', 'last_seen'])
        
        # Use the detail serializer to ensure the frontend gets the full object
        serializer = ContactDetailSerializer(contact)
        return serializer.data
    except Contact.DoesNotExist:
        logger.error(f"Contact {contact_id} not found in toggle_intervention_status.")
        return None


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    """
    Handles real-time messaging and status updates for a specific conversation.
    """
    async def connect(self):
        self.contact_id = self.scope['url_route']['kwargs']['contact_id']
        self.user = self.scope['user']

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.contact = await get_contact_for_user(self.contact_id, self.user)
        if not self.contact:
            logger.warning(f"User {self.user.id} tried to connect to non-existent or unauthorized contact WebSocket: {self.contact_id}")
            await self.close(code=4003)
            return

        self.group_name = f'conversation_{self.contact_id}'

        # Join conversation group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"User {self.user.id} connected to conversation WebSocket for contact {self.contact_id}.")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"User {self.user.id} disconnected from conversation WebSocket for contact {self.contact_id}.")

    async def receive_json(self, content):
        """
        Receive a message from the WebSocket.
        Dispatches actions based on the 'type' field in the JSON payload.
        """
        message_type = content.get('type')
        
        if message_type == 'send_message':
            message_text = content.get('message')
            if message_text:
                await create_and_dispatch_message(self.contact, self.user, message_text)
                logger.info(f"User {self.user.id} sent message via WebSocket to contact {self.contact_id}: '{message_text[:50]}...'")

        elif message_type == 'toggle_intervention':
            updated_contact_data = await toggle_intervention_status(self.contact_id)
            if updated_contact_data:
                # Broadcast the updated contact data to all clients in the group
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'contact_updated',
                        'contact': updated_contact_data
                    }
                )

    # Handler for broadcasts from the channel layer
    async def contact_updated(self, event):
        """
        Handler for contact status updates broadcast from the channel layer.
        """
        await self.send_json({'type': 'contact_updated', 'contact': event['contact']})

    async def new_message(self, event):
        """
        Handler for new messages broadcast from the channel layer (e.g., from signals).
        The signal sends a serialized message.
        """
        await self.send_json({'type': 'new_message', 'message': event['message']})

