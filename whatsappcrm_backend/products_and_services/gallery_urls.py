from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import GalleryImageViewSet, public_gallery_image_view, public_gallery_list_view

app_name = 'gallery'

router = SimpleRouter()
router.register(r'manage', GalleryImageViewSet, basename='gallery_manage')

urlpatterns = [
    path('', public_gallery_list_view, name='public_gallery_list'),
    path('<int:pk>/<int:version>/', public_gallery_image_view, name='gallery_image_file'),
    path('', include(router.urls)),
]
