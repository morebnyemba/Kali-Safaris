# stats/services.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.db.models import Sum
from django.db.models.functions import TruncDate

from conversations.models import Contact, Message
from customer_data.models import Order, InstallationRequest, SiteAssessmentRequest

def get_stats_card_data():
    """Calculates and returns data for the main stats cards."""
    now = timezone.now()
    twenty_four_hours_ago = now - timedelta(hours=24)
    four_hours_ago = now - timedelta(hours=4)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate value of open orders
    open_orders_value = Order.objects.filter(
        stage__in=['prospecting', 'qualification', 'proposal', 'negotiation']
    ).aggregate(total_value=Sum('amount'))['total_value'] or 0

    total_revenue = Order.objects.filter(stage='closed_won').aggregate(total=Sum('amount'))['total'] or 0
    revenue_today = Order.objects.filter(stage='closed_won', updated_at__gte=today_start).aggregate(total=Sum('amount'))['total'] or 0

    return {
        'messages_sent_24h': Message.objects.filter(direction='out', timestamp__gte=twenty_four_hours_ago).count(),
        'messages_received_24h': Message.objects.filter(direction='in', timestamp__gte=twenty_four_hours_ago).count(),
        'active_conversations_count': Message.objects.filter(timestamp__gte=four_hours_ago).values('contact_id').distinct().count(),
        'new_contacts_today': Contact.objects.filter(first_seen__gte=today_start).count(),
        'total_contacts': Contact.objects.count(),
        'pending_human_handovers': Contact.objects.filter(needs_human_intervention=True).count(),
        
        # Order & Revenue Stats
        'open_orders_value': f"{open_orders_value:,.2f}",
        'new_orders_today': Order.objects.filter(created_at__gte=today_start).count(),
        'total_open_orders': Order.objects.filter(stage__in=['prospecting', 'qualification', 'proposal', 'negotiation']).count(),
        'total_revenue': f"{total_revenue:,.2f}",
        'revenue_today': f"{revenue_today:,.2f}",

        # Installation & Assessment Stats
        'pending_installations': InstallationRequest.objects.filter(status='pending').count(),
        'completed_installations': InstallationRequest.objects.filter(status='completed').count(),
        'pending_assessments': SiteAssessmentRequest.objects.filter(status='pending').count(),
    }

def get_conversation_trends_chart_data():
    """Calculates and returns data for the conversation trends chart."""
    now = timezone.now()
    seven_days_ago_start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
    
    message_trends = Message.objects.filter(timestamp__gte=seven_days_ago_start_of_day)\
        .annotate(date=TruncDate('timestamp'))\
        .values('date')\
        .annotate(
            incoming_count=Count('id', filter=Q(direction='in')),
            outgoing_count=Count('id', filter=Q(direction='out'))
        )\
        .order_by('date')
    
    return [
        {
            "date": item['date'].strftime('%Y-%m-%d'), 
            "incoming_messages": item['incoming_count'],
            "outgoing_messages": item['outgoing_count'],
            "total_messages": item['incoming_count'] + item['outgoing_count']
        }
        for item in message_trends
    ]

def get_bot_performance_chart_data():
    """Calculates and returns data for the bot performance chart."""
    # NOTE: This query is inefficient as it counts all messages every time.
    # For a production system, consider using a caching layer (like Redis)
    # or a separate analytics model that is updated with atomic increments.
    return {
        "total_incoming_messages_processed": Message.objects.filter(direction='in').count(),
    }