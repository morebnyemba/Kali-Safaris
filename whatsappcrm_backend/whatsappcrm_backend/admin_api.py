from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


User = get_user_model()


def is_admin_role(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["admin", "administrators"]).exists()


class IsStaffReadAdminWrite(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user.is_staff
        return is_admin_role(user)


class PermissionLiteSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "codename", "name", "content_type_id", "label"]

    def get_label(self, obj):
        return f"{obj.content_type.app_label}.{obj.codename}"


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionLiteSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.select_related("content_type").all(),
        source="permissions",
        write_only=True,
        required=False,
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions", "permission_ids"]


class AdminUserSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False,
    )
    user_permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.select_related("content_type").all(),
        required=False,
    )
    group_names = serializers.SerializerMethodField()
    permission_labels = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "group_names",
            "user_permissions",
            "permission_labels",
            "date_joined",
            "last_login",
            "password",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "group_names", "permission_labels"]

    def get_group_names(self, obj):
        return list(obj.groups.values_list("name", flat=True))

    def get_permission_labels(self, obj):
        return sorted(obj.get_all_permissions())

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        permissions_data = validated_data.pop("user_permissions", [])
        password = validated_data.pop("password", None)

        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()

        if groups:
            user.groups.set(groups)
        if permissions_data:
            user.user_permissions.set(permissions_data)
        return user

    def update(self, instance, validated_data):
        groups = validated_data.pop("groups", None)
        permissions_data = validated_data.pop("user_permissions", None)
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if groups is not None:
            instance.groups.set(groups)
        if permissions_data is not None:
            instance.user_permissions.set(permissions_data)
        return instance


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="user.username", read_only=True)
    content_type = serializers.SerializerMethodField()
    action_label = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = [
            "id",
            "action_time",
            "actor",
            "object_id",
            "object_repr",
            "change_message",
            "content_type",
            "action_flag",
            "action_label",
        ]

    def get_content_type(self, obj):
        if not obj.content_type_id:
            return None
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_action_label(self, obj):
        if obj.action_flag == LogEntry.ADDITION:
            return "created"
        if obj.action_flag == LogEntry.CHANGE:
            return "updated"
        if obj.action_flag == LogEntry.DELETION:
            return "deleted"
        return "unknown"


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("groups", "user_permissions").all().order_by("username")
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffReadAdminWrite]
    search_fields = ["username", "first_name", "last_name", "email"]

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsStaffReadAdminWrite])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsStaffReadAdminWrite])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.prefetch_related("permissions").all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffReadAdminWrite]
    search_fields = ["name"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated, IsStaffReadAdminWrite])
    def permissions(self, request):
        queryset = Permission.objects.select_related("content_type").all().order_by(
            "content_type__app_label", "codename"
        )
        serializer = PermissionLiteSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogEntry.objects.select_related("user", "content_type").all().order_by("-action_time")
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffReadAdminWrite]
