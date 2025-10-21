# whatsappcrm_backend/meta_integration/views.py
import json
import logging
import hashlib # For signature verification
import hmac    # For signature verification

from django.http import HttpRequest, HttpResponse, JsonResponse # HttpRequest is not directly used as type hint here but fine
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
# get_object_or_404 is used by ViewSets implicitly or can be used directly
from django.utils import timezone # For WebhookEventLog _save_log and MetaWebhookAPIView handlers
from datetime import datetime # For WebhookEventLog _handle_message
from django.db import transaction
from django.conf import settings # To get APP_SECRET

from rest_framework import viewsets, permissions, status # permissions used by ViewSets
from rest_framework.response import Response # Used by ViewSets
from rest_framework.decorators import action # Used by ViewSets
# ParseError is not explicitly raised but good to keep if DRF might raise it for malformed requests
from rest_framework.exceptions import ParseError



from .models import MetaAppConfig, WebhookEventLog # EVENT_TYPE_CHOICES removed from here
from .serializers import (
    MetaAppConfigSerializer,
    WebhookEventLogSerializer,
    WebhookEventLogListSerializer
)
# from .utils import send_whatsapp_message # send_whatsapp_message_task is used from tasks now

# --- Cross-app imports to be localized or already localized ---
# from flows.services import process_message_for_flow # Imported locally in _handle_message
# from conversations.services import get_or_create_contact_by_wa_id # Imported locally in post
from conversations.models import Message # Imported locally in _handle_message
from .tasks import send_read_receipt_task

logger = logging.getLogger('meta_integration') # Using the app-specific logger from your original file

# --- Helper function to get active config (from your original file) ---
def get_active_meta_config():
    try:
        return MetaAppConfig.objects.get_active_config()
    except MetaAppConfig.DoesNotExist:
        logger.critical("CRITICAL: No active Meta App Configuration found. Webhook and message sending will fail.")
        return None
    except MetaAppConfig.MultipleObjectsReturned:
        logger.critical("CRITICAL: Multiple active Meta App Configurations found. Please fix in Django Admin.")
        return None # Or handle as per your app's logic, e.g., return the first one
    except Exception as e: # Catch any other unexpected error
        logger.critical(f"CRITICAL: Error retrieving active MetaAppConfig: {e}", exc_info=True)
        return None

# --- Permission Class (from your original file) ---
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

# --- ViewSets as defined in your original file, with minor adjustments for consistency if needed ---
class MetaAppConfigViewSet(viewsets.ModelViewSet):
    queryset = MetaAppConfig.objects.all().order_by('-is_active', 'name')
    serializer_class = MetaAppConfigSerializer
    permission_classes = [permissions.IsAdminUser] # Ensure this permission suits your needs

    @transaction.atomic
    def perform_create(self, serializer):
        if serializer.validated_data.get('is_active'):
            MetaAppConfig.objects.filter(is_active=True).update(is_active=False)
        serializer.save()
        logger.info(f"MetaAppConfig '{serializer.instance.name}' created by {self.request.user}.")


    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        if serializer.validated_data.get('is_active') and not instance.is_active: # Activating this one
            MetaAppConfig.objects.filter(is_active=True).exclude(pk=instance.pk).update(is_active=False)
        serializer.save()
        logger.info(f"MetaAppConfig '{instance.name}' updated by {self.request.user}.")


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def set_active(self, request, pk=None):
        config_to_activate = self.get_object()
        if config_to_activate.is_active:
            return Response({"message": "Configuration is already active."}, status=status.HTTP_200_OK)
        with transaction.atomic():
            MetaAppConfig.objects.filter(is_active=True).exclude(pk=config_to_activate.pk).update(is_active=False)
            config_to_activate.is_active = True
            config_to_activate.save(update_fields=['is_active', 'updated_at'])
        logger.info(f"MetaAppConfig '{config_to_activate.name}' set to active by {request.user}.")
        return Response(self.get_serializer(config_to_activate).data, status=status.HTTP_200_OK)


class WebhookEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WebhookEventLog.objects.all().select_related('app_config', 'message__contact').order_by('-received_at')
    permission_classes = [permissions.IsAdminUser] # Or IsAdminOrReadOnly if non-staff can view
    # filter_backends = [...] # Add if you use django-filter
    filterset_fields = ['event_type', 'processing_status', 'event_identifier', 'phone_number_id_received', 'waba_id_received', 'app_config__name']
    search_fields = ['payload', 'processing_notes', 'event_identifier', 'message__contact__whatsapp_id', 'message__contact__name']
    ordering_fields = ['received_at', 'processed_at', 'event_type']

    def get_serializer_class(self):
        return WebhookEventLogListSerializer if self.action == 'list' else WebhookEventLogSerializer

    @action(detail=False, methods=['get'])
    def latest(self, request):
        count_str = request.query_params.get('count', '25')
        try:
            count = int(count_str)
            if not (0 < count <= 200): raise ValueError("Count must be between 1 and 200.")
        except ValueError as e:
            return Response({"error": f"Invalid 'count' parameter: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        latest_logs = self.filter_queryset(self.get_queryset())[:count] # Apply filters before slicing
        serializer = self.get_serializer(latest_logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reprocess(self, request, pk=None):
        log_entry = self.get_object()
        # Allow reprocessing for 'message' or 'error'/'failed' statuses
        if log_entry.processing_status not in ['error', 'failed'] and not log_entry.event_type.startswith('message'):
             return Response({"error": "Only 'message' events or events in 'error'/'failed' state can typically be reprocessed this way."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Basic reprocessing: Set status to 'pending_reprocessing'
        # A Celery task or a separate management command would pick these up.
        log_entry.processing_status = 'pending_reprocessing'
        log_entry.processing_notes = (log_entry.processing_notes or "") + \
                                     f"\nManually marked for reprocessing by {request.user} on {timezone.now().isoformat()}."
        log_entry.processed_at = None # Clear processed_at for reprocessing
        log_entry.save(update_fields=['processing_status', 'processing_notes', 'processed_at'])
        logger.info(f"WebhookEventLog {log_entry.id} (Event: {log_entry.event_type}) marked for reprocessing by user {request.user}.")
        return Response({"message": f"Event {log_entry.id} marked for reprocessing."}, status=status.HTTP_202_ACCEPTED)


@method_decorator(csrf_exempt, name='dispatch')
class MetaWebhookAPIView(View):
    """
    Handles incoming webhook events from Meta (Facebook/WhatsApp).
    (Content from your uploaded meta_integration/views.py, with localized imports for flows and conversations)
    """

    def _verify_signature(self, request_body_bytes, x_hub_signature_256, app_secret_key):
        # ... (implementation from your uploaded file) ...
        if not x_hub_signature_256:
            logger.warning("Webhook signature (X-Hub-Signature-256) missing.")
            return False
        if not app_secret_key:
            logger.error("App Secret not configured for signature verification. Verification skipped (INSECURE).")
            return True # Bypassing for now if not configured, but log indicates insecurity

        if not x_hub_signature_256.startswith('sha256='):
            logger.warning("Webhook signature format is invalid (must start with 'sha256=').")
            return False
        expected_signature_hex = x_hub_signature_256.split('sha256=', 1)[1]
        byte_key = app_secret_key.encode('utf-8')
        hashed = hmac.new(byte_key, request_body_bytes, hashlib.sha256)
        calculated_signature_hex = hashed.hexdigest()
        if not hmac.compare_digest(calculated_signature_hex, expected_signature_hex):
            logger.warning(f"Webhook signature mismatch. Expected: {expected_signature_hex}, Calculated: {calculated_signature_hex}")
            return False
        logger.debug("Webhook signature verified successfully.")
        return True

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs): # app_id_or_name removed as it's not in urls.py for this view
        from conversations.services import get_or_create_contact_by_wa_id

        logger.info("Webhook POST request received.")
        logger.debug(f"Request headers: {request.headers}")

        # 1. Decode payload first to find the phone_number_id
        raw_payload_str = request.body.decode('utf-8', errors='ignore')
        try:
            payload = json.loads(raw_payload_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}. Body: {raw_payload_str[:500]}...")
            WebhookEventLog.objects.create(
                app_config=None, event_type='error',
                payload={'error': 'Invalid JSON', 'body_snippet': raw_payload_str[:500], 'exception': str(e)},
                processing_status='error', processing_notes='Failed to parse JSON.'
            )
            return HttpResponse("Invalid JSON payload", status=400)

        # 2. Determine the config based on the payload's phone_number_id
        target_config = None
        phone_id_from_payload = None
        try:
            phone_id_from_payload = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
            if phone_id_from_payload:
                target_config = MetaAppConfig.objects.get(phone_number_id=phone_id_from_payload)
            else:
                logger.warning("Could not find phone_number_id in webhook payload. Will fall back to active config if possible.")
                target_config = get_active_meta_config()
        except MetaAppConfig.DoesNotExist:
            logger.error(f"WEBHOOK POST: No MetaAppConfig found for phone_number_id '{phone_id_from_payload}'. Event ignored.")
            WebhookEventLog.objects.create(
                app_config=None, event_type='security', phone_number_id_received=phone_id_from_payload,
                payload=payload, processing_status='rejected', processing_notes=f"No config found for phone_number_id {phone_id_from_payload}."
            )
            return HttpResponse("EVENT_RECEIVED_BUT_UNCONFIGURED", status=200)
        except (IndexError, KeyError, AttributeError):
             logger.warning("Could not extract phone_number_id from payload structure. Falling back to active config.")
             target_config = get_active_meta_config()

        if not target_config:
            logger.error("WEBHOOK POST: Processing failed - No matching or active MetaAppConfig. Event ignored.")
            return HttpResponse("EVENT_RECEIVED_BUT_UNCONFIGURED", status=200)

        logger.info(f"Processing webhook for config: '{target_config.name}' (Phone ID: {target_config.phone_number_id})")

        # 3. Verify signature using the determined config's app_secret
        app_secret = target_config.app_secret
        if not app_secret:
             logger.warning(f"App Secret is not configured for '{target_config.name}'. Webhook signature verification will be SKIPPED. This is INSECURE.")
        elif not self._verify_signature(request.body, request.headers.get('X-Hub-Signature-256'), app_secret):
            logger.error("Webhook signature verification FAILED. Discarding request.")
            WebhookEventLog.objects.create(
                app_config=target_config, event_type='security',
                payload={'error': 'Signature verification failed', 'headers': dict(request.headers)},
                processing_status='rejected', processing_notes='Invalid X-Hub-Signature-256'
            )
            return HttpResponse("Invalid signature", status=403)

        log_entry = None # Initialize
        base_log_defaults = {
            'app_config': target_config, 'payload_object_type': payload.get("object")
        }

        try:
            # The complex dispatch logic from your meta_integration/views.py post method
            # (identifying messages, statuses, errors from payload structure)
            if payload.get("object") == "whatsapp_business_account":
                for entry_idx, entry in enumerate(payload.get("entry", [])):
                    waba_id = entry.get("id")
                    for change_idx, change in enumerate(entry.get("changes", [])):
                        value = change.get("value", {})
                        field = change.get("field")
                        metadata = value.get("metadata", {})
                        phone_id = metadata.get("phone_number_id")
                        logger.info(f"Processing entry[{entry_idx}].change[{change_idx}]: field='{field}', phone_id='{phone_id}'")
                        log_defaults_for_change = {**base_log_defaults, 'waba_id_received': waba_id, 'phone_number_id_received': phone_id}

                        if field == "messages":
                            if "messages" in value:
                                for msg_data in value["messages"]:
                                    wamid = msg_data.get("id")
                                    # Use update_or_create for WebhookEventLog to handle retries from Meta
                                    log_entry, created_log = WebhookEventLog.objects.update_or_create(
                                        event_identifier=wamid,
                                        app_config=target_config,
                                        defaults={
                                            'payload_object_type': payload.get("object"),
                                            'waba_id_received': waba_id,
                                            'phone_number_id_received': phone_id,
                                            'event_type': f"message_{msg_data.get('type', 'unknown')}",
                                            'payload': msg_data,
                                            'processing_status': 'pending' # Reset to pending if reprocessing
                                        }
                                    )
                                    if created_log or log_entry.processing_status in ['pending', 'pending_reprocessing', 'error']: # Process if new or needs reprocessing
                                        contact_wa_id = msg_data.get("from")
                                        profile_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "Unknown")
                                        contact, _ = get_or_create_contact_by_wa_id(
                                            wa_id=contact_wa_id,
                                            name=profile_name,
                                            meta_app_config=target_config
                                        )
                                        self._handle_message(msg_data, metadata, value, target_config, log_entry, contact)
                                    else:
                                        logger.info(f"Skipping already processed/ignored WebhookEventLog for WAMID: {wamid} (DB ID: {log_entry.id})")
                            
                            elif "statuses" in value:
                                for status_data in value["statuses"]:
                                    wamid = status_data.get("id") # This is the WAMID of the message being updated
                                    status_val = status_data.get("status")
                                    
                                    # Create a more unique identifier for status updates to avoid overwriting.
                                    # A single message (wamid) can have multiple statuses (sent, delivered, read).
                                    status_identifier = f"{wamid}_{status_val}"

                                    log_entry, _ = WebhookEventLog.objects.update_or_create(
                                        event_identifier=status_identifier, app_config=target_config,
                                        defaults={'event_type': 'message_status', 
                                                  **log_defaults_for_change, 'payload': status_data, 
                                                  'processing_status': 'pending'}
                                    )
                                    self.handle_status_update(status_data, metadata, target_config, log_entry)
                            # Add elif for "errors" here similar to above if needed
                            elif "errors" in value:
                                for error_data in value["errors"]:
                                    # This is for errors related to a specific message attempt
                                    error_code = error_data.get('code')
                                    log_id = f"error_{error_code}_{timezone.now().timestamp()}"
                                    log_entry, _ = WebhookEventLog.objects.update_or_create(
                                        event_identifier=log_id, app_config=target_config, event_type='error',
                                        defaults={**log_defaults_for_change, 'payload': error_data, 'processing_status': 'pending'}
                                    )
                                    self.handle_error_notification(error_data, metadata, target_config, log_entry)
                            else:
                                logger.warning(f"Change field is 'messages' but no 'messages' or 'statuses' key. Value keys: {value.keys()}")
                        # Add other field handlers ('message_template_status_update', etc.)
                        elif field == "account_update":
                            log_entry, _ = WebhookEventLog.objects.update_or_create(
                                event_identifier=f"{field}_{value.get('event', 'unknown')}_{entry.get('id', 'unknown')}_{timezone.now().timestamp()}",
                                app_config=target_config, event_type='account_update',
                                defaults={**log_defaults_for_change, 'payload': value, 'processing_status': 'pending'}
                            )
                            self.handle_account_update(value, metadata, target_config, log_entry)
                        elif field == "message_template_status_update":
                            log_entry, _ = WebhookEventLog.objects.update_or_create(
                                event_identifier=f"{field}_{value.get('message_template_id')}_{value.get('event')}",
                                app_config=target_config, event_type='template_status',
                                defaults={**log_defaults_for_change, 'payload': value, 'processing_status': 'pending'}
                            )
                            self.handle_template_status_update(value, metadata, target_config, log_entry)
                        else:
                            generic_event_id = f"{field}_{entry.get('id', 'unknown')}_{change_idx}_{timezone.now().timestamp()}"
                            log_entry, _ = WebhookEventLog.objects.update_or_create(
                                event_identifier=generic_event_id, app_config=target_config, event_type=field or 'unknown_field',
                                defaults={**log_defaults_for_change, 'payload': value, 'processing_status': 'pending'}
                            )
                            logger.warning(f"Unhandled change field '{field}'. Logged with ID {log_entry.id}")
                            self._save_log(log_entry, 'ignored', f"Unhandled field: {field}")


            else: # Other object types
                generic_event_id = f"{payload.get('object', 'unknown_object')}_{timezone.now().timestamp()}"
                log_entry, _ = WebhookEventLog.objects.update_or_create(
                    event_identifier=generic_event_id, app_config=target_config,
                    defaults={**base_log_defaults, 'payload': payload, 'processing_status': 'pending'}
                )
                logger.warning(f"Received webhook for unhandled object type: {payload.get('object')}")
                self._save_log(log_entry, 'ignored', f"Unhandled object: {payload.get('object')}")

            return HttpResponse("EVENT_RECEIVED", status=200)

        except Exception as e: # Catch-all for other unexpected errors during processing
            logger.error(f"General error processing webhook: {e}", exc_info=True)
            current_payload_for_log = payload if 'payload' in locals() else {'raw_error_body': raw_payload_str, 'exception_point': 'general_processing'}
            
            if log_entry and log_entry.pk: # If log_entry was created
                self._save_log(log_entry, 'failed', f"General processing error: {str(e)[:250]}")
            else: # If error happened before log_entry for this specific event part was created
                 WebhookEventLog.objects.create(
                    **base_log_defaults,
                    event_identifier=f"error_{timezone.now().timestamp()}",
                    processing_status='failed',
                    payload=current_payload_for_log,
                    event_type='unhandled_exception',
                    processing_notes=f"General processing error: {str(e)[:250]}"
                )
            return HttpResponse("Internal Server Error processing event.", status=500)

    # _save_log method from your original file
    def _save_log(self, log_entry: WebhookEventLog, status_val: str, notes: str = None):
        old_status = log_entry.processing_status
        log_entry.processing_status = status_val
        if notes:
            log_entry.processing_notes = f"{log_entry.processing_notes}\n{notes}" if log_entry.processing_notes else notes
        log_entry.processed_at = timezone.now()
        try:
            log_entry.save(update_fields=['processing_status', 'processing_notes', 'processed_at'])
            logger.debug(f"WebhookEventLog ID {log_entry.id} status from '{old_status}' to '{status_val}'.")
        except Exception as e:
            logger.error(f"Failed to save WebhookEventLog (ID: {log_entry.pk or 'New'}): {e}", exc_info=True)


    @transaction.atomic
    def _handle_message(self, msg_data: dict, metadata: dict, value_entry: dict, active_config: MetaAppConfig, log_entry: WebhookEventLog, contact):
        # Local imports
        from conversations.models import Message
        from flows.tasks import process_flow_for_message_task
        # Import Contact for type hinting and for the action loop
        from conversations.models import Contact

        whatsapp_message_id = msg_data.get("id")
        logger.info(
            f"Handling message WAMID: {whatsapp_message_id} for Contact ID: {contact.id} "
            f"({contact.whatsapp_id})."
        )

        # --- Start of _handle_message logic (ensure this aligns with your intent) ---
        message_timestamp_str = msg_data.get("timestamp")
        message_timestamp = None
        if message_timestamp_str:
            try: message_timestamp = timezone.make_aware(datetime.fromtimestamp(int(message_timestamp_str)))
            except ValueError: logger.warning(f"Could not parse message timestamp: {message_timestamp_str}")
        if not message_timestamp: message_timestamp = timezone.now()

        incoming_msg_obj, msg_created = Message.objects.update_or_create(
            wamid=whatsapp_message_id,
            defaults={
                'contact': contact,
                'app_config': active_config, # Link message to app config
                'direction': 'in',
                'message_type': msg_data.get("type", "unknown"),
                'content_payload': msg_data,
                'timestamp': message_timestamp,
                'status': 'delivered', # Delivered to your system
                'status_timestamp': message_timestamp,
            }
        )
        if not msg_created:
            logger.info(f"Incoming message with WAMID {whatsapp_message_id} already exists. Updating timestamp. Processing will continue to check flow state.")
            # Potentially update timestamp if newer, or other fields if webhook retries with more info
            incoming_msg_obj.timestamp = message_timestamp
            incoming_msg_obj.content_payload = msg_data # Update payload in case of retry
            incoming_msg_obj.save()
        else:
            logger.info(f"Saved incoming message (WAMID: {whatsapp_message_id}) as DB ID {incoming_msg_obj.id}")
        
        if log_entry and log_entry.pk:
            log_entry.message = incoming_msg_obj # Link log to message
            log_entry.processing_status = 'processing_queued'
            log_entry.save(update_fields=['message', 'processing_status'])
        
        try:
            # --- ARCHITECTURAL CHANGE ---
            # Instead of processing the flow synchronously, queue a Celery task.
            # This makes the webhook response immediate.
            transaction.on_commit(
                lambda: process_flow_for_message_task.delay(incoming_msg_obj.id)
            )
            logger.info(f"Queued process_flow_for_message_task for message {incoming_msg_obj.id}.")

        except Exception as e:
            # This block catches unexpected errors in the message handling logic itself,
            # outside of the `process_message_for_flow` service's internal error handling.
            logger.error(f"Unhandled exception in _handle_message for WAMID {whatsapp_message_id} (Contact: {contact.id}): {e}", exc_info=True)
            if log_entry and log_entry.pk:
                self._save_log(log_entry, 'failed', f"Critical error in webhook handler before queueing: {str(e)[:200]}")
        
        # --- Send Read Receipt ---
        self._send_read_receipt(whatsapp_message_id, active_config)

    def _send_read_receipt(self, wamid: str, app_config: MetaAppConfig, show_typing_indicator: bool = True):
        """
        Dispatches a Celery task to send a read receipt for the given message ID.
        By default, it also shows a typing indicator.
        """
        if not wamid:
            logger.warning(f"Cannot send read receipt: Missing WAMID.")
            return

        send_read_receipt_task.delay(
            wamid=wamid,
            config_id=app_config.id,
            show_typing_indicator=show_typing_indicator
        )
        logger.info(f"Dispatched read receipt task for WAMID {wamid} (Typing: {show_typing_indicator}).")


    # --- Placeholder for other handlers from your original file ---
    def handle_status_update(self, status_data, metadata, app_config, log_entry: WebhookEventLog):
        wamid = status_data.get("id"); status_value = status_data.get("status"); ts_str = status_data.get("timestamp")
        status_ts = timezone.make_aware(datetime.fromtimestamp(int(ts_str))) if ts_str and ts_str.isdigit() else timezone.now()
        logger.info(f"Status Update: WAMID={wamid}, Status='{status_value}'")
        notes = [f"Status for WAMID {wamid} is {status_value}."]
        try: # noqa
            msg_to_update = Message.objects.filter(wamid=wamid, direction='out').first()
            if msg_to_update:
                update_fields_list = ['status', 'status_timestamp']
                msg_to_update.status = status_value
                msg_to_update.status_timestamp = status_ts
                # Extract and store conversation and pricing if present
                if 'conversation' in status_data and isinstance(status_data['conversation'], dict):
                    msg_to_update.conversation_id_from_meta = status_data['conversation'].get('id')
                    update_fields_list.append('conversation_id_from_meta')
                if 'pricing' in status_data and isinstance(status_data['pricing'], dict):
                    msg_to_update.pricing_model_from_meta = status_data['pricing'].get('pricing_model')
                    update_fields_list.append('pricing_model_from_meta')
                msg_to_update.save(update_fields=update_fields_list)
                notes.append("DB record updated.")
                self._save_log(log_entry, 'processed', " ".join(notes))
            else: self._save_log(log_entry, 'ignored', f"No matching outgoing msg for WAMID {wamid}.")
        except Exception as e: logger.error(f"Error updating status for WAMID {wamid}: {e}", exc_info=True); self._save_log(log_entry, 'error', str(e))

    def handle_error_notification(self, error_data, metadata, app_config, log_entry: WebhookEventLog):
        logger.error(f"Received error notification from Meta: {error_data}")
        self._save_log(log_entry, 'processed', f"Meta error logged: {error_data.get('title')}")

    def handle_template_status_update(self, status_data, metadata, app_config, log_entry: WebhookEventLog):
        logger.info(f"Template Status Update: {status_data}")
        self._save_log(log_entry, 'processed', f"Template status '{status_data.get('event')}' for '{status_data.get('message_template_name')}' logged.")
    
    def handle_account_update(self, update_data, metadata, app_config, log_entry: WebhookEventLog):
        event = update_data.get('event')
        logger.info(f"Account Update Received: Event='{event}', Data: {update_data}")
        
        notes = f"Account update event '{event}' received."
        
        # You can add specific logic here for different events, like sending an admin email
        if event == 'DISABLED_UPDATE':
            is_disabled = update_data.get('is_disabled', False)
            if is_disabled:
                logger.critical(f"CRITICAL: WhatsApp Business Account {app_config.waba_id} has been disabled! Reason: {update_data.get('disable_reason')}")
                notes += f" Account DISABLED. Reason: {update_data.get('disable_reason')}. Immediate action required."
            else:
                logger.info(f"Account {app_config.waba_id} is no longer disabled.")
                notes += " Account is no longer disabled."
        
        elif event == 'ACCOUNT_REVIEW_UPDATE':
            decision = update_data.get('decision')
            logger.warning(f"Account review update for {app_config.waba_id}: {decision}. Rejection reason: {update_data.get('rejection_reason')}")
            notes += f" Review decision: {decision}."

        # For now, we just log it as processed.
        self._save_log(log_entry, 'processed', notes)

    # Add other handlers (handle_referral, handle_system_message, handle_flow_response, etc.) as needed,
    # ensuring they call self._save_log(log_entry, status, notes)

    def get(self, request: HttpRequest, *args, **kwargs): # app_id_or_name removed from signature
        # Handles webhook verification challenge from Meta
        # Your original GET logic, ensure active_config is fetched appropriately if path doesn't have app_id_or_name
        active_config = get_active_meta_config()
        if not active_config:
            return HttpResponse("Error: App configuration not found or inactive.", status=404) # Changed to 404

        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        mode = request.GET.get('hub.mode')

        logger.info(f"Webhook GET verification for config '{active_config.name}': mode='{mode}', received_token='{verify_token}', challenge='{challenge}'")

        if mode == 'subscribe' and verify_token == active_config.verify_token and challenge:
            logger.info(f"Webhook successfully verified for app: {active_config.name}.")
            return HttpResponse(challenge, status=200)
        else:
            # More detailed logging for easier debugging
            failure_reasons = []
            if mode != 'subscribe':
                failure_reasons.append(f"mode was '{mode}' not 'subscribe'")
            if verify_token != active_config.verify_token:
                failure_reasons.append("verify_token did not match")
            if not challenge:
                failure_reasons.append("challenge was missing")
            
            logger.warning(
                f"Webhook verification failed for app: {active_config.name}. "
                f"Reason(s): {', '.join(failure_reasons) or 'Unknown'}. "
                f"Received Token: '{verify_token}'"
            )
            return HttpResponse("Error: Verification token mismatch or challenge missing.", status=403)
