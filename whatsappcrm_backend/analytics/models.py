"""
Analytics models for tracking conversational flow performance.

Tracks user interactions, completion rates, errors, and timing metrics
to enable data-driven optimization of conversational flows.
"""

from django.db import models
from django.utils import timezone
from meta_integration.models import Contact


class FlowSession(models.Model):
    """
    Represents a complete user session through a conversational flow.
    
    Tracks the entire journey from flow start to completion or abandonment,
    including context and outcome.
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('error', 'Error'),
    ]
    
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='flow_sessions',
        help_text="User who initiated this flow session"
    )
    flow_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the conversational flow"
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the flow session started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the flow session completed"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text="Current status of the flow session"
    )
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flow context data for analysis"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if flow failed"
    )
    
    class Meta:
        db_table = 'analytics_flow_session'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['flow_name', 'status']),
            models.Index(fields=['started_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.flow_name} - {self.contact} - {self.status}"
    
    @property
    def duration_seconds(self):
        """Calculate session duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (timezone.now() - self.started_at).total_seconds()
    
    def mark_completed(self):
        """Mark the session as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_abandoned(self):
        """Mark the session as abandoned."""
        self.status = 'abandoned'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_error(self, error_message):
        """Mark the session as errored."""
        self.status = 'error'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at'])


class FlowStepEvent(models.Model):
    """
    Represents a single step interaction within a flow session.
    
    Tracks individual steps for funnel analysis, error tracking,
    and time-per-step metrics.
    """
    
    ACTION_CHOICES = [
        ('entered', 'Entered'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
        ('retry', 'Retry'),
    ]
    
    session = models.ForeignKey(
        FlowSession,
        on_delete=models.CASCADE,
        related_name='step_events',
        help_text="Parent flow session"
    )
    step_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the flow step"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Action taken at this step"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this event occurred"
    )
    time_spent = models.FloatField(
        null=True,
        blank=True,
        help_text="Time spent on this step (seconds)"
    )
    input_value = models.TextField(
        blank=True,
        help_text="User input at this step"
    )
    output_value = models.TextField(
        blank=True,
        help_text="System output at this step"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if step failed"
    )
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retries for this step"
    )
    
    class Meta:
        db_table = 'analytics_flow_step_event'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'step_name']),
            models.Index(fields=['step_name', 'action']),
        ]
    
    def __str__(self):
        return f"{self.session.flow_name} - {self.step_name} - {self.action}"


class FlowMetricSnapshot(models.Model):
    """
    Periodic snapshot of flow metrics for trend analysis.
    
    Pre-calculated metrics stored daily/weekly for performance.
    """
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    flow_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the flow"
    )
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        help_text="Snapshot period"
    )
    period_start = models.DateTimeField(
        db_index=True,
        help_text="Start of the period"
    )
    period_end = models.DateTimeField(
        help_text="End of the period"
    )
    
    # Completion metrics
    total_sessions = models.IntegerField(
        default=0,
        help_text="Total sessions started"
    )
    completed_sessions = models.IntegerField(
        default=0,
        help_text="Sessions completed successfully"
    )
    abandoned_sessions = models.IntegerField(
        default=0,
        help_text="Sessions abandoned"
    )
    error_sessions = models.IntegerField(
        default=0,
        help_text="Sessions ending in error"
    )
    
    # Time metrics
    avg_duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Average session duration"
    )
    median_duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Median session duration"
    )
    
    # Error metrics
    total_errors = models.IntegerField(
        default=0,
        help_text="Total errors encountered"
    )
    error_rate = models.FloatField(
        default=0.0,
        help_text="Percentage of sessions with errors"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this snapshot was created"
    )
    
    class Meta:
        db_table = 'analytics_flow_metric_snapshot'
        ordering = ['-period_start']
        unique_together = [['flow_name', 'period', 'period_start']]
        indexes = [
            models.Index(fields=['flow_name', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.flow_name} - {self.period} - {self.period_start.date()}"
    
    @property
    def completion_rate(self):
        """Calculate completion rate as percentage."""
        if self.total_sessions == 0:
            return 0.0
        return (self.completed_sessions / self.total_sessions) * 100
    
    @property
    def abandonment_rate(self):
        """Calculate abandonment rate as percentage."""
        if self.total_sessions == 0:
            return 0.0
        return (self.abandoned_sessions / self.total_sessions) * 100
