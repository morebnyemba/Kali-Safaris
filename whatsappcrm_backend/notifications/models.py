from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """
    Represents a notification to be sent to a system user (admin/agent).
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(_("Channel"), max_length=20, default='whatsapp')
    status = models.CharField(
        _("Status"), max_length=20,
        choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('read', 'Read')],
        default='pending', db_index=True
    )
    content = models.TextField(_("Content"))
    related_contact = models.ForeignKey('conversations.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_notifications')
    related_flow = models.ForeignKey('flows.Flow', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_notifications')
    
    template_name = models.CharField(max_length=100, blank=True, null=True, help_text="The name of the WhatsApp template to use if outside the 24h window.")
    template_context = models.JSONField(blank=True, null=True, help_text="The context data required to render the template variables.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Notification for {self.recipient.username} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("System Notification")
        verbose_name_plural = _("System Notifications")

class NotificationTemplate(models.Model):
    """
    Stores templates for system notifications.
    """
    name = models.CharField(
        _("Template Name"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique identifier for this template, e.g., 'human_handover_required'."
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    message_body = models.TextField(
        _("Message Body"),
        help_text="The template content. Can use Jinja2 variables like {{ contact.name }}."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("Notification Template")
        verbose_name_plural = _("Notification Templates")