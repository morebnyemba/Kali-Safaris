# whatsappcrm_backend/customer_data/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our new viewsets with it.
router = DefaultRouter()
router.register(r'profiles', views.CustomerProfileViewSet, basename='customerprofile')
router.register(r'interactions', views.InteractionViewSet, basename='interaction')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'inquiries', views.TourInquiryViewSet, basename='tourinquiry')

app_name = 'customer_data_api'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]