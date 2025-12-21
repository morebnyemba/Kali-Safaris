from django.db import models
from django.core.exceptions import ValidationError


class OmariConfig(models.Model):
    """
    Stores Omari API configuration credentials in the database.
    Only one active configuration is allowed at a time.
    """
    name = models.CharField(max_length=100, default='Default', help_text="Configuration name for reference")
    base_url = models.URLField(
        max_length=500,
        help_text="Base URL for Omari Merchant API (e.g., https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment)"
    )
    merchant_key = models.CharField(
        max_length=500,
        help_text="API Key provided by Omari for merchant authentication"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one configuration can be active at a time"
    )
    is_production = models.BooleanField(
        default=False,
        help_text="Indicates if this configuration is for production or testing"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Omari Configuration'
        verbose_name_plural = 'Omari Configurations'
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        env = "Production" if self.is_production else "UAT/Test"
        return f"{self.name} ({status}, {env})"
    
    def clean(self):
        """Ensure only one active configuration exists."""
        if self.is_active:
            # Check if there's already an active config (excluding self)
            existing_active = OmariConfig.objects.filter(is_active=True)
            if self.pk:
                existing_active = existing_active.exclude(pk=self.pk)
            
            if existing_active.exists():
                raise ValidationError({
                    'is_active': 'Only one Omari configuration can be active at a time. Please deactivate the current active configuration first.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """Returns the active configuration or None."""
        return cls.objects.filter(is_active=True).first()


class OmariTransaction(models.Model):
    """Tracks Omari payment transactions through the OTP flow."""

    # Merchant reference (UUID)
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Customer details
    msisdn = models.CharField(max_length=20)
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('ZWG', 'ZWG')])
    channel = models.CharField(max_length=10, choices=[('WEB', 'WEB'), ('POS', 'POS')], default='WEB')
    
    # OTP flow tracking
    otp_reference = models.CharField(max_length=50, blank=True, null=True)
    otp_requested_at = models.DateTimeField(auto_now_add=True)
    
    # Payment completion
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    debit_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('INITIATED', 'Initiated'),
            ('OTP_SENT', 'OTP Sent'),
            ('SUCCESS', 'Success'),
            ('FAILED', 'Failed'),
            ('PENDING', 'Pending'),
        ],
        default='INITIATED'
    )
    response_code = models.CharField(max_length=10, blank=True, null=True)
    response_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Link to booking/order
    booking = models.ForeignKey(
        'customer_data.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='omari_transactions',
        help_text="The booking this payment is for"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Omari Transaction'
        verbose_name_plural = 'Omari Transactions'
    
    def __str__(self):
        return f"{self.reference} - {self.status} - {self.currency} {self.amount}"
