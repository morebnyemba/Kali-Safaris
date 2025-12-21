from django.contrib import admin
from .models import OmariTransaction, OmariConfig


@admin.register(OmariConfig)
class OmariConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_production', 'created_at', 'updated_at')
    list_filter = ('is_active', 'is_production', 'created_at')
    search_fields = ('name', 'base_url')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuration Details', {
            'fields': ('name', 'is_active', 'is_production')
        }),
        ('API Credentials', {
            'fields': ('base_url', 'merchant_key'),
            'description': 'Enter the Omari Merchant API credentials. Keep these secure!'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion if there are multiple configs
        if obj and obj.is_active:
            # Don't allow deletion of active config
            return False
        return super().has_delete_permission(request, obj)


@admin.register(OmariTransaction)
class OmariTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'msisdn', 'amount', 'currency', 'status', 'otp_reference', 'created_at', 'completed_at')
    list_filter = ('status', 'currency', 'channel', 'created_at')
    search_fields = ('reference', 'msisdn', 'payment_reference', 'debit_reference', 'otp_reference')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'otp_requested_at', 'completed_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('reference', 'msisdn', 'amount', 'currency', 'channel')
        }),
        ('OTP Flow', {
            'fields': ('otp_reference', 'otp_requested_at')
        }),
        ('Payment Completion', {
            'fields': ('payment_reference', 'debit_reference', 'status', 'response_code', 'response_message', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Transactions created via API only
        return False
