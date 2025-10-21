# whatsappcrm_backend/meta_integration/serializers.py

from rest_framework import serializers
from .models import MetaAppConfig, WebhookEventLog

class MetaAppConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for the MetaAppConfig model.
    Provides CRUD operations.
    """
    class Meta:
        model = MetaAppConfig
        fields = [
            'id',
            'name',
            'verify_token',
            'access_token', # Be cautious about exposing this directly or ensure proper permissions
            'app_secret',
            'phone_number_id',
            'waba_id',
            'api_version',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'access_token': {
                'write_only': True,
                'required': False, # Not required on PATCH/PUT unless provided
                'style': {'input_type': 'password'},
                'help_text': "Leave empty if not changing."
            },
            'app_secret': {
                'write_only': True,
                'required': False, # Not required on PATCH/PUT unless provided
                'style': {'input_type': 'password'},
                'help_text': "Leave empty if not changing. Used for webhook signature verification."
            },
            'verify_token': {
                'style': {'input_type': 'password'}
            },
        }


class WebhookEventLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the WebhookEventLog model.
    Typically used for read-only purposes from the frontend.
    """
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    app_config_name = serializers.CharField(source='app_config.name', read_only=True, allow_null=True)

    class Meta:
        model = WebhookEventLog
        fields = [
            'id',
            'event_identifier',
            'app_config', # Foreign key ID
            'app_config_name', # Human-readable name
            'waba_id_received',
            'phone_number_id_received',
            'event_type',
            'event_type_display', # Human-readable event type
            'payload_object_type',
            'payload', # Could be large, consider excluding or making it optional for list views
            'received_at',
            'processed_at',
            'processing_status',
            'processing_notes'
        ]
        read_only_fields = fields # Make all fields read-only by default for logs


class WebhookEventLogListSerializer(WebhookEventLogSerializer):
    """
    A more concise serializer for listing WebhookEventLogs, excluding the large payload.
    """
    class Meta(WebhookEventLogSerializer.Meta):
        fields = [
            field for field in WebhookEventLogSerializer.Meta.fields if field != 'payload'
        ]
        read_only_fields = fields
