from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db import models
from customer_data.models import Order, InstallationRequest, SiteAssessmentRequest
from conversations.models import Message
from customer_data.models import CustomerProfile

class AnalyticsReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Parse date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            if start_date:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = timezone.now().date() - timedelta(days=30)
            if end_date:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = timezone.now().date()
        except Exception:
            return Response({'detail': 'Invalid date format.'}, status=400)

        # --- Enhanced Metrics ---
        # Date range filter for all time series
        date_filter = {
            'created_at__date__gte': start_date,
            'created_at__date__lte': end_date,
        }

        # 1. Message Volume Over Time (sent/received)
        days = (end_date - start_date).days + 1
        message_volume = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            sent = Message.objects.filter(direction='out', timestamp__date=day).count()
            received = Message.objects.filter(direction='in', timestamp__date=day).count()
            message_volume.append({'date': day.isoformat(), 'sent': sent, 'received': received})

        # 2. Top Contacts by Message Volume
        from django.db.models import Count
        top_contacts_qs = Message.objects.filter(**date_filter).values('contact__name', 'contact__whatsapp_id').annotate(total=Count('id')).order_by('-total')[:10]
        top_contacts = [
            {
                'name': c['contact__name'] or c['contact__whatsapp_id'],
                'whatsapp_id': c['contact__whatsapp_id'],
                'message_count': c['total']
            }
            for c in top_contacts_qs
        ]

        # 3. Orders Trend (orders per day)
        order_trend = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            count = Order.objects.filter(created_at__date=day).count()
            order_trend.append({'date': day.isoformat(), 'orders': count})

        # 4. Revenue (sum of closed_won orders in range)
        revenue = Order.objects.filter(stage='closed_won', created_at__date__gte=start_date, created_at__date__lte=end_date).aggregate(total=models.Sum('amount'))['total'] or 0

        # 5. Average Response Time (business to client)
        from django.db.models import F, ExpressionWrapper, DurationField
        responses = Message.objects.filter(
            direction='out',
            related_incoming_message__isnull=False,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).annotate(
            response_time=ExpressionWrapper(F('timestamp') - F('related_incoming_message__timestamp'), output_field=DurationField())
        )
        avg_response_time = responses.aggregate(avg=models.Avg('response_time'))['avg']
        avg_response_time_seconds = avg_response_time.total_seconds() if avg_response_time else None

        # 6. Most Active Hours (hourly message count)
        from django.db.models.functions import ExtractHour
        hourly = Message.objects.filter(**date_filter).annotate(hour=ExtractHour('timestamp')).values('hour').annotate(count=Count('id')).order_by('hour')
        most_active_hours = [{'hour': h['hour'], 'count': h['count']} for h in hourly]

        # 7. Summary Cards
        total_messages_sent = Message.objects.filter(direction='out', **date_filter).count()
        total_messages_received = Message.objects.filter(direction='in', **date_filter).count()
        active_contacts = Message.objects.filter(**date_filter).values('contact').distinct().count()
        new_contacts = CustomerProfile.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).count()
        orders_created = Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).count()
        open_orders_value = Order.objects.filter(stage='open').aggregate(total=models.Sum('amount'))['total'] or 0
        pending_installations = InstallationRequest.objects.filter(status='pending').count()
        pending_assessments = SiteAssessmentRequest.objects.filter(status='pending').count()

        return Response({
            'summary': {
                'total_messages_sent': total_messages_sent,
                'total_messages_received': total_messages_received,
                'active_contacts': active_contacts,
                'new_contacts': new_contacts,
                'orders_created': orders_created,
                'revenue': revenue,
                'open_orders_value': open_orders_value,
                'pending_installations': pending_installations,
                'pending_assessments': pending_assessments,
                'avg_response_time_seconds': avg_response_time_seconds,
            },
            'message_volume': message_volume,
            'top_contacts': top_contacts,
            'order_trend': order_trend,
            'most_active_hours': most_active_hours,
        })
