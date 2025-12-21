from django.urls import path
from .views import omari_auth_view, omari_request_view, omari_query_view

app_name = 'omari_integration'

urlpatterns = [
    path('auth/', omari_auth_view, name='auth'),
    path('request/', omari_request_view, name='request'),
    path('query/<str:reference>/', omari_query_view, name='query'),
]
