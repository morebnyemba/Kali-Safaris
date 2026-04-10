from django.urls import path
from .views import (
    cbz_ecocash_debit_view,
    cbz_card_debit_view,
    cbz_query_view,
    cbz_callback_view,
)

app_name = 'cbz_integration'

urlpatterns = [
    # EcoCash payment (WhatsApp bot or direct API)
    path('ecocash/debit/', cbz_ecocash_debit_view, name='ecocash_debit'),

    # Card payment (website checkout only)
    path('card/debit/', cbz_card_debit_view, name='card_debit'),

    # Transaction status query
    path('query/<str:reference>/', cbz_query_view, name='query'),

    # Out-of-band callback from iVeri
    path('callback/', cbz_callback_view, name='callback'),
]
