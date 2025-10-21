# whatsappcrm_backend/customer_data/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our new viewsets with it.
router = DefaultRouter()
router.register(r'profiles', views.CustomerProfileViewSet, basename='customerprofile')
router.register(r'interactions', views.InteractionViewSet, basename='interaction')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'installation-requests', views.InstallationRequestViewSet, basename='installationrequest')
router.register(r'site-assessments', views.SiteAssessmentRequestViewSet, basename='siteassessmentrequest')

app_name = 'customer_data_api'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]