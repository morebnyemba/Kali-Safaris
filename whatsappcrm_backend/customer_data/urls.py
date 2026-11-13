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
router.register(r'travelers', views.TravelerViewSet, basename='traveler')

app_name = 'customer_data_api'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('export/manifest/', views.export_booking_manifest, name='export_booking_manifest'),
    path('export/passenger-summary/', views.export_passenger_summary, name='export_passenger_summary'),
    path('export/id-pack/', views.export_id_pack, name='export_id_pack'),
    path('manage/<str:token>/', views.ManageBookingView.as_view(), name='manage_booking'),
    path('manage/<str:token>/travelers/<uuid:traveler_id>/id/', views.ManageTravelerIdView.as_view(), name='manage_traveler_id'),
    path('manage/<str:token>/reschedule/', views.ManageRescheduleView.as_view(), name='manage_reschedule'),
]