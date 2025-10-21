# stats/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from datetime import timedelta
from conversations.models import Contact, Message

import logging
logger = logging.getLogger(__name__)

class DashboardConsumer(WebsocketConsumer):
    """
    This consumer handles WebSocket connections for the live dashboard.
    It adds connecting users to a group and sends them updates pushed from signals.
    """
    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            self.close()
            return

        self.group_name = 'dashboard_updates'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()
        logger.info(f"User {self.user} connected to dashboard WebSocket and joined group '{self.group_name}'.")

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Leave room group
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )
            logger.info(f"User {self.user} disconnected from dashboard WebSocket.")

    # Receive message from WebSocket (we don't need this for a one-way push, but it's good practice)
    def receive(self, text_data):
        # You could implement logic here for the client to request a full data refresh, for example.
        pass

    # --- Handler for messages sent from the channel layer (e.g., from signals) ---
    def dashboard_update(self, event):
        """
        This method is called when a message with type 'dashboard.update'
        is sent to the group.
        """
        update_type = event.get('update_type')
        payload = event.get('payload', {})
        
        logger.debug(f"Consumer received dashboard_update event: type={update_type}, payload={payload}")

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'type': update_type,
            'payload': payload
        }))
        logger.debug(f"Sent update of type '{update_type}' to client {self.user}.")

    # --- Example of a more complex handler that could calculate stats here ---
    def recalculate_and_send(self, event):
        """
        An alternative pattern where the consumer does the calculation.
        The signal would just send a simple trigger like {'event': 'new_message'}.
        """
        event_trigger = event.get('event')
        stats_to_send = {}

        if event_trigger == 'new_message':
            now = timezone.now()
            twenty_four_hours_ago = now - timedelta(hours=24)
            stats_to_send['messages_sent_24h'] = Message.objects.filter(
                direction='out', timestamp__gte=twenty_four_hours_ago
            ).count()
            stats_to_send['messages_received_24h'] = Message.objects.filter(
                direction='in', timestamp__gte=twenty_four_hours_ago
            ).count()
        
        elif event_trigger == 'new_contact':
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            stats_to_send['new_contacts_today'] = Contact.objects.filter(
                first_seen__gte=today_start, first_seen__lte=today_end
            ).count()
            stats_to_send['total_contacts'] = Contact.objects.count()

        if stats_to_send:
            self.send(text_data=json.dumps({
                'type': 'stats_update',
                'payload': stats_to_send
            }))