from django.contrib import admin
from .models import CustomerProfile, Interaction, Booking, Payment, TourInquiry

class InteractionInline(admin.TabularInline):
    """
    Inline admin for displaying recent interactions directly on the CustomerProfile page.
    This provides immediate context about recent activities.
    """
    model = Interaction
    extra = 0  # Don't show extra empty forms for new interactions
    fields = ('created_at', 'interaction_type', 'agent', 'notes_preview')
    readonly_fields = ('created_at', 'interaction_type', 'agent', 'notes_preview')
    show_change_link = True  # Allow clicking to the full interaction change form
    ordering = ('-created_at',)
    verbose_name_plural = 'Recent Interactions'

    def notes_preview(self, obj):
        """Provides a truncated preview of the interaction notes."""
        if obj.notes:
            return (obj.notes[:75] + '...') if len(obj.notes) > 75 else obj.notes
        return "No notes."
    notes_preview.short_description = "Notes Preview"

    def has_add_permission(self, request, obj=None):
        # Interactions should be added via the API or main Interaction admin, not inline.
        return False

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the CustomerProfile model.
    """
    list_display = ('__str__', 'lead_status', 'company', 'assigned_agent', 'last_interaction_date')
    list_filter = ('lead_status', 'assigned_agent', 'country', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company', 'contact__whatsapp_id', 'contact__name')
    readonly_fields = ('contact', 'created_at', 'updated_at', 'last_interaction_date')
    inlines = [InteractionInline]
    list_per_page = 25
    list_select_related = ('contact', 'assigned_agent') # Performance optimization

    fieldsets = (
        ('Primary Info', {
            'fields': ('contact', ('first_name', 'last_name'), 'email')
        }),
        ('Company & Role', {
            'fields': ('company', 'role')
        }),
        ('Sales Pipeline', {
            'fields': ('lead_status', 'potential_value', 'acquisition_source', 'assigned_agent')
        }),
        ('Location', {
            'fields': (('city', 'state_province'), ('postal_code', 'country')),
            'classes': ('collapse',) # Collapsible section
        }),
        ('Segmentation & Notes', {
            'fields': ('tags', 'notes', 'custom_attributes')
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_interaction_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    """
    Admin interface for the Interaction model.
    """
    list_display = ('__str__', 'customer', 'agent', 'interaction_type', 'created_at')
    list_filter = ('interaction_type', 'agent', 'created_at')
    search_fields = ('notes', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    readonly_fields = ('created_at',)
    list_per_page = 30
    list_select_related = ('customer', 'agent', 'customer__contact') # Performance optimization
    autocomplete_fields = ['customer', 'agent'] # Use a search-friendly widget for foreign keys

    fieldsets = (
        (None, {
            'fields': ('customer', 'agent', 'interaction_type')
        }),
        ('Details', {
            'fields': ('notes', 'created_at')
        }),
    )

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for the Booking model.
    """
    list_display = ('booking_reference', 'customer', 'tour_name', 'start_date', 'payment_status', 'total_amount', 'assigned_agent')
    list_filter = ('payment_status', 'source', 'start_date', 'assigned_agent')
    search_fields = ('booking_reference', 'tour_name', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    autocomplete_fields = ['customer', 'tour', 'assigned_agent']
    list_editable = ('payment_status',)
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Booking Core Info', {
            'fields': ('booking_reference', 'customer', 'tour', 'tour_name', 'assigned_agent')
        }),
        ('Dates & Guests', {
            'fields': (('start_date', 'end_date'), ('number_of_adults', 'number_of_children'))
        }),
        ('Financials & Source', {
            'fields': (('total_amount', 'amount_paid'), 'payment_status', 'source')
        }),
        ('Additional Details', {
            'fields': ('notes', 'booking_details_payload'),
            'classes': ('collapse',)
        }),
    )
    list_select_related = ('customer', 'tour', 'assigned_agent')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'booking__booking_reference', 'transaction_reference')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['booking']

@admin.register(TourInquiry)
class TourInquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'destination', 'status', 'assigned_agent', 'created_at')
    list_filter = ('status', 'assigned_agent', 'created_at')
    search_fields = ('destination', 'notes', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['customer', 'assigned_agent']