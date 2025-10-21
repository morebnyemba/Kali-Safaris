# whatsappcrm_backend/meta_integration/admin.py

from django.contrib import admin
from .models import MetaAppConfig, WebhookEventLog

@admin.register(MetaAppConfig)
class MetaAppConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number_id', 'waba_id', 'api_version', 'is_active', 'updated_at')
    list_filter = ('is_active', 'api_version')
    search_fields = ('name', 'phone_number_id', 'waba_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('API Credentials & Identifiers (Keep these confidential)', {
            'fields': ('verify_token', 'access_token', 'app_secret', 'phone_number_id', 'waba_id', 'api_version'),
            'description': "These details are used to connect to the Meta (WhatsApp) Cloud API. Ensure they are correct and kept secure."
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_type', 'event_identifier', 'message_link', 'app_config_name', 'received_at', 'processing_status')
    list_filter = ('event_type', 'processing_status', 'received_at', 'app_config', 'waba_id_received', 'phone_number_id_received')
    search_fields = ('event_identifier', 'payload', 'processing_notes', 'waba_id_received', 'phone_number_id_received', 'message__wamid', 'message__contact__name')
    readonly_fields = ('app_config', 'message', 'payload_object_type', 'payload', 'received_at', 'processed_at')
    date_hierarchy = 'received_at'
    list_per_page = 25

    fieldsets = (
        (None, {'fields': ('event_type', 'event_identifier', 'app_config', 'message')}),
        ('Payload Information', {'fields': ('payload_object_type', 'waba_id_received', 'phone_number_id_received', 'payload')}),
        ('Processing Details', {'fields': ('processing_status', 'processing_notes', 'processed_at')}),
        ('Timestamps', {'fields': ('received_at',), 'classes': ('collapse',)}),
    )

    def app_config_name(self, obj):
        return obj.app_config.name if obj.app_config else "N/A"
    app_config_name.short_description = "App Configuration"

    def message_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.message:
            link = reverse("admin:conversations_message_change", args=[obj.message.id])
            return format_html('<a href="{}">{}</a>', link, f"Msg {obj.message.id}")
        return "N/A"
    message_link.short_description = "Message"

    def get_queryset(self, request):
        # Optimize query by prefetching related MetaAppConfig
        return super().get_queryset(request).select_related('app_config', 'message')
