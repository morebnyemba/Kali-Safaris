from django.urls import path

from .views import public_tours_list_view, tour_availability_view

app_name = 'products_and_services'

urlpatterns = [
    path('', public_tours_list_view, name='public_tours_list'),
    path('<int:tour_id>/availability/', tour_availability_view, name='tour_availability'),
]
