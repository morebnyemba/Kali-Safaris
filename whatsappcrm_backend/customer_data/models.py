# whatsappcrm_backend/customer_data/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _ # type: ignore
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from conversations.models import Contact
import uuid

# Import the new Tour model
from products_and_services.models import Tour

class LeadStatus(models.TextChoices):
    """Defines the choices for the lead status in the sales pipeline."""
    NEW = 'new', _('New')
    CONTACTED = 'contacted', _('Contacted')
    QUALIFIED = 'qualified', _('Qualified')
    PROPOSAL_SENT = 'proposal_sent', _('Proposal Sent')
    NEGOTIATION = 'negotiation', _('Negotiation')
    WON = 'won', _('Won')
    LOST = 'lost', _('Lost')
    ON_HOLD = 'on_hold', _('On Hold')

class InteractionType(models.TextChoices):
    """Defines the types of interactions that can be logged."""
    CALL = 'call', _('Call')
    EMAIL = 'email', _('Email')
    WHATSAPP = 'whatsapp', _('WhatsApp Message')
    MEETING = 'meeting', _('Meeting')
    NOTE = 'note', _('Internal Note')
    OTHER = 'other', _('Other')

class CustomerProfile(models.Model):
    """
    Stores aggregated and specific data about a customer, linked to their Contact record.
    This profile is enriched over time through conversations, forms, and manual entry.
    """
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        primary_key=True,
        help_text=_("The contact this customer profile belongs to.")
    )
    
    # Basic Info (can be synced or enriched)
    first_name = models.CharField(_("First Name"), max_length=100, blank=True, null=True)
    last_name = models.CharField(_("Last Name"), max_length=100, blank=True, null=True)
    email = models.EmailField(_("Email Address"), max_length=254, blank=True, null=True)
    company = models.CharField(_("Company"), max_length=150, blank=True, null=True)
    role = models.CharField(_("Role/Title"), max_length=100, blank=True, null=True)
    
    # Location Details
    address_line_1 = models.CharField(_("Address Line 1"), max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(_("Address Line 2"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    state_province = models.CharField(_("State/Province"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, null=True)
    
    # Sales & Lead Information
    lead_status = models.CharField(
        _("Lead Status"),
        max_length=50,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
        db_index=True,
        help_text=_("The current stage of the customer in the sales pipeline.")
    )
    potential_value = models.DecimalField(
        _("Potential Value"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Estimated value of the deal or lifetime value of the customer.")
    )
    acquisition_source = models.CharField(
        _("Acquisition Source"),
        max_length=150, 
        blank=True, 
        null=True, 
        help_text=_("How this customer was acquired, e.g., 'Website Form', 'Cold Call', 'Referral'")
    )
    lead_score = models.IntegerField(
        _("Lead Score"),
        default=0,
        db_index=True,
        help_text=_("A score to qualify leads, can be updated by flow actions.")
    )
    
    # Agent Assignment & Segmentation
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='assigned_customers',
        help_text=_("The sales or support agent assigned to this customer.")
    )
    tags = models.JSONField(
        _("Tags"),
        default=list, 
        blank=True, 
        help_text=_("Descriptive tags for segmentation, e.g., ['high-priority', 'tech-industry', 'follow-up']")
    )
    
    # Notes & Custom Data
    notes = models.TextField(
        _("Notes"), 
        blank=True, 
        null=True,
        help_text=_("General notes about the customer, their needs, or past interactions.")
    )
    custom_attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Flexible field for storing custom data collected via forms or integrations.")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_interaction_date = models.DateTimeField(
        _("Last Interaction Date"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Timestamp of the last recorded interaction with this customer.")
    )

    def get_full_name(self) -> str | None:
        """Returns the full name of the customer, or None if no name is set."""
        parts = [self.first_name, self.last_name]
        full_name = " ".join(p for p in parts if p)
        return full_name or None

    def __str__(self) -> str:
        """Returns a string representation of the customer profile."""
        display_name = self.get_full_name() or self.contact.name or self.contact.whatsapp_id
        return f"Customer: {display_name}"

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")
        ordering = ['-last_interaction_date', '-updated_at']


class Interaction(models.Model):
    """
    Represents a single interaction with a customer, such as a call, email, or meeting.
    This creates a historical log of all communications.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='interactions',
        help_text=_("The customer this interaction is associated with.")
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interactions',
        help_text=_("The agent who had the interaction.")
    )
    interaction_type = models.CharField(
        _("Interaction Type"),
        max_length=50,
        choices=InteractionType.choices,
        default=InteractionType.NOTE
    )
    notes = models.TextField(
        _("Notes / Summary"),
        help_text=_("A summary of the interaction, key points, and next steps.")
    )
    created_at = models.DateTimeField(
        _("Interaction Time"),
        default=timezone.now,
        help_text=_("When the interaction occurred.")
    )

    def __str__(self) -> str:
        """Returns a string representation of the interaction."""
        return f"{self.get_interaction_type_display()} with {self.customer} on {self.created_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs) -> None:
        """
        Overrides the save method to automatically update the related customer's
        `last_interaction_date` field. This ensures the customer profile
        always reflects the latest activity.
        """
        super().save(*args, **kwargs)
        if self.customer:
            # Using update_fields is a performance best practice, as it avoids
            # re-saving all fields and triggering unnecessary database operations.
            self.customer.last_interaction_date = self.created_at
            self.customer.save(update_fields=['last_interaction_date']) # type: ignore

    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")
        ordering = ['-created_at']


class Booking(models.Model):
    """
    Represents a customer's booking for a specific tour.
    This model replaces the old 'Order' model.
    """
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PENDING_MANUAL = 'pending_manual', _('Pending Manual Verification')
        DEPOSIT_PAID = 'deposit_paid', _('Deposit Paid')
        PAID = 'paid', _('Paid in Full')
        REFUNDED = 'refunded', _('Refunded')
        CANCELLED = 'cancelled', _('Cancelled')

    class BookingSource(models.TextChoices):
        WHATSAPP = 'whatsapp', _('WhatsApp')
        EMAIL_IMPORT = 'email_import', _('Email Import')
        MANUAL_ENTRY = 'manual_entry', _('Manual Entry')
        PHONE_CALL = 'phone_call', _('Phone Call')

    booking_reference = models.CharField(_("Booking Reference"), max_length=100, db_index=True, blank=True, help_text=_("Shared reference for same tour/date"))
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        db_index=True
    )
    tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    tour_name = models.CharField(_("Tour Name"), max_length=255, help_text=_("Name of the tour at the time of booking"))
    start_date = models.DateField(_("Tour Start Date"))
    end_date = models.DateField(_("Tour End Date"))

    number_of_adults = models.PositiveIntegerField(_("Number of Adults"), default=1)
    number_of_children = models.PositiveIntegerField(_("Number of Children"), default=0)

    total_amount = models.DecimalField(_("Total Amount"), max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(_("Amount Paid"), max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(
        _("Payment Status"),
        max_length=50,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    source = models.CharField(_("Source"), max_length=20, choices=BookingSource.choices, default=BookingSource.MANUAL_ENTRY)
    
    notes = models.TextField(_("Internal Notes"), blank=True, null=True)
    booking_details_payload = models.JSONField(
        _("Booking Details Payload"), blank=True, null=True, 
        help_text=_("Raw structured data from an email or other source.")
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Auto-generate booking_reference if not provided.
        For tours with a tour_id, uses a shared reference based on tour and date.
        """
        if not self.booking_reference:
            from .reference_generator import generate_booking_reference, generate_shared_booking_reference
            
            # If we have a tour and start_date, use shared reference
            # Note: Django automatically creates a tour_id field for ForeignKey relationships.
            # This field stores the primary key (ID) of the related Tour object.
            # tour_id is accessible even when tour is None (if tour_id was set directly).
            # This allows checking for tour association before accessing the tour object.
            if self.tour_id and self.start_date:
                shared_ref = generate_shared_booking_reference(self.tour_id, self.start_date)
                self.booking_reference = shared_ref
            else:
                # Fall back to unique reference for non-tour bookings or custom bookings
                max_attempts = 10
                for attempt in range(max_attempts):
                    ref = generate_booking_reference()
                    if not Booking.objects.filter(booking_reference=ref).exists():
                        self.booking_reference = ref
                        break
                
                # If we couldn't generate a unique reference after max attempts, raise an error
                if not self.booking_reference:
                    raise ValueError(f"Failed to generate a unique booking reference after {max_attempts} attempts")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_reference} for {self.customer}"

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        ordering = ['-start_date']

    def get_total_paid(self):
        """
        Returns the total amount paid for this booking by summing all successful payments.
        """
        total_paid = self.payments.filter(
            status=Payment.PaymentStatus.SUCCESSFUL
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        return total_paid

    def update_amount_paid(self, commit=True):
        """
        Recalculates the amount_paid field by summing up all related successful payments.
        """
        self.amount_paid = self.get_total_paid()
        if commit:
            self.save(update_fields=['amount_paid'])


class Traveler(models.Model):
    """
    Represents an individual traveler associated with a booking.
    Stores detailed information for each person traveling on a tour.
    """
    class TravelerType(models.TextChoices):
        ADULT = 'adult', _('Adult')
        CHILD = 'child', _('Child')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='travelers',
        db_index=True,
        help_text=_("The booking this traveler is associated with.")
    )
    
    # Traveler Details
    name = models.CharField(_("Full Name"), max_length=255)
    age = models.PositiveIntegerField(_("Age"))
    nationality = models.CharField(_("Nationality"), max_length=100)
    gender = models.CharField(_("Gender"), max_length=20)
    id_number = models.CharField(_("ID/Passport Number"), max_length=50)
    id_document = models.FileField(
        _("ID/Passport Document"),
        upload_to='traveler_documents/%Y/%m/',
        blank=True,
        null=True,
        help_text=_("Upload a photo or scan of ID/Passport")
    )
    medical_dietary_requirements = models.TextField(
        _("Medical/Dietary Requirements"), 
        blank=True, 
        null=True,
        help_text=_("Any special medical or dietary needs.")
    )
    traveler_type = models.CharField(
        _("Traveler Type"),
        max_length=10,
        choices=TravelerType.choices,
        default=TravelerType.ADULT
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.traveler_type}) - {self.booking.booking_reference}"

    class Meta:
        verbose_name = _("Traveler")
        verbose_name_plural = _("Travelers")
        ordering = ['booking', 'traveler_type', 'name']


class Payment(models.Model):
    """
    Represents a single payment transaction made towards a booking.
    """
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SUCCESSFUL = 'successful', _('Successful')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        CREDIT_CARD = 'credit_card', _('Credit Card')
        OMARI = 'omari', _('Omari')
        OTHER = 'other', _('Other')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        db_index=True
    )
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    status = models.CharField(
        _("Payment Status"), max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(
        _("Payment Method"), max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.OTHER
    )
    transaction_reference = models.CharField(
        _("Transaction Reference"), max_length=255, blank=True, null=True,
        help_text=_("A reference from the payment provider, e.g., transaction ID.")
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of {self.amount} {self.currency} for Booking {self.booking.booking_reference}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        Override save to trigger an update on the related booking's amount_paid
        whenever a payment is successfully saved or its status changes.
        """
        super().save(*args, **kwargs)
        # If this payment is linked to a booking, update the booking's total paid amount.
        # This ensures data consistency automatically.
        if self.booking:
            self.booking.update_amount_paid(commit=True)


class TourInquiry(models.Model):
    """
    Captures an initial inquiry from a customer about a tour.
    This replaces the old SiteAssessmentRequest model.
    """
    class InquiryStatus(models.TextChoices):
        NEW = 'new', _('New')
        CONTACTED = 'contacted', _('Contacted')
        PROPOSAL_SENT = 'proposal_sent', _('Proposal Sent')
        CONVERTED = 'converted', _('Converted to Booking')
        CLOSED = 'closed', _('Closed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inquiry_reference = models.CharField(_("Inquiry Reference"), max_length=100, unique=True, db_index=True, blank=True)
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='tour_inquiries',
        db_index=True
    )
    status = models.CharField(
        _("Inquiry Status"), max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.NEW
    )
    
    lead_traveler_name = models.CharField(_("Lead Traveler Name"), max_length=255, blank=True)
    destinations = models.CharField(_("Destinations of Interest"), max_length=255, blank=True)
    preferred_dates = models.CharField(_("Preferred Travel Dates"), max_length=255, blank=True)
    number_of_travelers = models.PositiveIntegerField(_("Number of Travelers"), null=True, blank=True)
    
    notes = models.TextField(_("Customer Notes / Requirements"), blank=True)
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_inquiries'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-generate inquiry_reference if not provided."""
        if not self.inquiry_reference:
            from .reference_generator import generate_inquiry_reference
            # Keep trying until we get a unique reference
            max_attempts = 10
            for attempt in range(max_attempts):
                ref = generate_inquiry_reference()
                if not TourInquiry.objects.filter(inquiry_reference=ref).exists():
                    self.inquiry_reference = ref
                    break
            
            # If we couldn't generate a unique reference after max attempts, raise an error
            if not self.inquiry_reference:
                raise ValueError(f"Failed to generate a unique inquiry reference after {max_attempts} attempts")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inquiry {self.inquiry_reference} from {self.customer} for {self.destinations or 'a tour'}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Tour Inquiry")
        verbose_name_plural = _("Tour Inquiries")
