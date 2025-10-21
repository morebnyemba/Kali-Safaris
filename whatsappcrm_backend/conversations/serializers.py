# whatsappcrm_backend/conversations/serializers.py

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
import logging

from .models import Contact, Message, Broadcast, BroadcastRecipient
from meta_integration.tasks import send_whatsapp_message_task
from meta_integration.models import MetaAppConfig

logger = logging.getLogger(__name__)

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for basic Contact model information.
    """
    # If you have a method on the model to get a display name or prefer contact.name
    # display_name = serializers.CharField(source='get_display_name', read_only=True) # Example

    class Meta:
        model = Contact
        fields = [
            'id',
            'whatsapp_id',
            'name',
            'first_seen', # This is the contact creation timestamp
            'last_seen',
            'is_blocked',
            'needs_human_intervention', # From your updated Contact model
            'intervention_requested_at', # From your updated Contact model
            # 'display_name', # If you add a property for it
        ]
        read_only_fields = ('id', 'first_seen', 'last_seen', 'intervention_requested_at')

    # Example validation if you need it (not strictly required by current setup)
    # def validate_whatsapp_id(self, value):
    #     if not re.match(r"^\+?\d{10,15}$", value): # Basic international phone number regex
    #         raise serializers.ValidationError("Invalid WhatsApp ID format.")
    #     return value

class MessageSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Message model.
    """
    # For read operations, showing basic contact details with the message
    contact_details = ContactSerializer(source='contact', read_only=True)
    # For write operations (creating a message), frontend will send contact PK
    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all(), write_only=True)
    
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'contact', # Write-only ID for associating message
            'contact_details', # Read-only nested object for display
            'wamid',
            'direction',
            'direction_display',
            'message_type',
            'message_type_display',
            'content_payload', # Full payload
            'text_content', # Extracted text
            'timestamp',
            'status',
            'status_display',
            'status_timestamp',
            'error_details',
            'is_internal_note',
        ]
        read_only_fields = (
            'id', 'wamid', 'timestamp', 'status_timestamp', 'error_details',
            'message_type_display', 'status_display', 'direction_display',
            'contact_details',
        )

    def create(self, validated_data):
        # This create method is for when your frontend POSTs to /crm-api/conversations/messages/
        # to send an outgoing message, for example, from an agent in the CRM UI.

        # Set defaults for outgoing messages created via API
        validated_data['direction'] = 'out'
        validated_data['status'] = 'pending_dispatch'
        if 'timestamp' not in validated_data:
            validated_data['timestamp'] = timezone.now()

        # Use a transaction to ensure the message is created before the task is scheduled.
        with transaction.atomic():
            message = Message.objects.create(**validated_data)
            active_config = MetaAppConfig.objects.get_active_config()
            if active_config:
                # Use on_commit to ensure the task is only queued if the DB transaction succeeds.
                transaction.on_commit(
                    lambda: send_whatsapp_message_task.delay(message.id, active_config.id)
                )
            else:
                logger.error(f"No active MetaAppConfig found. Message {message.id} cannot be dispatched.")
                message.status = 'failed'
                message.error_details = {'error': 'No active MetaAppConfig for sending.'}
                message.save(update_fields=['status', 'error_details'])

        return message

class MessageListSerializer(MessageSerializer):
    """
    A more concise serializer for listing Messages, excluding bulky fields like full content_payload.
    """
    content_preview = serializers.SerializerMethodField()

    class Meta(MessageSerializer.Meta):
        # Override fields from MessageSerializer.Meta
        fields = [
            'id',
            # 'contact', # Usually not needed in a list if messages are already filtered by contact
            'contact_details', # Or just contact_id and contact_name if contact_details is too much
            'wamid',
            'direction',
            'direction_display',
            'message_type',
            'message_type_display',
            'timestamp',
            'status',
            'status_display',
            'content_preview', # Custom preview field
            'text_content',
            'content_payload',
            'is_internal_note',
        ]
        # read_only_fields are inherited and all listed fields are effectively read_only here.

    def get_content_preview(self, obj: Message) -> str:
        if obj.text_content:
            return (obj.text_content[:75] + '...') if len(obj.text_content) > 75 else obj.text_content
        
        # Provide more specific previews for common non-text types
        if obj.message_type == 'image': return "[Image]"
        if obj.message_type == 'document': return f"[Document: {obj.content_payload.get('document', {}).get('filename', 'file')}]"
        if obj.message_type == 'audio': return "[Audio]"
        if obj.message_type == 'video': return "[Video]"
        if obj.message_type == 'sticker': return "[Sticker]"
        if obj.message_type == 'location': return "[Location Shared]"
        if obj.message_type == 'contacts': return "[Contact Card Shared]"
        
        if obj.message_type == 'interactive' and isinstance(obj.content_payload, dict):
            interactive_type = obj.content_payload.get('type')
            if interactive_type == 'button_reply' and obj.content_payload.get('button_reply'):
                return f"Button Click: {obj.content_payload['button_reply'].get('title', obj.content_payload['button_reply'].get('id'))}"
            if interactive_type == 'list_reply' and obj.content_payload.get('list_reply'):
                return f"List Selection: {obj.content_payload['list_reply'].get('title', obj.content_payload['list_reply'].get('id'))}"
            return f"Interactive: {interactive_type or 'message'}"
        
        if obj.message_type == 'system' and isinstance(obj.content_payload, dict) and obj.content_payload.get('system', {}).get('body'):
            return f"System: {obj.content_payload['system']['body']}"

        return f"({obj.get_message_type_display()})"

