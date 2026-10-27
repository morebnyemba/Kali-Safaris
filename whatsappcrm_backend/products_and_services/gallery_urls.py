from django.urls import path

from .views import public_gallery_image_view, public_gallery_list_view

app_name = 'gallery'

urlpatterns = [
    path('', public_gallery_list_view, name='public_gallery_list'),
    path('<int:pk>/<int:version>/', public_gallery_image_view, name='gallery_image_file'),
]
