# --- IsStaffOrReadOnly Permission ---
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.http import Http404

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow read access to any authenticated user,
    but full write access (create, update, delete) only to admin/staff users.
    """
    def has_permission(self, request, view):
        # Allow read-only access for any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write access only for staff users.
        return request.user and request.user.is_staff

from .models import Order, InstallationRequest, SiteAssessmentRequest
from .serializers import OrderSerializer, InstallationRequestSerializer, SiteAssessmentRequestSerializer
# --- Order ViewSet ---
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('customer', 'assigned_agent').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filterset_fields = ['stage', 'payment_status', 'customer']
    search_fields = ['order_number', 'name', 'notes']

# --- InstallationRequest ViewSet ---
class InstallationRequestViewSet(viewsets.ModelViewSet):
    queryset = InstallationRequest.objects.select_related('customer', 'associated_order').all()
    serializer_class = InstallationRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filterset_fields = ['status', 'installation_type', 'customer']
    search_fields = ['order_number', 'full_name', 'address', 'contact_phone']

# --- SiteAssessmentRequest ViewSet ---
class SiteAssessmentRequestViewSet(viewsets.ModelViewSet):
    queryset = SiteAssessmentRequest.objects.select_related('customer').all()
    serializer_class = SiteAssessmentRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filterset_fields = ['status', 'customer']
    search_fields = ['assessment_id', 'full_name', 'address', 'contact_info']
# whatsappcrm_backend/customer_data/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.http import Http404


# New models and serializers
from .models import CustomerProfile, Interaction
from .serializers import CustomerProfileSerializer, InteractionSerializer, MyTokenObtainPairSerializer

# Still need Contact for get_or_create logic
from conversations.models import Contact

import logging
logger = logging.getLogger(__name__)

class MyTokenObtainPairView(TokenObtainPairView):
    """
    Uses the custom serializer to add user details to the JWT response.
    """
    serializer_class = MyTokenObtainPairSerializer

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow read access to any authenticated user,
    but full write access (create, update, delete) only to admin/staff users.
    """
    def has_permission(self, request, view):
        # Allow read-only access for any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write access only for staff users.
        return request.user and request.user.is_staff

class IsInteractionOwnerOrAdmin(permissions.BasePermission):
    """
    Allows read access to any authenticated user.
    Allows any authenticated user to create an interaction.
    Allows write access (update, delete) only to the agent who created the interaction
    or to an admin/staff user.
    """
    def has_permission(self, request, view):
        # Allow any authenticated user to access the view (for list and create)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Allow read access for any authenticated user.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write access only to the owner or an admin.
        return obj.agent == request.user or request.user.is_staff

class CustomerProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Customer Profiles.
    A profile is automatically created for a contact on first access (GET/PUT/PATCH).
    """
    queryset = CustomerProfile.objects.select_related('contact', 'assigned_agent').all()
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    
    # CustomerProfile's PK is contact_id.
    # The URL will be /profiles/{pk}/ where pk is the contact_id.
    lookup_field = 'pk' # Explicitly state we are looking up by the primary key (contact_id)

    # Enable filtering and searching for better usability on the frontend.
    # For more advanced filtering (e.g., date ranges), consider using the `django-filter` library
    # and defining a `filterset_class`.
    filterset_fields = ['lead_status', 'assigned_agent', 'country', 'company']
    search_fields = ['first_name', 'last_name', 'email', 'company', 'contact__whatsapp_id', 'tags']

    def get_object(self):
        """
        Override get_object to use the PK from the URL, which is the contact_id.
        If the profile doesn't exist for a GET/PUT/PATCH, create it on-the-fly.
        """
        queryset = self.filter_queryset(self.get_queryset())
        # The 'pk' in the URL corresponds to the Contact's ID.
        pk = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)

        try:
            # The primary key of CustomerProfile is the contact_id.
            obj = queryset.get(pk=pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except CustomerProfile.DoesNotExist:
            # For safe methods (GET) or update methods (PUT, PATCH), if the profile doesn't exist
            # but the underlying Contact does, we create the profile. This is a common pattern
            # for user profiles that might not be created immediately with the user/contact.
            if self.request.method in ['GET', 'PUT', 'PATCH']:
                contact = get_object_or_404(Contact, pk=pk) # First, ensure the contact exists.
                # get_or_create is atomic and safe.
                obj, created = CustomerProfile.objects.get_or_create(contact=contact)
                if created:
                    logger.info(f"CustomerProfile created on-the-fly for Contact ID: {pk} during {self.request.method} action.")
                # We must still check permissions on the newly created object.
                self.check_object_permissions(self.request, obj)
                return obj
            # For other methods like DELETE, if it doesn't exist, it's a 404.
            raise Http404("CustomerProfile not found and action is not retrieve/update.")

    # The `perform_update` method is no longer needed as `updated_at` is automatic
    # and `last_interaction_date` is handled by the Interaction model.

class InteractionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for logging and viewing customer interactions.
    Supports filtering by customer profile ID, e.g., /api/interactions/?customer=<contact_id>
    """
    queryset = Interaction.objects.select_related('customer__contact', 'agent').all().order_by('-created_at')
    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInteractionOwnerOrAdmin]

    # For more advanced filtering (e.g., date ranges), consider using the `django-filter` library
    # and defining a `filterset_class`.
    filterset_fields = ['customer', 'interaction_type', 'agent']
    search_fields = ['notes', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id']

    # No custom perform_create needed, the serializer handles agent assignment from request context.
    # The IsInteractionOwnerOrAdmin permission class allows any authenticated user to create.