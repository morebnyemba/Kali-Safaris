from django.contrib import admin
from django.utils.html import format_html

from .models import GalleryImage, Tour, SeasonalTourPrice

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """
    Admin interface for the Tour model.
    """
    list_display = ('name', 'category', 'location', 'get_duration_display', 'base_price', 'is_active')
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


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """
    Photos on the website's gallery page. Deleting an entry also deletes its file.
    """
    list_display = ('thumbnail', '__str__', 'category', 'year', 'sort_order', 'is_active')
    list_display_links = ('thumbnail', '__str__')
    list_filter = ('category', 'is_active', 'year')
    search_fields = ('caption',)
    list_editable = ('category', 'year', 'sort_order', 'is_active')
    readonly_fields = ('preview',)
    fields = ('image', 'preview', 'category', 'caption', 'year', 'sort_order', 'is_active')

    @admin.display(description='Photo')
    def thumbnail(self, obj):
        return format_html('<img src="{}" style="height:56px;width:84px;object-fit:cover;border-radius:6px">', obj.file_path() + '/') if obj.pk and obj.image else '—'

    @admin.display(description='Preview')
    def preview(self, obj):
        return format_html('<img src="{}" style="max-height:240px;border-radius:8px">', obj.file_path() + '/') if obj.pk and obj.image else '—'
