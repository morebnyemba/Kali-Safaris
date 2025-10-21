from django.contrib import admin
from django.utils.html import format_html
import json
from .models import EmailAttachment, ParsedInvoice

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'sender', 'processed', 'email_date', 'saved_at')
    list_filter = ('processed', 'email_date', 'sender')
    search_fields = ('filename', 'sender', 'subject')
    readonly_fields = ('saved_at', 'updated_at', 'pretty_extracted_data')
    fieldsets = (
        (None, {'fields': ('filename', 'sender', 'subject', 'email_date', 'processed')}),
        ('File Info', {'fields': ('file',)}),
        ('Extracted Data', {'fields': ('pretty_extracted_data',)}),
        ('Timestamps', {'fields': ('saved_at', 'updated_at')}),
    )

    def pretty_extracted_data(self, instance):
        """Displays the JSON data in a readable format."""
        if instance.extracted_data:
            # Convert the dict to a formatted string
            pretty_json = json.dumps(instance.extracted_data, indent=2)
            return format_html("<pre><code>{}</code></pre>", pretty_json)
        return "No data extracted."
    pretty_extracted_data.short_description = "Extracted Data (Formatted)"

@admin.register(ParsedInvoice)
class ParsedInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'attachment_filename', 'invoice_date', 'total_amount')
    search_fields = ('invoice_number', 'attachment__filename')

    def attachment_filename(self, obj):
        return obj.attachment.filename
    attachment_filename.short_description = 'Attachment'