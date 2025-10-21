from django.contrib import admin
from django.utils import timezone
from .models import AIProvider

@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_active', 'rate_limit_status', 'rate_limit_reset_time', 'updated_at')
    list_filter = ('provider', 'is_active')
    search_fields = ('provider',)
    readonly_fields = ('rate_limit_limit', 'rate_limit_remaining', 'rate_limit_reset_time', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('provider', 'api_key', 'is_active')}),
        ('Rate Limit Status (Read-Only)', {
            'fields': ('rate_limit_limit', 'rate_limit_remaining', 'rate_limit_reset_time'),
            'classes': ('collapse',),
            'description': 'This information is updated automatically after an API call.'
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)})
    )
    ordering = ('provider',)

    def rate_limit_status(self, obj):
        if obj.rate_limit_limit is not None and obj.rate_limit_remaining is not None:
            return f"{obj.rate_limit_remaining} / {obj.rate_limit_limit}"
        return "N/A"
    rate_limit_status.short_description = "Requests Remaining"