"""
Analytics reporting utilities for flow performance analysis.
"""

from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import FlowSession, FlowStepEvent, FlowMetricSnapshot


def get_flow_completion_rate(flow_name, days=7):
    """
    Calculate completion rate for a flow over the last N days.
    
    Args:
        flow_name: Name of the flow
        days: Number of days to look back
    
    Returns:
        dict with completion metrics
    """
    since = timezone.now() - timedelta(days=days)
    sessions = FlowSession.objects.filter(
        flow_name=flow_name,
        started_at__gte=since
    )
    
    total = sessions.count()
    if total == 0:
        return {'completion_rate': 0, 'total': 0}
    
    completed = sessions.filter(status='completed').count()
    abandoned = sessions.filter(status='abandoned').count()
    errors = sessions.filter(status='error').count()
    
    return {
        'total': total,
        'completed': completed,
        'abandoned': abandoned,
        'errors': errors,
        'completion_rate': (completed / total) * 100,
        'abandonment_rate': (abandoned / total) * 100,
        'error_rate': (errors / total) * 100,
    }


def get_step_funnel(flow_name, days=7):
    """
    Get funnel analysis showing drop-off at each step.
    
    Args:
        flow_name: Name of the flow
        days: Number of days to look back
    
    Returns:
        list of dicts with step-by-step funnel data
    """
    since = timezone.now() - timedelta(days=days)
    sessions = FlowSession.objects.filter(
        flow_name=flow_name,
        started_at__gte=since
    )
    
    # Get all steps with counts
    steps = FlowStepEvent.objects.filter(
        session__in=sessions,
        action='entered'
    ).values('step_name').annotate(
        count=Count('id')
    ).order_by('step_name')
    
    total_sessions = sessions.count()
    funnel = []
    
    for step in steps:
        funnel.append({
            'step_name': step['step_name'],
            'users': step['count'],
            'percentage': (step['count'] / total_sessions) * 100 if total_sessions > 0 else 0
        })
    
    return funnel


def get_error_analysis(flow_name, days=7):
    """
    Analyze errors by step and frequency.
    
    Args:
        flow_name: Name of the flow
        days: Number of days to look back
    
    Returns:
        list of dicts with error analysis
    """
    since = timezone.now() - timedelta(days=days)
    sessions = FlowSession.objects.filter(
        flow_name=flow_name,
        started_at__gte=since
    )
    
    errors = FlowStepEvent.objects.filter(
        session__in=sessions,
        action='error'
    ).values('step_name', 'error_message').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return list(errors)


def generate_daily_snapshot(flow_name, date):
    """
    Generate a daily metric snapshot for a flow.
    
    Args:
        flow_name: Name of the flow
        date: Date for the snapshot
    
    Returns:
        FlowMetricSnapshot instance
    """
    period_start = timezone.make_aware(
        timezone.datetime.combine(date, timezone.datetime.min.time())
    )
    period_end = period_start + timedelta(days=1)
    
    sessions = FlowSession.objects.filter(
        flow_name=flow_name,
        started_at__gte=period_start,
        started_at__lt=period_end
    )
    
    total = sessions.count()
    if total == 0:
        return None
    
    completed = sessions.filter(status='completed').count()
    abandoned = sessions.filter(status='abandoned').count()
    errors = sessions.filter(status='error').count()
    
    # Calculate average duration for completed sessions
    completed_sessions = sessions.filter(status='completed', completed_at__isnull=False)
    durations = [s.duration_seconds for s in completed_sessions]
    avg_duration = sum(durations) / len(durations) if durations else None
    
    # Calculate error metrics
    total_errors = FlowStepEvent.objects.filter(
        session__in=sessions,
        action='error'
    ).count()
    error_rate = (total_errors / total) * 100 if total > 0 else 0
    
    snapshot, created = FlowMetricSnapshot.objects.update_or_create(
        flow_name=flow_name,
        period='daily',
        period_start=period_start,
        defaults={
            'period_end': period_end,
            'total_sessions': total,
            'completed_sessions': completed,
            'abandoned_sessions': abandoned,
            'error_sessions': errors,
            'avg_duration_seconds': avg_duration,
            'total_errors': total_errors,
            'error_rate': error_rate,
        }
    )
    
    return snapshot
