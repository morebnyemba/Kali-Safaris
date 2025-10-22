from django.contrib import admin
from .models import Tour

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """
    Admin interface for the Tour model.
    """
    list_display = ('name', 'category', 'location', 'duration_days', 'base_price', 'is_active')
    list_filter = ('category', 'is_active', 'location')
    search_fields = ('name', 'description', 'location')
    list_editable = ('base_price', 'is_active')
    fieldsets = (
        ('Core Information', {
            'fields': ('name', 'category', 'description', 'image')
        }),
        ('Details & Pricing', {
            'fields': ('location', 'duration_days', 'base_price', 'is_active')
        }),
    )
