from django.db import models


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
