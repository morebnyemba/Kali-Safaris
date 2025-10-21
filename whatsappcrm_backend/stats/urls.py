# stats/urls.py
from django.urls import path
from .views import (
    DashboardSummaryStatsAPIView,
    FinancialStatsAPIView,
    EngagementStatsAPIView,
    MessageVolumeAPIView
)

app_name = 'stats_api'

urlpatterns = [
    # The main summary endpoint for the dashboard overview
    path('summary/', DashboardSummaryStatsAPIView.as_view(), name='dashboard_summary_stats'),
    # Granular, filterable endpoints for detailed analytics
    path('financial/', FinancialStatsAPIView.as_view(), name='financial_stats'),
    path('engagement/', EngagementStatsAPIView.as_view(), name='engagement_stats'),
    path('messages/', MessageVolumeAPIView.as_view(), name='message_volume_stats'),
]