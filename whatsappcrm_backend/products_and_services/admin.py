from django.contrib import admin
from .models import Tour, SeasonalTourPrice, TourTimeSlot


class TourTimeSlotInline(admin.TabularInline):
    model = TourTimeSlot
    extra = 1
    fields = ('start_time', 'end_time', 'label', 'is_active')
    verbose_name_plural = 'Time slots — customers must pick one when booking (leave empty for trips with no fixed time)'


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """
    Admin interface for the Tour model.
    """
    list_display = ('name', 'category', 'location', 'get_duration_display', 'get_time_slots', 'base_price', 'is_active')
    list_filter = ('category', 'is_active', 'location', 'duration_unit')
    search_fields = ('name', 'description', 'location')
    list_editable = ('base_price', 'is_active')
    fieldsets = (
        ('Core Information', {
            'fields': ('name', 'category', 'description', 'image')
        }),
        ('Duration', {
            'fields': (('duration_value', 'duration_unit'),),
            'description': 'Specify the tour duration in hours or days.'
        }),
        ('Details & Pricing', {
            'fields': ('location', 'base_price', 'is_active')
        }),
    )
    
    inlines = [TourTimeSlotInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('time_slots')

    @admin.display(description='Time slots')
    def get_time_slots(self, obj):
        return ', '.join(s.time_range for s in obj.active_time_slots()) or '—'

    def get_duration_display(self, obj):
        """Display duration in a human-readable format."""
        return obj.get_duration_display_text()
    get_duration_display.short_description = 'Duration'
    get_duration_display.admin_order_field = 'duration_value'


@admin.register(SeasonalTourPrice)
class SeasonalTourPriceAdmin(admin.ModelAdmin):
    """
    Admin interface for the SeasonalTourPrice model.
    """
    list_display = ('tour', 'start_date', 'end_date', 'price_per_adult', 'price_per_child', 'is_active')
    list_filter = ('is_active', 'tour')
    search_fields = ('tour__name',)
    list_editable = ('is_active',)
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Tour & Period', {
            'fields': ('tour', 'start_date', 'end_date', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_per_adult', 'price_per_child')
        }),
    )
