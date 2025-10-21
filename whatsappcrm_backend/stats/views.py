# views.py
# whatsappcrm_backend/stats/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Avg, Q, Sum
from django.db.models.functions import TruncDate, TruncDay, TruncWeek, TruncMonth, TruncHour
from django.utils.dateparse import parse_date

# Import models from your other apps
from conversations.models import Contact, Message
from flows.models import Flow, ContactFlowState
from meta_integration.models import MetaAppConfig
from customer_data.models import Payment

import logging
logger = logging.getLogger(__name__)

class DashboardSummaryStatsAPIView(APIView):
    """
    API View to provide a summary of statistics for the dashboard.
    All timestamp comparisons are timezone-aware.
    """
    permission_classes = [permissions.IsAuthenticated] # Or IsAdminUser if preferred

    def _get_time_ranges(self):
        """Helper to establish common time ranges for queries."""
        now = timezone.now()
        return {
            'now': now,
            'today_start': now.replace(hour=0, minute=0, second=0, microsecond=0),
            'today_end': now.replace(hour=23, minute=59, second=59, microsecond=999999),
            'twenty_four_hours_ago': now - timedelta(hours=24),
            'seven_days_ago_start_of_day': now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6),
            'four_hours_ago': now - timedelta(hours=4)
        }

    def _get_card_stats(self, time_ranges):
        """Calculate the primary statistics for the dashboard cards."""
        meta_configs_total = MetaAppConfig.objects.count()
        active_meta_config_obj = MetaAppConfig.objects.filter(is_active=True).first()

        new_contacts_today_count = Contact.objects.filter(
            first_seen__gte=time_ranges['today_start'], 
            first_seen__lte=time_ranges['today_end']
        ).count()

        messages_sent_24h_count = Message.objects.filter(
            direction='out', 
            timestamp__gte=time_ranges['twenty_four_hours_ago']
        ).count()

        active_conversations_count = Message.objects.filter(
            timestamp__gte=time_ranges['four_hours_ago']
        ).values('contact_id').distinct().count()

        return {
            'active_conversations_count': active_conversations_count,
            'new_contacts_today': new_contacts_today_count,
            'total_contacts': Contact.objects.count(),
            'messages_sent_24h': messages_sent_24h_count,
            'messages_received_24h': Message.objects.filter(direction='in', timestamp__gte=time_ranges['twenty_four_hours_ago']).count(),
            'meta_configs_total': meta_configs_total,
            'meta_config_active_name': active_meta_config_obj.name if active_meta_config_obj else "None",
            'pending_human_handovers': Contact.objects.filter(needs_human_intervention=True).count(),
        }

    def _get_flow_insights(self, time_ranges):
        """Calculate statistics related to flow performance."""
        avg_steps_data = Flow.objects.annotate(num_steps=Count('steps')).filter(num_steps__gt=0).aggregate(avg_val=Avg('num_steps'))
        
        # A "completion" is defined as a flow state reaching an 'end_flow' step today.
        flow_completions_today = ContactFlowState.objects.filter(
            current_step__step_type='end_flow',
            last_updated_at__gte=time_ranges['today_start'],
            last_updated_at__lte=time_ranges['today_end']
        ).count()
        
        return {
            'active_flows_count': Flow.objects.filter(is_active=True).count(),
            'total_flows_count': Flow.objects.count(),
            'flow_completions_today': flow_completions_today,
            'avg_steps_per_flow': round(avg_steps_data['avg_val'], 1) if avg_steps_data['avg_val'] else 0.0,
        }
    
    def _get_chart_data(self, time_ranges, flow_insights):
        """Prepare data structures for frontend charts."""
        message_trends = Message.objects.filter(timestamp__gte=time_ranges['seven_days_ago_start_of_day'])\
            .annotate(date=TruncDate('timestamp'))\
            .values('date')\
            .annotate(incoming_count=Count('id', filter=Q(direction='in')),
                      outgoing_count=Count('id', filter=Q(direction='out')))\
            .order_by('date')
        
        total_flows_started_today = ContactFlowState.objects.filter(started_at__gte=time_ranges['today_start']).count()
        automated_resolution_rate = 0.0
        if total_flows_started_today > 0:
            automated_resolution_rate = flow_insights['flow_completions_today'] / total_flows_started_today

        return {
            'conversation_trends': [
                {
                    "date": item['date'].strftime('%Y-%m-%d'), 
                    "incoming_messages": item['incoming_count'],
                    "outgoing_messages": item['outgoing_count'],
                    "total_messages": item['incoming_count'] + item['outgoing_count']
                }
                for item in message_trends
            ],
            'bot_performance': {
                "automated_resolution_rate": automated_resolution_rate,
                "avg_bot_response_time_seconds": 0.0, # Placeholder: This requires more complex logic to calculate accurately.
                "total_incoming_messages_processed": Message.objects.filter(direction='in').count(),
            }
        }

    def _get_activity_log(self):
        """Compile a list of recent, notable activities."""
        recent_new_contacts = Contact.objects.order_by('-first_seen')[:3]
        recent_updated_flows = Flow.objects.order_by('-updated_at')[:2]
        recent_handovers = Contact.objects.filter(needs_human_intervention=True).order_by('-intervention_requested_at')[:2]
        
        activity_log_for_frontend = []
        for contact_activity in recent_new_contacts:
            activity_log_for_frontend.append({
                "id": f"contact_new_{contact_activity.id}",
                "text": f"New contact: {contact_activity.name or contact_activity.whatsapp_id}",
                "timestamp": contact_activity.first_seen.isoformat(),
                "iconName": "FiUsers",
                "iconColor": "text-emerald-500"
            })
        for flow_activity in recent_updated_flows:
            activity_log_for_frontend.append({
                "id": f"flow_update_{flow_activity.id}",
                "text": f"Flow '{flow_activity.name}' was updated.",
                "timestamp": flow_activity.updated_at.isoformat(),
                "iconName": "FiZap",
                "iconColor": "text-purple-500"
            })
        for handover in recent_handovers:
            activity_log_for_frontend.append({
                "id": f"handover_{handover.id}",
                "text": f"Human handover requested for {handover.name or handover.whatsapp_id}.",
                "timestamp": handover.intervention_requested_at.isoformat(),
                "iconName": "FiAlertCircle",
                "iconColor": "text-red-500"
            })

        activity_log_for_frontend.sort(key=lambda x: x['timestamp'], reverse=True)
        return activity_log_for_frontend[:5]

    def get(self, request, format=None):
        time_ranges = self._get_time_ranges()
        
        stats_cards = self._get_card_stats(time_ranges)
        flow_insights = self._get_flow_insights(time_ranges)
        charts_data = self._get_chart_data(time_ranges, flow_insights)
        recent_activity_log = self._get_activity_log()

        data = {
            'stats_cards': stats_cards,
            'flow_insights': flow_insights,
            'charts_data': charts_data,
            'recent_activity_log': recent_activity_log,
            'system_status': 'Operational'
        }

        return Response(data, status=status.HTTP_200_OK)


