# whatsappcrm_backend/conversations/admin.py

from django.contrib import admin
from .models import Contact, Message, Broadcast, BroadcastRecipient

@admin.action(description='Clear human intervention flag for selected contacts')
def clear_human_intervention(modeladmin, request, queryset):
    """
    Admin action to manually clear the 'needs_human_intervention' flag.
    """
    updated_count = queryset.update(
        needs_human_intervention=False,
        intervention_requested_at=None
    )
    modeladmin.message_user(
        request,
        f"{updated_count} contact(s) were successfully updated. Human intervention flag cleared."
    )

class MessageInline(admin.TabularInline): # Or admin.StackedInline for a different layout
    model = Message
    fields = ('timestamp', 'direction', 'message_type', 'text_content_preview', 'status', 'wamid')
    readonly_fields = ('timestamp', 'direction', 'message_type', 'text_content_preview', 'status', 'wamid')
    extra = 0 # Don't show extra empty forms for adding messages here
    can_delete = False # Usually don't want to delete messages from contact view
    show_change_link = True # Link to the full message change form
    ordering = ('-timestamp',) # Show latest messages first in the inline

    def text_content_preview(self, obj):
        if obj.text_content:
            return (obj.text_content[:75] + '...') if len(obj.text_content) > 75 else obj.text_content
        if obj.message_type != 'text' and isinstance(obj.content_payload, dict):
            # For non-text, show a snippet of the payload keys or type
            if obj.message_type == 'interactive' and obj.content_payload.get('type'):
                return f"Interactive: {obj.content_payload.get('type')}"
            return f"({obj.message_type})"
        return "N/A"
    text_content_preview.short_description = "Content Preview"

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('whatsapp_id', 'name', 'user', 'needs_human_intervention', 'last_seen', 'is_blocked', 'associated_app_config_name')
    search_fields = ('whatsapp_id', 'name', 'user__username', 'user__email')
    list_filter = ('needs_human_intervention', 'is_blocked', 'last_seen', 'first_seen', 'associated_app_config')
    readonly_fields = ('first_seen', 'last_seen', 'intervention_requested_at')
    actions = [clear_human_intervention]
    inlines = [MessageInline]
    autocomplete_fields = ('user',)
    fieldsets = (
        (None, {'fields': ('whatsapp_id', 'name', 'is_blocked', 'needs_human_intervention')}),
        ('Association', {'fields': ('user', 'associated_app_config',)}),
        ('Timestamps', {'fields': ('first_seen', 'last_seen', 'intervention_requested_at'), 'classes': ('collapse',)}),
    )

    def associated_app_config_name(self, obj):
        return obj.associated_app_config.name if obj.associated_app_config else "N/A"
    associated_app_config_name.short_description = "App Config"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_link', 'direction', 'message_type', 'status', 'timestamp', 'wamid_short', 'app_config')
    list_filter = ('timestamp', 'direction', 'message_type', 'status', 'contact__name', 'app_config') # Add 'app_config' if using the FK
    search_fields = ('wamid', 'text_content', 'contact__whatsapp_id', 'contact__name', 'content_payload') # Be careful with JSON search
    readonly_fields = ('contact', 'app_config', 'wamid', 'direction', 'message_type', 'content_payload', 'timestamp', 'status_timestamp', 'error_details') # 'app_config'
    date_hierarchy = 'timestamp'
    list_per_page = 25
    fieldsets = (
        ('Message Info', {'fields': ('contact', 'app_config', 'direction', 'message_type', 'timestamp')}), # 'app_config'
        ('Content', {'fields': ('wamid', 'text_content', 'content_payload')}),
        ('Status & Delivery', {'fields': ('status', 'status_timestamp', 'error_details')}),
        ('Internal', {'fields': ('is_internal_note',)}),
    )

    def contact_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.contact:
            link = reverse("admin:conversations_contact_change", args=[obj.contact.id])
            return format_html('<a href="{}">{}</a>', link, obj.contact)
        return "N/A"
    contact_link.short_description = "Contact"

    def wamid_short(self, obj):
        if obj.wamid:
            return (obj.wamid[:20] + '...') if len(obj.wamid) > 20 else obj.wamid
        return "N/A"
    wamid_short.short_description = "WAMID"

    def get_queryset(self, request):
        # Optimize query by prefetching related Contact
        return super().get_queryset(request).select_related('contact', 'app_config') # 'app_config'


class BroadcastRecipientInline(admin.TabularInline):
    model = BroadcastRecipient
    fields = ('contact', 'status', 'status_timestamp', 'message')
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_name', 'status', 'total_recipients', 'sent_count', 'delivered_count', 'read_count', 'failed_count', 'created_at', 'created_by')
    list_filter = ('status', 'template_name', 'created_at')
    search_fields = ('name', 'template_name', 'created_by__username')
    readonly_fields = ('created_at', 'created_by', 'total_recipients', 'pending_dispatch_count', 'sent_count', 'delivered_count', 'read_count', 'failed_count')
    inlines = [BroadcastRecipientInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
