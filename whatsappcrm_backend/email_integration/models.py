from django.db import models
from django.utils.timezone import now

class EmailAttachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    sender = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    email_date = models.DateTimeField(blank=True, null=True) # Changed from CharField
    saved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False, db_index=True)
    extracted_data = models.JSONField(blank=True, null=True, help_text="Structured data extracted by AI model.")

    def __str__(self):
        return f"{self.filename} (Processed: {self.processed})"

class ParsedInvoice(models.Model):
    """Stores structured data extracted from an email attachment."""
    attachment = models.OneToOneField(
        EmailAttachment,
        on_delete=models.CASCADE,
        related_name='parsed_invoice'
    )
    invoice_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    invoice_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    extracted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.invoice_number or 'N/A'} from {self.attachment.filename}"