from django.urls import path
from .views import AnalyticsReportsView

urlpatterns = [
    path('reports/', AnalyticsReportsView.as_view(), name='analytics-reports'),
]
