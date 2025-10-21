# whatsappcrm_backend/conversations/views.py

from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Prefetch, Subquery, OuterRef, Count, F
from functools import reduce
from operator import or_
from django.utils import timezone
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging # Make sure logging is imported

from .models import Contact, Message
from .serializers import (
    ContactSerializer,
    MessageSerializer,
    MessageListSerializer,
    ContactListSerializer,
    ContactDetailSerializer,
    BroadcastCreateSerializer,
    BroadcastSerializer, 
    BroadcastGroupCreateSerializer,
)
from .tasks import dispatch_broadcast_task
# To get active MetaAppConfig for sending
from meta_integration.models import MetaAppConfig
from customer_data.models import CustomerProfile
# To personalize messages using flow template logic
from flows.services import _resolve_value

logger = logging.getLogger(__name__) # Standard way to get logger for current module

# Define permissions if not already in a central place
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    Others can only read. Assumes IsAuthenticated is also applied.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        return request.user and request.user.is_staff

class CanCreateMessagesOrAdminOnly(permissions.BasePermission):
    """
    Allows any authenticated user to create (POST) a message,
    but restricts list, retrieve, update, and delete to admin/staff users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method == 'POST': # Allow any authenticated user to create
            return True
        # For all other methods (GET, PUT, PATCH, DELETE), require staff status
        return request.user and request.user.is_staff


class ContactViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Contacts.
    - Admins can CRUD.
    - Authenticated users can list/retrieve (permissions can be refined).
    """
    queryset = Contact.objects.all().order_by('-last_seen')
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return ContactListSerializer
        if self.action == 'retrieve':
            return ContactDetailSerializer
        return ContactSerializer

    def get_queryset(self):
        """
        Dynamically filter and annotate the queryset based on the action.
        - For 'list', add message previews and unread counts, and order by last message time.
        - For 'retrieve', prefetch related data for a detailed view.
        """
        queryset = Contact.objects.all()

        if self.action == 'list':
            # Subquery to get the text content of the latest message for each contact
            latest_message_subquery = Message.objects.filter(
                contact=OuterRef('pk')
            ).order_by('-timestamp')
            
            latest_message_preview = latest_message_subquery.values('text_content')[:1]
            latest_message_timestamp = latest_message_subquery.values('timestamp')[:1]

            queryset = queryset.annotate(
                last_message_preview=Subquery(latest_message_preview),
                # A simple unread count: incoming messages with 'received' status.
                # A more complex implementation might track read status per agent.
                unread_count=Count('messages', filter=Q(messages__direction='in', messages__status='received')),
                # Annotate the latest message timestamp to order by it
                latest_message_ts=Subquery(latest_message_timestamp)
            ).order_by(F('latest_message_ts').desc(nulls_last=True), '-last_seen')

            search_term = self.request.query_params.get('search', None)
            if search_term:
                queryset = queryset.filter(
                    Q(name__icontains=search_term) | 
                    Q(whatsapp_id__icontains=search_term)
                )

            needs_intervention_filter = self.request.query_params.get('needs_human_intervention', None)
            if needs_intervention_filter is not None:
                if needs_intervention_filter.lower() == 'true':
                    queryset = queryset.filter(needs_human_intervention=True)
                elif needs_intervention_filter.lower() == 'false':
                    queryset = queryset.filter(needs_human_intervention=False)

        elif self.action == 'retrieve':
            # For the detail view, prefetch messages in chronological order
            queryset = queryset.prefetch_related(
                Prefetch('messages', queryset=Message.objects.order_by('timestamp'))
            )
        else:
            # Fallback for other actions, use default ordering
            queryset = queryset.order_by('-last_seen')
            
        return queryset

    @action(detail=True, methods=['get'], url_path='messages', permission_classes=[permissions.IsAuthenticated])
    def list_messages_for_contact(self, request, pk=None):
        contact = get_object_or_404(Contact, pk=pk)
        # Return messages in REVERSE chronological order for pagination (most recent first)
        messages_queryset = Message.objects.filter(contact=contact).select_related('contact').order_by('-timestamp')
        
        page = self.paginate_queryset(messages_queryset)
        if page is not None:
            serializer = MessageListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = MessageListSerializer(messages_queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='toggle-block', permission_classes=[permissions.IsAuthenticated, IsAdminOrReadOnly])
    def toggle_block_status(self, request, pk=None):
        contact = get_object_or_404(Contact, pk=pk)
        contact.is_blocked = not contact.is_blocked
        contact.save(update_fields=['is_blocked', 'last_seen']) # last_seen is auto_now
        serializer = self.get_serializer(contact)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='toggle-intervention', permission_classes=[permissions.IsAuthenticated, IsAdminOrReadOnly])
    def toggle_human_intervention(self, request, pk=None):
        """
        Toggles the 'needs_human_intervention' flag for a contact.
        """
        contact = self.get_object()
        contact.needs_human_intervention = not contact.needs_human_intervention
        if not contact.needs_human_intervention:
            # Also clear the timestamp when resolving the intervention
            contact.intervention_requested_at = None
        else:
            contact.intervention_requested_at = timezone.now()
        contact.save(update_fields=['needs_human_intervention', 'intervention_requested_at', 'last_seen'])
        
        # --- Broadcast update via WebSocket ---
        channel_layer = get_channel_layer()
        group_name = f'conversation_{contact.id}'
        
        # Use the detail serializer to get the full, updated contact representation
        serializer = ContactDetailSerializer(contact)
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {'type': 'contact_updated', 'contact': serializer.data}
        )
        logger.info(f"Broadcasted contact update for contact {contact.id} to group {group_name}.")
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessageViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Message.objects.all().select_related('contact').order_by('-timestamp')
    permission_classes = [permissions.IsAuthenticated, CanCreateMessagesOrAdminOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return MessageListSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        """
        Handles the creation of an outgoing message and dispatches it for sending via Celery.
        """
        # The serializer expects 'contact' (PK), 'message_type', and 'content_payload'.
        # 'direction' and 'status' are set here for outgoing messages.
        # The request.user (agent sending the message) can also be logged if needed.
        # message_by_user = self.request.user # If you want to track which CRM user sent it

        message = serializer.save(
            direction='out',
            status='pending_dispatch', # Initial status before task picks it up
            timestamp=timezone.now() # Set send timestamp
            # created_by=message_by_user # Example if you add a 'created_by' FK to User
        )
        
        logger.info(
            f"Message record {message.id} created for contact {message.contact.whatsapp_id} "
            f"by user {self.request.user}. Type: {message.message_type}. Status: {message.status}."
        )

        # The logic for dispatching the message has been moved to the MessageSerializer's
        # create method for better encapsulation. The serializer now handles finding the
        # active config and queueing the Celery task transactionally.
        # This keeps the view cleaner and focused on handling the request/response cycle.
        # No further action is needed here.
        pass


    def get_queryset(self):
        queryset = super().get_queryset()
        contact_id = self.request.query_params.get('contact_id')
        if contact_id:
            try:
                queryset = queryset.filter(contact_id=int(contact_id))
            except ValueError:
                logger.warning(f"Invalid contact_id query parameter: {contact_id}")
                return Message.objects.none() # Return empty for invalid ID
        
        search_term = self.request.query_params.get('search')
        if search_term:
            queryset = queryset.filter(
                Q(text_content__icontains=search_term) |
                Q(contact__name__icontains=search_term) |
                Q(contact__whatsapp_id__icontains=search_term)
            )
        return queryset


class BroadcastViewSet(viewsets.ViewSet):
    """
    API endpoint for sending business-initiated template messages (broadcasts).
    """
    permission_classes = [permissions.IsAdminUser] # Only admins can broadcast

    @action(detail=False, methods=['post'], url_path='send-template')
    def send_template_message(self, request):
        """
        Accepts a list of contact IDs and a template to send.
        Creates a Broadcast object to track the campaign and dispatches a single
        Celery task to handle the message creation and sending asynchronously.
        """
        serializer = BroadcastCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        # Create the parent Broadcast object to track this campaign
        broadcast = Broadcast.objects.create(
            name=validated_data.get('name', f"Broadcast on {timezone.now().strftime('%Y-%m-%d %H:%M')}"),
            template_name=validated_data['template_name'],
            created_by=request.user,
            status='pending',
            total_recipients=len(validated_data['contact_ids'])
        )
        logger.info(f"Created Broadcast object {broadcast.id} for {broadcast.total_recipients} recipients.")

        # Dispatch a single Celery task to handle the entire broadcast job
        dispatch_broadcast_task.delay(
            broadcast_id=broadcast.id,
            contact_ids=validated_data['contact_ids'],
            language_code=validated_data['language_code'],
            components_template=validated_data.get('components')
        )

        # Immediately return the created Broadcast object to the client
        response_serializer = BroadcastSerializer(broadcast)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'], url_path='send-to-group')
    def send_to_group(self, request):
        """
        Sends a template message to a dynamically generated group of contacts
        based on CustomerProfile tags or assigned agent.
        """
        serializer = BroadcastGroupCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        tags = validated_data.get('tags', [])
        agent_id = validated_data.get('assigned_agent_id')

        # Build the filter for CustomerProfile
        profile_filters = Q()
        if tags:
            # Create a Q object for each tag and combine with OR
            tag_queries = [Q(tags__contains=tag) for tag in tags]
            profile_filters |= reduce(or_, tag_queries)
        
        if agent_id:
            # This will OR with the tag query if it exists
            profile_filters |= Q(assigned_agent_id=agent_id)

        # Get the primary keys (which are contact_ids) of the matching profiles
        contact_ids = list(CustomerProfile.objects.filter(profile_filters).values_list('contact_id', flat=True))

        if not contact_ids:
            return Response({"message": "No contacts found matching the specified criteria."}, status=status.HTTP_404_NOT_FOUND)

        # Create the parent Broadcast object
        broadcast = Broadcast.objects.create(
            name=validated_data.get('name', f"Group Broadcast on {timezone.now().strftime('%Y-%m-%d %H:%M')}"),
            template_name=validated_data['template_name'],
            created_by=request.user,
            status='pending',
            total_recipients=len(contact_ids)
        )
        logger.info(f"Created Broadcast object {broadcast.id} for {broadcast.total_recipients} recipients based on group criteria.")

        # Dispatch the Celery task
        dispatch_broadcast_task.delay(
            broadcast_id=broadcast.id,
            contact_ids=contact_ids,
            language_code=validated_data['language_code'],
            components_template=validated_data.get('components')
        )

        response_serializer = BroadcastSerializer(broadcast)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)