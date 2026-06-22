from django.db import models
from django.core.exceptions import ValidationError


class CBZConfig(models.Model):
    """
    Stores iVeri/CBZ API configuration credentials in the database.
    Only one active configuration is allowed at a time.

    ApplicationID is obtained from the iVeri backoffice portal.
    CertificateID is required for REST transactions, but can be generated later
    through the SOAP certificate lifecycle if it is not yet available.
    """
    name = models.CharField(
        max_length=100, default='Default',
        help_text="Configuration name for reference (e.g., 'Production', 'UAT')"
    )
    portal_url = models.URLField(
        max_length=500,
        default='https://portal.host.iveri.com',
        help_text="iVeri Gateway Portal URL"
    )
    certificate_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="CertificateID (GUID) used by REST transactions. Can be generated via SOAP lifecycle tools."
    )
    application_id = models.CharField(
        max_length=100,
        help_text="ApplicationID (GUID) assigned by the acquiring bank (CBZ)"
    )
    mode = models.CharField(
        max_length=10,
        choices=[('Test', 'Test / Sandbox'), ('LIVE', 'Live / Production')],
        default='Test',
        help_text="Transaction mode: Test for sandbox, LIVE for production"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one configuration can be active at a time"
    )
    
    # Optional: out-of-band notification URL for async results
    callback_url = models.URLField(
        max_length=500, blank=True, null=True,
        help_text="URL for iVeri to send out-of-band transaction notifications (optional)"
    )

    # COPYandPAY (OPPWA / ZimSwitch) credentials
    copyandpay_base_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="COPYandPAY base URL, e.g. https://eu-test.oppwa.com"
    )
    copyandpay_entity_id = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text="COPYandPAY entityId for checkout preparation"
    )
    copyandpay_bearer_token = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Authorization bearer token used for COPYandPAY API calls"
    )
    copyandpay_test_mode = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        help_text="Optional testMode value (for example EXTERNAL)"
    )
    copyandpay_brands = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Space-separated brands exposed by paymentWidgets. This merchant entityId is provisioned by ZimSwitch as Private Label only (default: PRIVATE_LABEL). Only brands enabled on your CBZ merchant account will appear in the widget."
    )
    copyandpay_widget_integrity = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Optional SRI integrity hash for paymentWidgets.js"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CBZ/iVeri Configuration'
        verbose_name_plural = 'CBZ/iVeri Configurations'
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status}, {self.get_mode_display()})"

    def clean(self):
        """Ensure only one active configuration exists."""
        if self.is_active:
            existing_active = CBZConfig.objects.filter(is_active=True)
            if self.pk:
                existing_active = existing_active.exclude(pk=self.pk)
            if existing_active.exists():
                raise ValidationError({
                    'is_active': (
                        'Only one CBZ/iVeri configuration can be active at a time. '
                        'Please deactivate the current active configuration first.'
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(cls):
        """Returns the active configuration or None."""
        return cls.objects.filter(is_active=True).first()


class CBZTransaction(models.Model):
    """
    Tracks CBZ/iVeri payment transactions through their lifecycle.
    Supports both EcoCash (mobile money) and Card (Visa/Mastercard) payments.
    """

    class PaymentType(models.TextChoices):
        ECOCASH = 'ecocash', 'EcoCash'
        CARD = 'card', 'Card (Visa/Mastercard)'

    class TransactionStatus(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        DECLINED = 'DECLINED', 'Declined'
        FAILED = 'FAILED', 'Failed'
        VOIDED = 'VOIDED', 'Voided'
        REFUNDED = 'REFUNDED', 'Refunded'

    # Merchant reference (unique per transaction)
    merchant_reference = models.CharField(
        max_length=100, unique=True, db_index=True,
        help_text="Unique merchant reference for this transaction"
    )

    # iVeri references (populated from response)
    transaction_index = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="iVeri TransactionIndex returned on success"
    )
    request_id = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="iVeri RequestID for tracking"
    )

    # Payment type
    payment_type = models.CharField(
        max_length=10, choices=PaymentType.choices,
        help_text="Type of payment: EcoCash or Card"
    )

    # Customer details
    msisdn = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Mobile number for EcoCash payments (2637XXXXXXXX format)"
    )
    # Card details are NOT stored — only masked PAN for reference
    masked_pan = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Masked card PAN (e.g., 5413****0020) — for reference only"
    )

    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('ZWG', 'ZWG')])
    command = models.CharField(
        max_length=20, default='Debit',
        help_text="iVeri command (Debit, Authorisation, Credit, etc.)"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.INITIATED
    )
    result_code = models.CharField(max_length=32, blank=True, null=True)
    result_description = models.TextField(blank=True, null=True)

    # iVeri authorisation details
    authorisation_code = models.CharField(max_length=20, blank=True, null=True)

    # Additional iVeri response fields (Phase 2 — data-to-persist requirements)
    bank_reference = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Bank reference number returned by iVeri/acquiring bank"
    )
    consumer_order_id = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Consumer-facing order ID from iVeri response"
    )
    card_bin = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Card BIN (first 6 digits) — identifies card network/issuer"
    )

    # Raw gateway response for audit/troubleshooting (never contains full PAN/CVV)
    gateway_response = models.JSONField(
        blank=True, null=True,
        help_text="Raw iVeri response payload for audit purposes (PCI-scrubbed)"
    )

    # Idempotency key — prevents duplicate payment submissions
    idempotency_key = models.CharField(
        max_length=64, blank=True, null=True, unique=True, db_index=True,
        help_text="Client-supplied idempotency key to prevent duplicate transactions"
    )

    # Link to booking
    booking = models.ForeignKey(
        'customer_data.Booking',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cbz_transactions',
        help_text="The booking this payment is for"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'CBZ/iVeri Transaction'
        verbose_name_plural = 'CBZ/iVeri Transactions'

    def __str__(self):
        return f"{self.merchant_reference} - {self.payment_type} - {self.status} - {self.currency} {self.amount}"

    @property
    def is_successful(self):
        return self.status == self.TransactionStatus.APPROVED
