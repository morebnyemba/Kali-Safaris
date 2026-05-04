from django.urls import path
from .views import (
    cbz_public_config_view,
    cbz_ecocash_debit_view,
    cbz_card_debit_view,
    cbz_card_3ds_complete_view,
    cbz_query_view,
    cbz_callback_view,
    cbz_certificate_generate_view,
    cbz_certificate_get_view,
    cbz_certificate_submit_view,
    cbz_certificate_renew_view,
)

app_name = 'cbz_integration'

urlpatterns = [
    path('config/', cbz_public_config_view, name='public_config'),

    # EcoCash payment (WhatsApp bot or direct API)
    path('ecocash/debit/', cbz_ecocash_debit_view, name='ecocash_debit'),

    # Card payment (website checkout only)
    path('card/debit/', cbz_card_debit_view, name='card_debit'),
    path('card/3ds/complete/', cbz_card_3ds_complete_view, name='card_3ds_complete'),

    # Transaction status query
    path('query/<str:reference>/', cbz_query_view, name='query'),

    # Out-of-band callback from iVeri
    path('callback/', cbz_callback_view, name='callback'),

    # SOAP certificate lifecycle management
    path('certificates/generate/', cbz_certificate_generate_view, name='certificate_generate'),
    path('certificates/current/', cbz_certificate_get_view, name='certificate_get'),
    path('certificates/submit/', cbz_certificate_submit_view, name='certificate_submit'),
    path('certificates/renew/', cbz_certificate_renew_view, name='certificate_renew'),
]
