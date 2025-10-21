# whatsappcrm_backend/media_manager/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'media_manager_api'

router = DefaultRouter()
router.register(r'assets', views.MediaAssetViewSet, basename='mediaasset')

urlpatterns = [
    path('', include(router.urls)),
]