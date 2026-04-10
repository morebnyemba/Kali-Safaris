from django.contrib import admin
from .models import CBZConfig, CBZTransaction


@admin.register(CBZConfig)
class CBZConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'mode', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'mode', 'created_at')
    search_fields = ('name', 'portal_url')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Configuration Details', {
            'fields': ('name', 'is_active', 'mode')
        }),
        ('iVeri API Credentials', {
            'fields': ('portal_url', 'certificate_id', 'application_id'),
            'description': (
                'Enter the iVeri Gateway credentials obtained from the CBZ/iVeri backoffice. '
                'Keep these secure! CertificateID and ApplicationID are GUIDs.'
            ),
        }),
        ('Callback Configuration', {
            'fields': ('callback_url',),
            'classes': ('collapse',),
            'description': 'Optional: URL for iVeri to send out-of-band transaction notifications.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of active config
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(CBZTransaction)
class CBZTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'merchant_reference', 'payment_type', 'amount', 'currency',
        'status', 'msisdn', 'masked_pan', 'created_at', 'completed_at',
    )
    list_filter = ('status', 'payment_type', 'currency', 'created_at')
    search_fields = (
        'merchant_reference', 'transaction_index', 'msisdn',
        'masked_pan', 'authorisation_code', 'request_id',
    )
    readonly_fields = (
        'merchant_reference', 'created_at', 'updated_at', 'completed_at',
    )

    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'merchant_reference', 'payment_type', 'command',
                'amount', 'currency', 'booking',
            ),
        }),
        ('Customer Details', {
            'fields': ('msisdn', 'masked_pan'),
        }),
        ('iVeri Response', {
            'fields': (
                'transaction_index', 'request_id', 'authorisation_code',
                'status', 'result_code', 'result_description',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        # Transactions created via API only
        return False
