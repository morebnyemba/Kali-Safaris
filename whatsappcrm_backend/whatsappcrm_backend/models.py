from django.db import models

class EmailAttachment(models.Model):
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    sender = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    email_date = models.CharField(max_length=255, blank=True, null=True)
    saved_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    ocr_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.filename
