from django.contrib import admin
from .models import Notification, NotificationTemplate

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'status', 'channel', 'created_at', 'sent_at')
    list_filter = ('status', 'channel', 'recipient')
    search_fields = ('recipient__username', 'content')
    readonly_fields = ('created_at', 'sent_at', 'recipient', 'related_contact', 'related_flow', 'content', 'error_message')
    list_per_page = 30
    list_select_related = ('recipient',)

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'updated_at')
    search_fields = ('name', 'message_body', 'description')