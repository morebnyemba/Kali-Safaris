# whatsappcrm_backend/customer_data/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Order, InstallationRequest, SiteAssessmentRequest, CustomerProfile, Interaction

User = get_user_model()

# whatsappcrm_backend/customer_data/serializers.py
# --- SimpleUserSerializer ---
class SimpleUserSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic User (agent) information."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'first_name', 'last_name']

# --- SimpleCustomerProfileSerializer ---
class SimpleCustomerProfileSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic CustomerProfile information, ideal for nesting."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    contact_id = serializers.IntegerField(source='contact.id', read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['contact_id', 'full_name', 'company']

# --- Order Serializer ---
class OrderSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    assigned_agent = SimpleUserSerializer(read_only=True)
    assigned_agent_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True),
        source='assigned_agent', write_only=True, allow_null=True, required=False
    )
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'name', 'customer', 'stage', 'stage_display', 'payment_status', 'payment_status_display',
            'amount', 'currency', 'expected_close_date', 'assigned_agent', 'assigned_agent_id', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

# --- InstallationRequest Serializer ---
class InstallationRequestSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)
    associated_order = OrderSerializer(read_only=True)

    class Meta:
        model = InstallationRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

# --- SiteAssessmentRequest Serializer ---
class SiteAssessmentRequestSerializer(serializers.ModelSerializer):
    customer = SimpleCustomerProfileSerializer(read_only=True)

    class Meta:
        model = SiteAssessmentRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
# whatsappcrm_backend/customer_data/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomerProfile, Interaction
from conversations.models import Contact

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes the JWT response to include user details, which the frontend expects.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the token payload itself
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add the user object to the response dictionary for the frontend.
        data['user'] = {
            'id': self.user.id, 'username': self.user.username,
            'email': self.user.email, 'is_staff': self.user.is_staff,
        }
        return data

# A simple serializer for providing context on related models
class SimpleContactSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic Contact information."""
    class Meta:
        model = Contact
        fields = ['id', 'whatsapp_id', 'name']

class SimpleUserSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic User (agent) information."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'first_name', 'last_name']

class SimpleCustomerProfileSerializer(serializers.ModelSerializer):
    """A lightweight serializer for basic CustomerProfile information, ideal for nesting."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    contact_id = serializers.IntegerField(source='contact.id', read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['contact_id', 'full_name', 'company']

class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    A comprehensive serializer for CustomerProfile details.

    Handles the full representation of a customer's profile, including nested
    details for read operations and ID-based fields for write operations.
    """
    # The primary key of CustomerProfile is 'contact', which is a OneToOneField.
    # DRF handles this, 'pk' in the URL will map to 'contact_id'.
    contact = SimpleContactSerializer(read_only=True)

    # To make choices human-readable in API responses
    lead_status_display = serializers.CharField(source='get_lead_status_display', read_only=True)

    # Nested serializer for the assigned agent
    assigned_agent = SimpleUserSerializer(read_only=True)
    # Writable field for assigning an agent by their ID
    assigned_agent_id = serializers.PrimaryKeyRelatedField(
        # For performance and security, only list users who can be agents.
        queryset=User.objects.filter(is_staff=True),
        source='assigned_agent', write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = CustomerProfile
        # The 'contact' field is the PK, so it's implicitly read-only here.
        fields = [
            'contact', 'first_name', 'last_name', 'email', 'company', 'role',
            'address_line_1', 'address_line_2', 'city', 'state_province', 'postal_code', 'country',
            'lead_status', 'lead_status_display', 'potential_value', 'acquisition_source',
            'assigned_agent', 'assigned_agent_id', 'tags', 'notes', 'custom_attributes',
            'created_at', 'updated_at', 'last_interaction_date'
        ]
        read_only_fields = ('created_at', 'updated_at', 'last_interaction_date')

class InteractionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing customer interactions.

    On read, it provides lightweight, nested representations of the customer and agent.
    On write, it accepts IDs for customer and agent, and can automatically assign
    the logged-in user as the agent if not specified.
    """
    # Display human-readable choice values
    interaction_type_display = serializers.CharField(source='get_interaction_type_display', read_only=True)

    # Provide context on the customer and agent using lightweight serializers for performance
    customer = SimpleCustomerProfileSerializer(read_only=True)
    agent = SimpleUserSerializer(read_only=True)

    # Writable fields for creating an interaction
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomerProfile.objects.all(), source='customer', write_only=True
    )
    agent_id = serializers.PrimaryKeyRelatedField(
        # Ensure only staff members can be assigned as agents
        queryset=User.objects.filter(is_staff=True),
        source='agent', write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Interaction
        fields = [
            'id', 'customer', 'customer_id', 'agent', 'agent_id', 'interaction_type',
            'interaction_type_display', 'notes', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        """
        Overrides create to automatically assign the authenticated user as the
        agent if one is not provided in the request payload.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Check if an agent was specified in the payload before assigning the request user.
            # This handles cases where agent_id is explicitly sent as null.
            if 'agent' not in validated_data and 'agent_id' not in self.initial_data:
                validated_data['agent'] = request.user

        return super().create(validated_data)