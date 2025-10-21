from django.contrib import admin
from .models import Product, ProductCategory
from django.utils.html import format_html

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for the generic Product model.
    """
    list_display = ('name', 'sku', 'product_type', 'category', 'price', 'is_active')
    list_filter = ('product_type', 'is_active', 'category', 'license_type')
    search_fields = ('name', 'sku', 'description')
    list_editable = ('price', 'is_active')
    autocomplete_fields = ('category', 'parent_product')
    filter_horizontal = ('compatible_products',)
    fieldsets = (
        ('Core Information', {
            'fields': ('name', 'sku', 'product_type', 'category', 'description')
        }),
        ('Pricing & Availability', {
            'fields': (('price', 'currency'), 'is_active')
        }),
        ('Software & Relationships', {
            'fields': ('license_type', 'dedicated_flow_name', 'parent_product', 'compatible_products'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('image',)
        }),
    )

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Product Categories.
    """
    list_display = ('name', 'parent', 'description')
    search_fields = ('name',)
    autocomplete_fields = ('parent',)