# --- Robust, Filterable Analytics Endpoints ---

class BaseAnalyticsView(APIView):
    """
    Base view for analytics endpoints to handle common date filtering.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_date_range(self, request):
        """
        Parses 'start_date' and 'end_date' from query parameters.
        Defaults to the last 30 days if not provided.
        Returns a timezone-aware start and end datetime.
        """
        now = timezone.now()
        end_date_str = request.query_params.get('end_date')
        start_date_str = request.query_params.get('start_date')

        if end_date_str and (end_date := parse_date(end_date_str)):
            # Set to end of the day
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        else:
            end_datetime = now

        if start_date_str and (start_date := parse_date(start_date_str)):
            # Set to start of the day
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        else:
            # Default to 30 days before end_datetime
            start_datetime = end_datetime - timedelta(days=30)
            
        return start_datetime, end_datetime

class FinancialStatsAPIView(BaseAnalyticsView):
    """
    Provides detailed financial statistics with filtering and grouping.
    Query Parameters:
    - `start_date` (YYYY-MM-DD): Start of the date range. Defaults to 30 days ago.
    - `end_date` (YYYY-MM-DD): End of the date range. Defaults to now.
    - `group_by` (day, week, month, payment_method): How to aggregate the data. Defaults to 'day'.
    """
    def get(self, request, format=None):
        start_datetime, end_datetime = self.get_date_range(request)
        group_by = request.query_params.get('group_by', 'day')

        base_queryset = Payment.objects.filter(status='successful', created_at__range=(start_datetime, end_datetime))

        total_giving = base_queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_transactions = base_queryset.count()
        average_transaction = total_giving / total_transactions if total_transactions > 0 else 0

        if group_by in ['day', 'week', 'month']:
            trunc_func = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth}[group_by]
            trends = base_queryset.annotate(period=trunc_func('created_at')).values('period').annotate(total_amount=Sum('amount'), count=Count('id')).order_by('period')
            date_format = '%Y-%m-%d' if group_by != 'month' else '%Y-%m'
            trends_data = [{'period': item['period'].strftime(date_format), 'total_amount': item['total_amount'], 'transactions': item['count']} for item in trends]
        else: # group by payment_method
            trends = base_queryset.values('payment_method').annotate(total_amount=Sum('amount'), count=Count('id')).order_by('-total_amount')
            trends_data = [{'payment_method': item['payment_method'], 'total_amount': item['total_amount'], 'transactions': item['count']} for item in trends]

        return Response({
            'summary': {
                'total_giving': total_giving, 'total_transactions': total_transactions,
                'average_transaction_value': average_transaction,
                'date_range': {'start': start_datetime.isoformat(), 'end': end_datetime.isoformat()}
            },
            'group_by': group_by, 'trends': trends_data
        })

class EngagementStatsAPIView(BaseAnalyticsView):
    """
    Provides detailed user engagement statistics.
    """
    def get(self, request, format=None):
        start_datetime, end_datetime = self.get_date_range(request)
        
        active_contacts_count = Message.objects.filter(timestamp__range=(start_datetime, end_datetime)).values('contact_id').distinct().count()
        flows_started_count = ContactFlowState.objects.filter(started_at__range=(start_datetime, end_datetime)).count()
        handovers_requested_count = Contact.objects.filter(needs_human_intervention=True, intervention_requested_at__range=(start_datetime, end_datetime)).count()

        return Response({
            'active_contacts_in_period': active_contacts_count, 'flows_started_in_period': flows_started_count,
            'handovers_requested_in_period': handovers_requested_count,
            'date_range': {'start': start_datetime.isoformat(), 'end': end_datetime.isoformat()}
        })

class MessageVolumeAPIView(BaseAnalyticsView):
    """
    Provides message volume statistics.
    """
    def get(self, request, format=None):
        start_datetime, end_datetime = self.get_date_range(request)
        group_by = request.query_params.get('group_by', 'day')

        trunc_func, date_format = (TruncHour, '%Y-%m-%dT%H:00:00') if group_by == 'hour' else (TruncDay, '%Y-%m-%d')

        message_trends = Message.objects.filter(timestamp__range=(start_datetime, end_datetime))\
            .annotate(period=trunc_func('timestamp')).values('period')\
            .annotate(incoming=Count('id', filter=Q(direction='in')), outgoing=Count('id', filter=Q(direction='out'))).order_by('period')
        
        trends_data = [{'period': item['period'].strftime(date_format), 'incoming_messages': item['incoming'], 'outgoing_messages': item['outgoing'], 'total_messages': item['incoming'] + item['outgoing']} for item in message_trends]

        return Response({'date_range': {'start': start_datetime.isoformat(), 'end': end_datetime.isoformat()}, 'group_by': group_by, 'volume_per_period': trends_data})
