from django.contrib import admin
from .models import DailyStat

@admin.register(DailyStat)
class DailyStatAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'new_contacts', 'messages_received', 'messages_sent', 
        'new_orders_count', 'won_orders_count', 'revenue', 'last_updated'
    )
    list_filter = ('date',)
    ordering = ('-date',)
    readonly_fields = ('date', 'last_updated')

    def has_add_permission(self, request):
        return False # These should only be created by the system

    def has_change_permission(self, request, obj=None):
        return False # And not changed manually