class ContactListSerializer(ContactSerializer):
    """
    Serializer for the contact list view. It adds extra context like
    the last message preview and unread count, which are expected to be
    annotated onto the queryset by the view.
    """
    last_message_preview = serializers.CharField(read_only=True, default="No messages yet")
    unread_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(ContactSerializer.Meta):
        # Inherit all fields from the base ContactSerializer and add the new ones.
        fields = ContactSerializer.Meta.fields + ['last_message_preview', 'unread_count']



class ContactDetailSerializer(ContactSerializer):
    """
    Contact serializer that includes the nested CustomerProfile 
    and a list of recent messages for detailed views.
    """
    # The view must prefetch the related messages into an attribute named 'messages'.
    # e.g., .prefetch_related('messages')
    recent_messages = MessageListSerializer(many=True, read_only=True, source='messages')

    class Meta(ContactSerializer.Meta):
        # Inherit fields from ContactSerializer and add new ones
        fields = ContactSerializer.Meta.fields + ['recent_messages']

class BroadcastCreateSerializer(serializers.Serializer):
    """
    Serializer for validating the creation of a broadcast job.
    This is used by the `create` action of the BroadcastViewSet.
    """
    name = serializers.CharField(max_length=255, required=False, help_text="An optional internal name for this broadcast.")
    contact_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="A list of Contact IDs to send the message to."
    )
    template_name = serializers.CharField(max_length=255)
    language_code = serializers.CharField(max_length=15, default="en_US")
    components = serializers.ListField(
        child=serializers.DictField(), 
        required=False, 
        help_text="A template for components with variables like {{ member_profile.first_name }}. E.g., [{'type': 'body', 'parameters': [{'type': 'text', 'text': '{{ member_profile.first_name }}'}]}]"
    )

    def validate_contact_ids(self, value):
        """
        Check if all provided contact IDs exist in the database.
        """
        existing_contacts_count = Contact.objects.filter(id__in=value).count()
        if existing_contacts_count != len(set(value)):
            raise serializers.ValidationError("One or more contact IDs are invalid or do not exist.")
        return value


class BroadcastGroupCreateSerializer(serializers.Serializer):
    """
    Serializer for validating the creation of a broadcast job targeted at a dynamic group.
    """
    name = serializers.CharField(max_length=255, required=False, help_text="An optional internal name for this broadcast.")
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text="A list of tags. Contacts with ANY of these tags will be targeted."
    )
    assigned_agent_id = serializers.IntegerField(required=False, help_text="ID of an admin/agent. All contacts assigned to this agent will be targeted.")
    
    template_name = serializers.CharField(max_length=255)
    language_code = serializers.CharField(max_length=15, default="en_US")
    components = serializers.ListField(
        child=serializers.DictField(), 
        required=False, 
        help_text="A template for components with variables. E.g., [{'type': 'body', 'parameters': [{'type': 'text', 'text': '{{ customer_profile.first_name }}'}]}]"
    )

    def validate(self, data):
        if not data.get('tags') and data.get('assigned_agent_id') is None:
            raise serializers.ValidationError("You must provide at least one targeting option: 'tags' or 'assigned_agent_id'.")
        return data


class BroadcastRecipientSerializer(serializers.ModelSerializer):
    """Serializer for displaying individual recipient status within a broadcast."""
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = BroadcastRecipient
        fields = ['id', 'contact', 'status', 'status_timestamp']


class BroadcastSerializer(serializers.ModelSerializer):
    """Serializer for displaying the details and aggregate status of a Broadcast job."""
    recipients = BroadcastRecipientSerializer(many=True, read_only=True, help_text="A list of recipients and their individual statuses.")
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Broadcast
        fields = [
            'id', 'name', 'template_name', 'created_by_username', 'created_at', 'status',
            'total_recipients', 'pending_dispatch_count', 'sent_count', 'delivered_count',
            'read_count', 'failed_count'
        ]