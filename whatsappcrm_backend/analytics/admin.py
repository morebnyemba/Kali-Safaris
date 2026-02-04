"""
Django admin configuration for analytics models.
"""

from django.contrib import admin
from django.db.models import Avg, Count
from django.utils.html import format_html
from .models import FlowSession, FlowStepEvent, FlowMetricSnapshot


@admin.register(FlowSession)
class FlowSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'flow_name', 'contact', 'status', 'started_at', 'duration_display', 'step_count']
    list_filter = ['status', 'flow_name', 'started_at']
    search_fields = ['contact__name', 'flow_name']
    readonly_fields = ['started_at', 'completed_at', 'duration_seconds']
    date_hierarchy = 'started_at'
    
    def duration_display(self, obj):
        """Display duration in human-readable format."""
        duration = obj.duration_seconds
        if duration < 60:
            return f"{duration:.1f}s"
        return f"{duration/60:.1f}m"
    duration_display.short_description = 'Duration'
    
    def step_count(self, obj):
        """Count of steps in this session."""
        return obj.step_events.count()
    step_count.short_description = 'Steps'


@admin.register(FlowStepEvent)
class FlowStepEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'step_name', 'action', 'timestamp', 'time_spent', 'retry_count']
    list_filter = ['action', 'step_name', 'timestamp']
    search_fields = ['session__flow_name', 'step_name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(FlowMetricSnapshot)
class FlowMetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ['flow_name', 'period', 'period_start', 'completion_rate_display', 'total_sessions', 'avg_duration_display']
    list_filter = ['period', 'flow_name', 'period_start']
    readonly_fields = ['created_at', 'completion_rate', 'abandonment_rate']
    date_hierarchy = 'period_start'
    
    def completion_rate_display(self, obj):
        """Display completion rate with color coding."""
        rate = obj.completion_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    completion_rate_display.short_description = 'Completion Rate'
    
    def avg_duration_display(self, obj):
        """Display average duration in human-readable format."""
        if obj.avg_duration_seconds:
            duration = obj.avg_duration_seconds
            if duration < 60:
                return f"{duration:.1f}s"
            return f"{duration/60:.1f}m"
        return "-"
    avg_duration_display.short_description = 'Avg Duration'
