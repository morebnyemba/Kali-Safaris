import logging

from django import forms
from django.contrib import admin, messages

from .models import CBZConfig, CBZTransaction
from .services import build_certificate_client_from_settings


logger = logging.getLogger(__name__)


class CBZConfigAdminForm(forms.ModelForm):
    auto_generate_certificate = forms.BooleanField(
        required=False,
        help_text='Generate a new CertificateID after saving this configuration.',
    )
    auto_renew_certificate = forms.BooleanField(
        required=False,
        help_text='Renew the current CertificateID after saving this configuration.',
    )

    class Meta:
        model = CBZConfig
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('auto_generate_certificate') and cleaned_data.get('auto_renew_certificate'):
            raise forms.ValidationError('Select only one certificate action per save.')
        return cleaned_data


@admin.register(CBZConfig)
class CBZConfigAdmin(admin.ModelAdmin):
    form = CBZConfigAdminForm
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
                'CertificateID is required for REST payments, and may be generated through the SOAP certificate lifecycle if not yet issued.'
            ),
        }),
        ('COPYandPAY Credentials', {
            'fields': (
                'copyandpay_base_url',
                'copyandpay_entity_id',
                'copyandpay_bearer_token',
                'copyandpay_test_mode',
                'copyandpay_brands',
                'copyandpay_widget_integrity',
            ),
            'description': (
                'Store COPYandPAY credentials in the database. '
                'When set here on the active configuration, these values take precedence over environment variables.'
            ),
        }),
        ('Certificate Lifecycle', {
            'fields': ('auto_generate_certificate', 'auto_renew_certificate'),
            'description': (
                'Optional admin actions. Use generate for the initial CertificateID or renew when the existing certificate is rotating. '
                'These actions run after the configuration record is saved.'
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        auto_generate = form.cleaned_data.get('auto_generate_certificate')
        auto_renew = form.cleaned_data.get('auto_renew_certificate')
        if not auto_generate and not auto_renew:
            return

        action_label = 'generation' if auto_generate else 'renewal'

        try:
            client = build_certificate_client_from_settings(obj)
            if auto_generate:
                result = client.generate_certificate_id()
            else:
                result = client.renew_certificate_id(certificate_id=obj.certificate_id or '')

            obj.certificate_id = result['certificate_id']
            obj.save(update_fields=['certificate_id', 'updated_at'])
            self.message_user(
                request,
                f"CertificateID {action_label} completed successfully.",
                level=messages.SUCCESS,
            )
        except Exception as exc:
            logger.exception(
                "CBZ admin certificate %s failed | config_id=%s",
                action_label,
                obj.pk,
            )
            self.message_user(
                request,
                f"Configuration saved, but certificate {action_label} failed: {exc}",
                level=messages.ERROR,
            )


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
