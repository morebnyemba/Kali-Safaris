from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .admin_api import AdminUserViewSet, AuditLogViewSet, GroupViewSet


router = DefaultRouter()
router.register(r"users", AdminUserViewSet, basename="admin-user")
router.register(r"roles", GroupViewSet, basename="admin-role")
router.register(r"audit", AuditLogViewSet, basename="admin-audit")


app_name = "admin_api"

urlpatterns = [
    path("", include(router.urls)),
]
