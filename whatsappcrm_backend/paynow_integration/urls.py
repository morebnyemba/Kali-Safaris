from django.urls import path
from .views import paynow_return_view, paynow_ipn_view

app_name = 'paynow_integration'

urlpatterns = [
    path('return/', paynow_return_view, name='paynow-return'),
    path('ipn/', paynow_ipn_view, name='paynow-ipn'),
]
