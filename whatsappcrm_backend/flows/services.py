# whatsappcrm_backend/flows/services.py
from django.db import models
import ast
import logging
import re
from typing import List, Dict, Any, Optional, Union, Literal

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.apps import apps
from django.forms.models import model_to_dict
from django.db.models.fields.files import ImageFieldFile, FileField
from jinja2 import Environment, select_autoescape, Undefined, pass_context
from django.core.exceptions import ValidationError as DjangoValidationError # Renamed to avoid conflict with Pydantic
from pydantic import ValidationError
from django.conf import settings
from datetime import date, datetime
import re
import uuid
from decimal import Decimal, InvalidOperation
import json

from conversations.models import Contact, Message
from .models import Flow, FlowStep, FlowTransition, ContactFlowState
from notifications.services import queue_notifications_to_users
from customer_data.models import CustomerProfile

# Import Pydantic schemas from the new file
from .schemas import (
    StepConfigSendMessage, StepConfigQuestion, StepConfigAction,
    StepConfigHumanHandover, StepConfigEndFlow, StepConfigSwitchFlow,
    MediaMessageContent, FallbackConfig, InteractiveMessagePayload # Added InteractiveMessagePayload
)

logger = logging.getLogger(__name__)

# --- Dynamic Custom Action Registry ---
class FlowActionRegistry:
    def __init__(self): self._actions = {}
    def register(self, name, func): self._actions[name] = func; logger.info(f"Registered flow action: '{name}'")
    def get(self, name): return self._actions.get(name)
flow_action_registry = FlowActionRegistry()

def _make_context_json_serializable(context: dict) -> dict:
    """
    Recursively cleans a dictionary to ensure all its values are JSON serializable.
    Converts Django model instances to their string representation.
    """
    cleaned_context = {}
    for key, value in context.items():
        if isinstance(value, models.Model):
            cleaned_context[key] = str(value)  # Convert model instance to its string representation
        elif isinstance(value, dict):
            cleaned_context[key] = _make_context_json_serializable(value)
        elif isinstance(value, list):
            # This is a simplified list handling; assumes list doesn't contain complex objects needing deep serialization
            cleaned_context[key] = value
        else:
            cleaned_context[key] = value
    return cleaned_context

def send_group_notification_action(contact: Contact, flow_context: dict, params: dict) -> list:
    """
    Custom flow action to queue notifications for admin user groups.
    """
    group_names = params.get('group_names')
    contact_ids = params.get('contact_ids')
    template_name = params.get('template_name')

    if (not isinstance(group_names, list) and not isinstance(contact_ids, list)) or not template_name:
        logger.error(f"Action 'send_group_notification' for contact {contact.id} is missing 'template_name' and at least one of 'group_names' (list) or 'contact_ids' (list) in params.")
        return []

    # Get the current flow from the context if available
    current_flow_id = flow_context.get('_flow_state', {}).get('current_flow_id')
    related_flow = Flow.objects.filter(pk=current_flow_id).first() if current_flow_id else None

    # Create a JSON-serializable version of the context before passing it to the notification service.
    serializable_context = _make_context_json_serializable(flow_context)

    queue_notifications_to_users(
        template_name=template_name,
        template_context=serializable_context,
        group_names=group_names,
        contact_ids=contact_ids,
        related_contact=contact,
        related_flow=related_flow
    )
    
    logger.info(f"Queued notification for groups {group_names} from flow action for contact {contact.id}.")
    return [] # This action does not return any actions for the main loop

flow_action_registry.register('send_group_notification', send_group_notification_action)

from paynow_integration.services import PaynowService
try:
    from media_manager.models import MediaAsset # For asset_pk lookup
    MEDIA_ASSET_ENABLED = True
except ImportError:
    MEDIA_ASSET_ENABLED = False

# Log MediaAsset status at module load time
if not MEDIA_ASSET_ENABLED:
    logger.warning("MediaAsset model not found or could not be imported. MediaAsset functionality (e.g., 'asset_pk') will be disabled in flows.")

# --- Jinja2 Environment Setup ---
# A custom undefined type for Jinja that doesn't raise an error for missing variables,
# but returns an empty string instead.
class SilentUndefined(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return '' # Return empty string for undefined variables

def strftime_filter(value, format_string='%b %d, %Y'):
    """
    Jinja2 filter to format a date/datetime object or string using strftime.
    """
    if not value:
        return ""
    
    dt_obj = None
    if isinstance(value, str):
        try:
            dt_obj = parse_datetime(value) # Handles ISO format and some others
        except (ValueError, TypeError):
            # If parse_datetime fails, try common date formats
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
                try:
                    dt_obj = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            if not dt_obj:
                return value # Return original string if parsing fails
    elif isinstance(value, (datetime, date)):
        dt_obj = value
    elif value is None:
        return "" # Handle None gracefully
    else:
        # If it's not a string, datetime, or date, return as is
        return value
    
    return dt_obj.strftime(format_string) if dt_obj else value

def truncatewords_filter(value, length=25, end_text='...'):
    """
    Jinja2 filter to truncate a string after a certain number of words.
    """
    if not isinstance(value, str):
        return value
    words = value.split()
    if len(words) <= length:
        return value
    return ' '.join(words[:length]) + end_text

@pass_context
def to_interactive_rows_filter(context, value, row_template=None):
    """
    Jinja2 filter to convert a list of dicts into a JSON string representation
    of interactive message rows. This allows dynamic row generation from context variables.

    Usage: {{ product_list | to_interactive_rows(row_template={'id': '{{ item.sku }}', 'title': '{{ item.name }}'}) }}
    """
    if not isinstance(value, list):
        return "[]"

    # Default template if none is provided, maintaining backward compatibility
    if not isinstance(row_template, dict):
        row_template = {
            "id": "{{ item.sku or item.id }}",
            "title": "{{ item.name }}",
            "description": "{% if item.price is not none %}${{ item.price }}{% endif %}"
        }

    rows_list = []
    for item in value:
        # For each item in the list, render the id, title, and description from the template
        rendered_row = {
            "id": jinja_env.from_string(row_template.get('id', '')).render(item=item),
            "title": jinja_env.from_string(row_template.get('title', '')).render(item=item),
            "description": jinja_env.from_string(row_template.get('description', '')).render(item=item)
        }
        rows_list.append(rendered_row)

    return json.dumps(rows_list)

jinja_env = Environment(
    loader=None, # We're loading templates from strings, not files
    autoescape=select_autoescape(['html', 'xml'], disabled_extensions=('txt',), default_for_string=False),
    undefined=SilentUndefined,
    enable_async=False
)
jinja_env.filters['strftime'] = strftime_filter # Add the custom filter
jinja_env.filters['truncatewords'] = truncatewords_filter # Add the filter
jinja_env.filters['to_interactive_rows'] = to_interactive_rows_filter # Add the new filter
jinja_env.globals['now'] = timezone.now # Make 'now' globally available for date comparisons

def _get_value_from_context_or_contact(variable_path: str, flow_context: dict, contact: Contact) -> Any:
    """
    Resolves a variable path (e.g., 'contact.name', 'flow_context.user_email') to its value.
    Safely accesses attributes on Django models and keys in dictionaries. Does NOT execute methods.
    """
    if not variable_path: return None
    parts = variable_path.split('.')
    current_value = None
    source_object_name = parts[0]

    if source_object_name == 'flow_context':
        current_value = flow_context
        path_to_traverse = parts[1:]
    elif source_object_name == 'contact':
        current_value = contact
        path_to_traverse = parts[1:]
    elif source_object_name == 'customer_profile':
        try:
            current_value = contact.customer_profile # Access related object via Django ORM
            path_to_traverse = parts[1:]
        except (CustomerProfile.DoesNotExist, AttributeError):
            logger.debug(
                f"Contact {contact.id}: CustomerProfile does not exist when accessing '{variable_path}'"
            )
            return None
    else: # Default to flow_context if no recognized prefix
        current_value = flow_context
        path_to_traverse = parts # Use all parts as keys for the context dict

    for i, part in enumerate(path_to_traverse):
        if current_value is None: # If an intermediate part was None, the final value is None
            return None
        try:
            if isinstance(current_value, dict):
                current_value = current_value.get(part)
            elif isinstance(current_value, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current_value):
                    current_value = current_value[index]
                else:
                    return None # Index out of bounds
            elif hasattr(current_value, part): # Check for model field or property
                attr = getattr(current_value, part)
                if callable(attr) and not isinstance(getattr(type(current_value), part, None), property):
                    # This is a method, not a property. Do not call it for security/predictability.
                    logger.warning(
                        f"Contact {contact.id}: Attempted to access a callable method '{part}' "
                        f"via template variable '{variable_path}'. This is not allowed. Returning None."
                    )
                    return None
                current_value = attr # Access property or attribute
            else: # Part not found
                return None
        except Exception as e:
            logger.warning(
                f"Contact {contact.id}: Error accessing path '{'.'.join(path_to_traverse[:i+1])}' "
                f"for variable '{variable_path}': {e}"
            )
            return None
    return current_value

def _resolve_value(template_value: Any, flow_context: dict, contact: Contact) -> Any:
    """
    Resolves a template value using Jinja2, which can be a string, dict, or list.
    Provides 'contact', 'customer_profile', and the flow_context to the template.
    """
    if isinstance(template_value, str):
        # Use Jinja2 for powerful string templating, supporting loops, conditionals, and filters.
        try:
            template = jinja_env.from_string(template_value)
            # The context for Jinja includes the contact, their profile, and the flow context flattened.
            render_context = {
                **flow_context, # type: ignore
                'contact': contact,
                'customer_profile': getattr(contact, 'customer_profile', None)
            }
            return template.render(render_context)
        except Exception as e:
            logger.error(f"Jinja2 template rendering failed for contact {contact.id}: {e}. Template: '{template_value}'", exc_info=False)
            return template_value # Return original on error
    elif isinstance(template_value, dict):
        # Recursively resolve values in a dictionary
        return {k: _resolve_value(v, flow_context, contact) for k, v in template_value.items()}
    elif isinstance(template_value, list):
        # Recursively resolve values in a list
        return [_resolve_value(item, flow_context, contact) for item in template_value]
    
    # For non-string, non-dict, non-list types, return as is
    return template_value

def _resolve_template_components(components_config: list, flow_context: dict, contact: Contact) -> list:
    if not components_config or not isinstance(components_config, list): return []
    try:
        resolved_components_list = json.loads(json.dumps(components_config)) # Deep copy
        for component in resolved_components_list: # type: ignore
            if isinstance(component.get('parameters'), list): # type: ignore
                for param in component['parameters']: # type: ignore
                    # Resolve text for any parameter type that might contain it
                    if 'text' in param and isinstance(param['text'], str): # type: ignore
                        param['text'] = _resolve_value(param['text'], flow_context, contact) # type: ignore
                    
                    # Specific handling for media link in header/body components using image/video/document type parameters
                    param_type = param.get('type') # type: ignore
                    if param_type in ['image', 'video', 'document'] and isinstance(param.get(param_type), dict): # type: ignore
                        media_obj = param[param_type] # type: ignore
                        if 'link' in media_obj and isinstance(media_obj['link'], str): # type: ignore
                             media_obj['link'] = _resolve_value(media_obj['link'], flow_context, contact) # type: ignore
                    
                    # Handle payload for button parameters
                    if component.get('type') == 'button' and param.get('type') == 'payload' and 'payload' in param and isinstance(param['payload'], str): # type: ignore
                         param['payload'] = _resolve_value(param['payload'], flow_context, contact) # type: ignore

                    # Handle currency and date_time fallback_values
                    if param_type == 'currency' and isinstance(param.get('currency'), dict) and 'fallback_value' in param['currency']: # type: ignore
                        param['currency']['fallback_value'] = _resolve_value(param['currency']['fallback_value'], flow_context, contact) # type: ignore
                    if param_type == 'date_time' and isinstance(param.get('date_time'), dict) and 'fallback_value' in param['date_time']: # type: ignore
                        param['date_time']['fallback_value'] = _resolve_value(param['date_time']['fallback_value'], flow_context, contact) # type: ignore

        return resolved_components_list
    except Exception as e:
        logger.error(f"Error resolving template components: {e}. Config: {components_config}", exc_info=True)
        return components_config

def _clear_contact_flow_state(contact: Contact, error: bool = False):
    deleted_count, _ = ContactFlowState.objects.filter(contact=contact).delete()
    if deleted_count > 0:        
        logger.info(f"Contact {contact.id}: Cleared flow state ({contact.whatsapp_id})." + (" Due to an error." if error else ""))

def _initiate_paynow_giving_payment(contact: Contact, amount_str: str, payment_type: str, payment_method: str, phone_number: str, email: str, currency: str, notes: str) -> dict:
    """
    Placeholder for initiating a Paynow payment.
    This function should be implemented with the actual Paynow integration logic.
    """
    logger.warning(
        f"Placeholder function '_initiate_paynow_giving_payment' called for contact {contact.id}. "
        f"Amount: {amount_str}, Phone: {phone_number}. "
        "This should be replaced with actual Paynow integration logic."
    )
    # In a real implementation, you would:
    # 1. Call the PaynowService to create a transaction.
    # 2. Get a response from Paynow.
    # 3. Update the context with the result.
    # For now, we simulate a success.
    return {
        "paynow_initiation_success": True,
        "paynow_initiation_error": None
    }

def _execute_step_actions(step: FlowStep, contact: Contact, flow_context: dict, suppress_prompt: bool = False) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    actions_to_perform = []
    raw_step_config = step.config or {} 
    current_step_context = flow_context.copy() 

    logger.debug(
        f"Contact {contact.id}: Executing actions for step '{step.name}' (ID: {step.id}, Type: {step.step_type}). "
        f"Raw Config: {raw_step_config}"
    )

    if step.step_type == 'send_message':
        try:
            # The config for a 'send_message' step IS the message config.
            # The previous implementation incorrectly expected it to be nested under a 'message_config' key.
            # This change aligns the service with the model and serializer validations.
            message_config_data = raw_step_config
            if not message_config_data:
                logger.error(f"Contact {contact.id}: 'send_message' step '{step.name}' (ID: {step.id}) has an empty config. Step cannot be executed.")
                return actions_to_perform, current_step_context

            send_message_config = StepConfigSendMessage.model_validate(message_config_data)
            actual_message_type = send_message_config.message_type
            final_api_data_structure = {}

            if actual_message_type == "text" and send_message_config.text:
                text_content = send_message_config.text
                resolved_body = _resolve_value(text_content.body, current_step_context, contact)
                final_api_data_structure = {'body': resolved_body, 'preview_url': text_content.preview_url}
            
            elif actual_message_type in ['image', 'document', 'audio', 'video', 'sticker'] and getattr(send_message_config, actual_message_type):
                media_conf: MediaMessageContent = getattr(send_message_config, actual_message_type)
                media_data_to_send = {}
                
                valid_source_found = False
                if MEDIA_ASSET_ENABLED and media_conf.asset_pk:
                    try:
                        asset = MediaAsset.objects.get(pk=media_conf.asset_pk)
                        if asset.status == 'synced' and asset.whatsapp_media_id and not asset.is_whatsapp_id_potentially_expired():
                            media_data_to_send['id'] = asset.whatsapp_media_id
                            valid_source_found = True
                            logger.info(f"Contact {contact.id}: Using MediaAsset {asset.pk} ('{asset.name}') with WA ID: {asset.whatsapp_media_id} for step {step.id}.")
                        else: 
                            logger.warning(f"Contact {contact.id}: MediaAsset {asset.pk} ('{asset.name}') not usable for step {step.id} (Status: {asset.status}, Expired: {asset.is_whatsapp_id_potentially_expired()}). Trying direct id/link from config.")
                    except MediaAsset.DoesNotExist:
                        logger.error(f"Contact {contact.id}: MediaAsset pk={media_conf.asset_pk} not found for step {step.id}. Trying direct id/link from config.")
                
                if not valid_source_found: # Try direct id or link if asset_pk didn't work or wasn't provided
                    if media_conf.id:
                        media_data_to_send['id'] = _resolve_value(media_conf.id, current_step_context, contact)
                        valid_source_found = True
                    elif media_conf.link:
                        resolved_link = _resolve_value(media_conf.link, current_step_context, contact)
                        # If the link is relative (e.g., from Django's media files), make it absolute.
                        if resolved_link and resolved_link.startswith('/'):
                            domain = getattr(settings, 'BACKEND_DOMAIN_FOR_CSP', None)
                            if not domain:
                                logger.error(f"Contact {contact.id}: Cannot form absolute URL for media link '{resolved_link}' because BACKEND_DOMAIN_FOR_CSP is not set in settings.")
                                resolved_link = None # Prevent sending a broken link
                            else:
                                resolved_link = f"https://{domain}{resolved_link}"
                        
                        if resolved_link:
                            media_data_to_send['link'] = resolved_link
                            valid_source_found = True
                
                if not valid_source_found:
                    logger.error(f"Contact {contact.id}: No valid media source (asset_pk, id, or link) for {actual_message_type} in step '{step.name}' (ID: {step.id}).")
                else:
                    if media_conf.caption:
                        media_data_to_send['caption'] = _resolve_value(media_conf.caption, current_step_context, contact)
                    if actual_message_type == 'document' and media_conf.filename:
                        media_data_to_send['filename'] = _resolve_value(media_conf.filename, current_step_context, contact)
                    final_api_data_structure = media_data_to_send
            
            elif actual_message_type == "interactive" and send_message_config.interactive:
                interactive_payload_validated = send_message_config.interactive # Already validated by StepConfigSendMessage
                interactive_payload_dict = interactive_payload_validated.model_dump(exclude_none=True, by_alias=True)
                
                # Resolve templates directly within the dictionary structure
                final_api_data_structure = _resolve_value(interactive_payload_dict, current_step_context, contact)

            elif actual_message_type == "template" and send_message_config.template:
                template_payload_validated = send_message_config.template
                template_payload_dict = template_payload_validated.model_dump(exclude_none=True, by_alias=True)
                if 'components' in template_payload_dict and template_payload_dict['components']:
                    template_payload_dict['components'] = _resolve_template_components(
                        template_payload_dict['components'], current_step_context, contact
                    )
                final_api_data_structure = template_payload_dict
            
            elif actual_message_type == "contacts" and send_message_config.contacts:
                contacts_list_of_objects = send_message_config.contacts
                contacts_list_of_dicts = [c.model_dump(exclude_none=True, by_alias=True) for c in contacts_list_of_objects]
                resolved_contacts = _resolve_value(contacts_list_of_dicts, current_step_context, contact)
                final_api_data_structure = {"contacts": resolved_contacts}

            elif actual_message_type == "location" and send_message_config.location:
                location_obj = send_message_config.location
                location_dict = location_obj.model_dump(exclude_none=True, by_alias=True)
                final_api_data_structure = {"location": _resolve_value(location_dict, current_step_context, contact)}

            if final_api_data_structure:
                actions_to_perform.append({
                    'type': 'send_whatsapp_message',
                    'recipient_wa_id': contact.whatsapp_id,
                    'message_type': actual_message_type,
                    'data': final_api_data_structure
                })
            elif actual_message_type: # If type was specified but no payload generated
                 logger.warning(f"Contact {contact.id}: No data payload generated for message_type '{actual_message_type}' in step '{step.name}' (ID: {step.id}). Pydantic Config: {send_message_config.model_dump_json(indent=2) if send_message_config else None}")

        except ValidationError as e:
            logger.error(f"Contact {contact.id}: Pydantic validation error for 'send_message' step '{step.name}' (ID: {step.id}) config: {e.errors()}. Raw config: {raw_step_config}", exc_info=False)
        except Exception as e:
            logger.error(f"Contact {contact.id}: Unexpected error processing 'send_message' step '{step.name}' (ID: {step.id}): {e}", exc_info=True)

    elif step.step_type == 'question':
        try:
            question_config = StepConfigQuestion.model_validate(raw_step_config)
            if question_config.message_config and not suppress_prompt: # Only send prompt if not suppressed
                try:
                    temp_msg_pydantic_config = StepConfigSendMessage.model_validate(question_config.message_config)
                    # The config for a send_message step is the message config itself (flat structure).
                    dummy_config = temp_msg_pydantic_config.model_dump(exclude_none=True, by_alias=True)
                    dummy_send_step = FlowStep(
                        name=f"{step.name}_prompt", step_type="send_message", config=dummy_config
                    )
                    send_actions, _ = _execute_step_actions(dummy_send_step, contact, current_step_context)
                    actions_to_perform.extend(send_actions)
                except ValidationError as ve:
                    logger.error(f"Contact {contact.id}: Pydantic validation error for 'message_config' within 'question' step '{step.name}' (ID: {step.id}): {ve.errors()}", exc_info=False)
            
            if question_config.reply_config: # This part is always active for a question step
                current_step_context['_question_awaiting_reply_for'] = {
                    'variable_name': question_config.reply_config.save_to_variable,
                    'expected_type': question_config.reply_config.expected_type,
                    'validation_regex': question_config.reply_config.validation_regex,
                    'original_question_step_id': step.id 
                }
                logger.debug(f"Step '{step.name}' is a question, awaiting reply for: {question_config.reply_config.save_to_variable}")
        except ValidationError as e:
            logger.error(f"Contact {contact.id}: Pydantic validation for 'question' step '{step.name}' (ID: {step.id}) failed: {e.errors()}", exc_info=False)

    elif step.step_type == 'action':
        try:
            action_step_config = StepConfigAction.model_validate(raw_step_config)
            for action_item_conf in action_step_config.actions_to_run:
                action_type = action_item_conf.action_type
                # Handle custom actions registered in flow_action_registry
                custom_action_func = flow_action_registry.get(action_type)
                if custom_action_func:
                    resolved_params = _resolve_value(action_item_conf.params_template or {}, current_step_context, contact)
                    custom_actions = custom_action_func(contact, current_step_context, resolved_params)
                    actions_to_perform.extend(custom_actions)
                    continue # Skip default handling if it's a custom action
                if action_type == 'set_context_variable' and action_item_conf.variable_name is not None:
                    resolved_value = _resolve_value(action_item_conf.value_template, current_step_context, contact)
                    current_step_context[action_item_conf.variable_name] = resolved_value
                    logger.info(f"Contact {contact.id}: Action in step {step.id} set context var '{action_item_conf.variable_name}' to '{resolved_value}'.")
                elif action_type == 'update_contact_field' and action_item_conf.field_path is not None:
                    resolved_value = _resolve_value(action_item_conf.value_template, current_step_context, contact)
                    _update_contact_data(contact, action_item_conf.field_path, resolved_value)
                elif action_type == 'update_customer_profile' and action_item_conf.fields_to_update is not None:
                    resolved_fields_to_update = _resolve_value(action_item_conf.fields_to_update, current_step_context, contact) # type: ignore
                    _update_customer_profile_data(contact, resolved_fields_to_update, current_step_context)
                elif action_type == 'send_admin_notification':
                    # This action is deprecated. We now use 'send_group_notification'.
                    # For backward compatibility, we'll map it to the new system.
                    logger.warning("The 'send_admin_notification' action is deprecated. Please use 'send_group_notification' with a 'template_name' instead.")
                    queue_notifications_to_users(
                        group_names=["Technical Admin"],
                        message_body=_resolve_value(action_item_conf.message_template, current_step_context, contact),
                        related_contact=contact
                    )
                elif action_type == 'query_model':
                    app_label = action_item_conf.app_label
                    model_name = action_item_conf.model_name
                    variable_name = action_item_conf.variable_name
                    
                    if not app_label or not model_name or not variable_name:
                        logger.error(f"Contact {contact.id}: 'query_model' action in step {step.id} is missing required fields. Skipping.")
                        continue
                    
                    try:
                        Model = apps.get_model(app_label, model_name)

                        filters_template = action_item_conf.filters_template or {}
                        # --- FIX: Resolve the entire filters dictionary first ---
                        # This ensures that values like "{{ context_var }}" are resolved before being used.
                        resolved_filters = _resolve_value(filters_template, current_step_context, contact)
                        
                        if not isinstance(resolved_filters, dict):
                            logger.warning(f"Contact {contact.id}: 'filters_template' for query_model did not resolve to a dictionary. Using empty filters. Resolved value: {resolved_filters}")
                            filters = {}
                        
                        # --- NEW LOGIC TO SUPPORT __not_in ---
                        exclude_filters = {}
                        final_filters = {}
                        for key, value in resolved_filters.items():
                            if key.endswith('__not_in'):
                                new_key = key[:-8] + '__in' # FIX: Use double underscore for the 'in' lookup
                                try:
                                    # ast.literal_eval is a safe way to evaluate a string containing a Python literal.
                                    parsed_value = ast.literal_eval(value) if isinstance(value, str) else value
                                    if not isinstance(parsed_value, list):
                                        raise TypeError("Value for __not_in did not evaluate to a list.")
                                    exclude_filters[new_key] = parsed_value
                                except (ValueError, SyntaxError, TypeError) as e:
                                    logger.warning(f"Could not parse value for '{key}' in query_model: {value}. Error: {e}. Skipping this filter.")
                            else:
                                final_filters[key] = value
                        
                        queryset = Model.objects.filter(**final_filters)
                        if exclude_filters:
                            queryset = queryset.exclude(**exclude_filters)
                            
                        order_by_fields = action_item_conf.order_by
                        if order_by_fields and isinstance(order_by_fields, list):
                            queryset = queryset.order_by(*order_by_fields)
                            
                        if action_item_conf.limit is not None and isinstance(action_item_conf.limit, int):
                            queryset = queryset[:action_item_conf.limit]
                            
                        # --- OPTIMIZATION: Use .values() for performance ---
                        fields_to_return = getattr(action_item_conf, 'fields_to_return', None)
                        if fields_to_return and isinstance(fields_to_return, list):
                            # OPTIMIZED PATH: Use .values() for much faster serialization. This is the recommended approach.
                            results_list = list(queryset.values(*fields_to_return))
                            # .values() handles Decimal and basic types. Dates need manual conversion for JSON.
                            for item in results_list:
                                for key, value in item.items():
                                    if isinstance(value, (date, datetime)):
                                        item[key] = value.isoformat()
                                    elif isinstance(value, Decimal):
                                        item[key] = str(value) # Convert Decimal to string for JSON
                                    elif isinstance(value, uuid.UUID):
                                        item[key] = str(value)
                        else:
                            # BACKWARD COMPATIBILITY PATH: Use model_to_dict (slower)
                            logger.warning(f"Contact {contact.id}: 'query_model' in step {step.id} is not using 'fields_to_return'. "
                                           f"Using slower model_to_dict. Consider specifying fields for performance.")
                            results_list = []
                            for obj in queryset:
                                dict_obj = model_to_dict(obj)
                                # Post-process to ensure all values are JSON serializable
                                for key, value in dict_obj.items():
                                    if isinstance(value, (date, datetime)): dict_obj[key] = value.isoformat()
                                    elif isinstance(value, Decimal): dict_obj[key] = str(value)
                                    elif isinstance(value, (ImageFieldFile, FileField)):
                                        try: dict_obj[key] = value.url if value else None
                                        except ValueError: dict_obj[key] = None
                                results_list.append(dict_obj)
                            
                        current_step_context[variable_name] = results_list
                        logger.info(f"Contact {contact.id}: Action in step {step.id} queried {model_name} and stored {len(results_list)} items in '{variable_name}'.")
                    except LookupError:
                        logger.error(f"Contact {contact.id}: 'query_model' action in step {step.id} failed. Model '{app_label}.{model_name}' not found.")
                    except Exception as e:
                        logger.error(f"Contact {contact.id}: 'query_model' action in step {step.id} failed with error: {e}", exc_info=True)
                elif action_type == 'create_model_instance':
                    app_label = action_item_conf.app_label
                    model_name = action_item_conf.model_name
                    fields_template = action_item_conf.fields_template
                    save_to_variable = action_item_conf.save_to_variable

                    if not app_label or not model_name or not fields_template:
                        logger.error(f"Contact {contact.id}: 'create_model_instance' action in step {step.id} is missing required fields. Skipping.")
                        continue
                    
                    try:
                        Model = apps.get_model(app_label, model_name)
                        resolved_fields = _resolve_value(fields_template, current_step_context, contact)
                        
                        # Special handling for foreign keys to the current customer's profile
                        if 'customer' in resolved_fields and resolved_fields['customer'] == 'current':
                            if hasattr(contact, 'customer_profile'):
                                resolved_fields['customer'] = contact.customer_profile
                            else:
                                logger.error(f"Contact {contact.id} does not have a customer_profile. Cannot create {model_name}.")
                                continue
                        
                        # Special handling for location data
                        if 'latitude' in resolved_fields and 'longitude' in resolved_fields:
                            try:
                                resolved_fields['latitude'] = Decimal(resolved_fields['latitude']) if resolved_fields['latitude'] is not None else None
                                resolved_fields['longitude'] = Decimal(resolved_fields['longitude']) if resolved_fields['longitude'] is not None else None
                            except (InvalidOperation, TypeError):
                                logger.warning(f"Could not convert lat/lon to Decimal for {model_name}. Skipping update for these fields.")
                                resolved_fields.pop('latitude', None)
                                resolved_fields.pop('longitude', None)

                        instance = Model.objects.create(**resolved_fields)
                        logger.info(f"Contact {contact.id}: Created new {model_name} instance with ID {instance.pk}.")

                        if save_to_variable:
                            instance_dict = model_to_dict(instance)
                            # Post-process to ensure all values are JSON serializable before saving to context.
                            for key, value in instance_dict.items():
                                if isinstance(value, Decimal):
                                    instance_dict[key] = str(value)
                                elif isinstance(value, (datetime, date)):
                                    instance_dict[key] = value.isoformat()
                                elif isinstance(value, (ImageFieldFile, FileField)):
                                    try:
                                        instance_dict[key] = value.url if value else None
                                    except ValueError:
                                        instance_dict[key] = None
                            
                            # Manually add the primary key because model_to_dict excludes non-editable fields by default.
                            # Also ensure UUIDs are converted to strings for JSON serialization.
                            if isinstance(instance.pk, uuid.UUID):
                                instance_dict['id'] = str(instance.pk)
                            else:
                                instance_dict['id'] = instance.pk
                            current_step_context[save_to_variable] = instance_dict
                            logger.info(f"Contact {contact.id}: Saved created instance to context variable '{save_to_variable}'.")
                    except LookupError:
                        logger.error(f"Contact {contact.id}: 'create_model_instance' action failed. Model '{app_label}.{model_name}' not found.")
                    except Exception as e:
                        logger.error(f"Contact {contact.id}: 'create_model_instance' action failed with error: {e}", exc_info=True)
                else:
                    logger.warning(f"Contact {contact.id}: Unknown or misconfigured action_type '{action_type}' in step '{step.name}' (ID: {step.id}).")
        except ValidationError as e:
            logger.error(f"Contact {contact.id}: Pydantic validation for 'action' step '{step.name}' (ID: {step.id}) failed: {e.errors()}", exc_info=False)

    elif step.step_type == 'switch_flow':
        try:
            switch_config = StepConfigSwitchFlow.model_validate(raw_step_config)
            
            # Start with the initial context from the config and resolve any templates in it
            initial_context = _resolve_value(switch_config.initial_context_template or {}, current_step_context, contact)
            if not isinstance(initial_context, dict):
                initial_context = {}

            # If a keyword is specified, add it to the context being passed to the new flow
            if switch_config.trigger_keyword_to_pass:
                initial_context['simulated_trigger_keyword'] = switch_config.trigger_keyword_to_pass

            # Resolve the target flow name as a template to allow for dynamic switching
            resolved_target_flow_name = _resolve_value(switch_config.target_flow_name, current_step_context, contact)
            if not resolved_target_flow_name:
                logger.error(f"Contact {contact.id}: 'switch_flow' step '{step.name}' target_flow_name resolved to an empty value. Cannot switch. Template: '{switch_config.target_flow_name}'")
                return actions_to_perform, current_step_context

            actions_to_perform.append({
                'type': '_internal_command_switch_flow',
                'target_flow_name': resolved_target_flow_name,
                'initial_context': initial_context
            })
            logger.info(f"Contact {contact.id}: Step '{step.name}' queued switch to flow '{resolved_target_flow_name}'.")
        except ValidationError as e:
            logger.error(f"Contact {contact.id}: Pydantic validation for 'switch_flow' step '{step.name}' (ID: {step.id}) failed: {e.errors()}", exc_info=False)

    elif step.step_type == 'end_flow':
        try:
            end_flow_config = StepConfigEndFlow.model_validate(raw_step_config)
            if end_flow_config.message_config:
                try:
                    final_msg_pydantic_config = StepConfigSendMessage.model_validate(end_flow_config.message_config)
                    # The config for a send_message step is the message config itself (flat structure).
                    dummy_config = final_msg_pydantic_config.model_dump(exclude_none=True, by_alias=True)
                    dummy_end_msg_step = FlowStep(
                        name=f"{step.name}_final_msg", step_type="send_message", config=dummy_config
                    )
                    send_actions, _ = _execute_step_actions(dummy_end_msg_step, contact, current_step_context)
                    actions_to_perform.extend(send_actions)
                except ValidationError as ve:
                     logger.error(f"Contact {contact.id}: Pydantic validation for 'message_config' in 'end_flow' step '{step.name}' (ID: {step.id}): {ve.errors()}", exc_info=False)
            logger.info(f"Contact {contact.id}: Executing 'end_flow' step '{step.name}' (ID: {step.id}).")
            actions_to_perform.append({'type': '_internal_command_clear_flow_state'})
        except ValidationError as e:
            logger.error(f"Contact {contact.id}: Pydantic validation for 'end_flow' step '{step.name}' (ID: {step.id}) config: {e.errors()}", exc_info=False)

    elif step.step_type == 'human_handover':
        try:
            handover_config = StepConfigHumanHandover.model_validate(raw_step_config)
            logger.info(f"Executing 'human_handover' step '{step.name}'.")
            if handover_config.pre_handover_message_text and not suppress_prompt: # Avoid sending pre-handover message on re-execution/fallback
                resolved_msg = _resolve_value(handover_config.pre_handover_message_text, current_step_context, contact)
                actions_to_perform.append({'type': 'send_whatsapp_message', 'recipient_wa_id': contact.whatsapp_id, 'message_type': 'text', 'data': {'body': resolved_msg}})
            
            contact.needs_human_intervention = True
            contact.intervention_requested_at = timezone.now()
            contact.save(update_fields=['needs_human_intervention', 'intervention_requested_at'])
            logger.info(f"Contact {contact.id} ({contact.whatsapp_id}) flagged for human intervention.")
            notification_info = _resolve_value(handover_config.notification_details or f"Contact {contact.name or contact.whatsapp_id} requires help.", current_step_context, contact)
            logger.info(f"HUMAN INTERVENTION NOTIFICATION: {notification_info}. Context: {current_step_context}")
            actions_to_perform.append({'type': '_internal_command_clear_flow_state'})
        except ValidationError as e:
            logger.error(f"Contact {contact.id}: Pydantic validation for 'human_handover' step '{step.name}' (ID: {step.id}) failed: {e.errors()}", exc_info=False)

    elif step.step_type in ['condition', 'wait_for_reply', 'start_flow_node']: # 'wait_for_reply' is more a state than an executable step here
        logger.debug(f"'{step.step_type}' step '{step.name}' processed. No direct actions from this function, logic handled by transitions or flow control.")
    else:
        logger.warning(f"Unhandled step_type: '{step.step_type}' for step '{step.name}'.")

    return actions_to_perform, current_step_context


def _create_human_handover_actions(contact: Contact, message_text: str) -> List[Dict[str, Any]]:
    """
    Creates a standard set of actions for handing a conversation over to a human agent.
    This centralizes the handover logic to keep the code DRY.
    """
    actions = []
    actions.append({
        'type': 'send_whatsapp_message',
        'recipient_wa_id': contact.whatsapp_id,
        'message_type': 'text',
        'data': {'body': message_text}
    })
    
    contact.needs_human_intervention = True
    contact.intervention_requested_at = timezone.now()
    contact.save(update_fields=['needs_human_intervention', 'intervention_requested_at'])
    
    # Queue a WhatsApp notification to the admin team
    queue_notifications_to_users(
        template_name='human_handover_flow',
        group_names=["Technical Admin"],
        related_contact=contact,
        template_context={'last_bot_message': message_text}
    )

    actions.append({'type': '_internal_command_clear_flow_state'})
    return actions

def _handle_fallback(current_step: FlowStep, contact: Contact, flow_context: dict, contact_flow_state: ContactFlowState) -> List[Dict[str, Any]]:
    """
    Handles the logic when no transition condition is met from a step.
    This can be due to an invalid user reply to a question, or a logical dead-end in the flow.
    """
    actions_to_perform = []
    updated_context = flow_context.copy()
    try:
        fallback_config = FallbackConfig.model_validate(current_step.config.get('fallback_config', {}) if isinstance(current_step.config, dict) else {})
    except ValidationError as e:
        logger.warning(f"Invalid fallback_config for step {current_step.id}. Using defaults. Errors: {e.errors()}")
        fallback_config = FallbackConfig()

    # Scenario 1: The step was a question, and the user's reply was invalid.
    if current_step.step_type == 'question':
        max_retries = fallback_config.max_retries
        current_fallback_count = updated_context.get('_fallback_count', 0)
 
        if fallback_config.action == 're_prompt' and current_fallback_count < max_retries:
            logger.info(f"Fallback: Re-prompting question step '{current_step.name}' for contact {contact.id} (Attempt {current_fallback_count + 1}/{max_retries}).")
            updated_context['_fallback_count'] = current_fallback_count + 1
 
            # Send a prefix message before re-sending the prompt. Use the configured message, or a generic one.
            prefix_message_text = fallback_config.re_prompt_message_text or "I'm sorry, that wasn't a valid response. Let's try that again."
            resolved_prefix_text = _resolve_value(prefix_message_text, updated_context, contact)
            actions_to_perform.append({
                'type': 'send_whatsapp_message', 'recipient_wa_id': contact.whatsapp_id,
                'message_type': 'text', 'data': {'body': resolved_prefix_text}
            })

            # Now, re-execute the original question step to send its prompt again.
            # The `suppress_prompt=False` (default) ensures the prompt message is sent.
            step_actions, re_executed_context = _execute_step_actions(current_step, contact, updated_context, suppress_prompt=False)
            actions_to_perform.extend(step_actions)
            updated_context = re_executed_context
 
            # Save the updated context (with incremented fallback_count) and keep the user in the step
            contact_flow_state.flow_context_data = updated_context
            contact_flow_state.save(update_fields=['flow_context_data', 'last_updated_at'])
            return actions_to_perform
        else: # Retries exhausted or action is not 're_prompt'
            action_after_retries = fallback_config.action_after_retries
            if action_after_retries:
                logger.info(f"Fallback retries exhausted for step '{current_step.name}'. Executing configured action_after_retries: '{action_after_retries}'.")
                # Create a dummy step to execute the final fallback action
                dummy_fallback_step = FlowStep(
                    name=f"{current_step.name}_fallback_action",
                    step_type=action_after_retries,
                    config=fallback_config.config_after_retries or {}
                )
                return _execute_step_actions(dummy_fallback_step, contact, updated_context)[0]
            else:
                # ROBUSTNESS: Default behavior after retries is now human handover, not silent exit.
                logger.warning(f"Fallback retries exhausted for step '{current_step.name}' and no 'action_after_retries' defined. Defaulting to human handover for contact {contact.id}.")
                handover_message = "I'm still having trouble understanding. I'm connecting you with a team member who can assist you shortly."
                return _create_human_handover_actions(contact, handover_message)
 
    # Scenario 2: It's a non-question step with no valid transition (a "dead end").
    else:
        logger.error(
            f"CRITICAL: Flow for contact {contact.id} reached a dead end at step '{current_step.name}' (type: {current_step.step_type}). "
            "No valid transition was found. This indicates a flow design issue. Initiating human handover as a safe default."
        )
        # This path directly triggers handover with a clear message to the user.
        handover_message = "Apologies, I've encountered a technical issue and can't continue. I'm alerting a team member to assist you."
        return _create_human_handover_actions(contact, handover_message)

def _trigger_new_flow(contact: Contact, message_data: dict, incoming_message_obj: Message) -> bool:
    """
    Finds and sets up the initial state for a new flow based on a trigger keyword.
    This function does NOT execute the first step; it only creates the state.
    The main processing loop is responsible for all step executions.

    Returns:
        True if a flow was triggered, False otherwise.
    """
    message_text_body = message_data.get('text', {}).get('body', '').strip() # Keep original case for extraction
    message_text_lower = message_text_body.lower()

    triggered_flow = None
    initial_context = {} # To hold any data extracted from the trigger
    
    active_flows = Flow.objects.filter(is_active=True).order_by('name')

    if message_text_body:  # Only attempt keyword trigger if there's text
        for flow_candidate in active_flows:
            if isinstance(flow_candidate.trigger_keywords, list):
                for keyword in flow_candidate.trigger_keywords:
                    if keyword.strip().lower() in message_text_lower and (not hasattr(contact, 'flow_state')):
                        triggered_flow = flow_candidate
                        
                        # --- DYNAMIC DATA EXTRACTION FROM TRIGGER ---
                        trigger_conf = triggered_flow.trigger_config or {}
                        extraction_regex = trigger_conf.get("extraction_regex")
                        context_var_name = trigger_conf.get("context_variable")

                        if extraction_regex and context_var_name:
                            try:
                                match = re.search(extraction_regex, message_text_body)
                                if match and match.groups():
                                    extracted_data = match.group(1) # Use the first capturing group
                                    initial_context[context_var_name] = extracted_data.strip()
                                    logger.info(f"Extracted '{extracted_data.strip()}' into '{context_var_name}' from trigger for flow '{flow_candidate.name}'.")
                            except re.error as e:
                                logger.error(f"Invalid extraction_regex for flow '{flow_candidate.name}': {e}")

                        logger.info(f"Keyword '{keyword}' triggered flow '{flow_candidate.name}' for contact {contact.whatsapp_id}.")
                        break
            if triggered_flow:
                break

    if triggered_flow:
        entry_point_step = FlowStep.objects.filter(flow=triggered_flow, is_entry_point=True).first()
        if entry_point_step:
            logger.info(f"Setting up new flow '{triggered_flow.name}' for contact {contact.whatsapp_id} at entry step '{entry_point_step.name}'.")

            _clear_contact_flow_state(contact)

            ContactFlowState.objects.create(
                contact=contact,
                current_flow=triggered_flow,
                current_step=entry_point_step,
                flow_context_data=initial_context, # Pass the extracted context
                started_at=timezone.now()
            )
            return True
        else:
            logger.error(f"Flow '{triggered_flow.name}' is active but has no entry point step defined.")
            return False

    logger.info(f"No active flow triggered for contact {contact.whatsapp_id} with message: {message_text_body[:100] if message_text_body else message_data.get('type')}")
    return False


def _evaluate_transition_condition(transition: FlowTransition, contact: Contact, message_data: dict, flow_context: dict, incoming_message_obj: Message) -> bool:
    config = transition.condition_config
    if not isinstance(config, dict):
        logger.warning(f"Transition {transition.id} has invalid condition_config (not a dict): {config}")
        return False
    condition_type = config.get('type')
    logger.debug(f"Contact {contact.id}, Flow {transition.current_step.flow.id}, Step {transition.current_step.id}: Evaluating condition type '{condition_type}' for transition {transition.id}. Context: {flow_context}, Message Type: {message_data.get('type')}")

    if not condition_type: return False # No condition type means no specific condition to evaluate beyond default
    if condition_type == 'always_true': return True

    user_text = ""
    if message_data.get('type') == 'text' and isinstance(message_data.get('text'), dict):
        user_text = message_data.get('text', {}).get('body', '').strip()

    interactive_reply_id = None
    nfm_response_data = None 
    if message_data.get('type') == 'interactive' and isinstance(message_data.get('interactive'), dict):
        interactive_payload = message_data.get('interactive', {})
        interactive_type_from_payload = interactive_payload.get('type')
        if interactive_type_from_payload == 'button_reply' and isinstance(interactive_payload.get('button_reply'), dict):
            interactive_reply_id = interactive_payload.get('button_reply', {}).get('id')
        elif interactive_type_from_payload == 'list_reply' and isinstance(interactive_payload.get('list_reply'), dict):
            interactive_reply_id = interactive_payload.get('list_reply', {}).get('id')
        elif interactive_type_from_payload == 'nfm_reply' and isinstance(interactive_payload.get('nfm_reply'), dict):
            nfm_payload = interactive_payload.get('nfm_reply', {})
            response_json_str = nfm_payload.get('response_json')
            if response_json_str:
                try:
                    nfm_response_data = json.loads(response_json_str)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse nfm_reply response_json for transition {transition.id}")
    
    # --- Condition Implementations ---
    value_for_condition = config.get('value') # Get expected value for comparison

    if condition_type == 'user_reply_matches_keyword':
        keyword = str(config.get('keyword', '')).strip()
        if not keyword: return False # Cannot match empty keyword
        case_sensitive = config.get('case_sensitive', False)
        return (keyword == user_text) if case_sensitive else (keyword.lower() == user_text.lower())
    
    elif condition_type == 'user_reply_contains_keyword':
        keyword = str(config.get('keyword', '')).strip()
        if not keyword: return False
        case_sensitive = config.get('case_sensitive', False)
        return (keyword in user_text) if case_sensitive else (keyword.lower() in user_text.lower())
    
    elif condition_type == 'interactive_reply_id_equals':
        return interactive_reply_id is not None and interactive_reply_id == str(value_for_condition)
    
    elif condition_type == 'message_type_is':
        return message_data.get('type') == str(value_for_condition) # Compare with expected message_type
    
    elif condition_type == 'user_reply_matches_regex':
        regex = config.get('regex')
        if regex and user_text:
            try: return bool(re.match(regex, user_text))
            except re.error as e: logger.error(f"Invalid regex in transition {transition.id}: {regex}. Error: {e}"); return False
        return False
        
    elif condition_type == 'variable_equals':
        variable_name = config.get('variable_name')
        if variable_name is None: return False
        actual_value = _get_value_from_context_or_contact(variable_name, flow_context, contact)
        
        # --- NEW LOGIC ---
        # If the expected value is an empty string, also treat None as a match.
        # This makes the condition more intuitive for checking "is empty or not set".
        if value_for_condition == "" and actual_value is None:
            result = True
        else:
            # Original comparison logic
            result = str(actual_value) == str(value_for_condition)
        # --- END NEW LOGIC ---

        logger.debug(
            f"Contact {contact.id}, Flow {transition.current_step.flow.id}, Step {transition.current_step.id}: "
            f"Condition 'variable_equals' check for '{variable_name}'. "
            f"Actual: '{actual_value}' (type: {type(actual_value).__name__}), "
            f"Expected: '{value_for_condition}' (type: {type(value_for_condition).__name__}). "
            f"Result: {result}"
        )
        return result
        
    elif condition_type == 'variable_exists':
        variable_name_template = config.get('variable_name')
        if variable_name_template is None: return False
        # Resolve the variable name itself as a template to handle dynamic paths like 'list.{{ index }}'
        resolved_variable_path = _resolve_value(variable_name_template, flow_context, contact)
        actual_value = _get_value_from_context_or_contact(resolved_variable_path, flow_context, contact)
        result = actual_value is not None
        logger.debug(
            f"Contact {contact.id}, Flow {transition.current_step.flow.id}, Step {transition.current_step.id}: "
            f"Condition 'variable_exists' check for '{resolved_variable_path}'. "
            f"Value: '{str(actual_value)[:100]}' (type: {type(actual_value).__name__}). Result: {result}"
        )
        return result
        
    elif condition_type == 'variable_contains':
        variable_name = config.get('variable_name')
        if variable_name is None: return False
        actual_value = _get_value_from_context_or_contact(variable_name, flow_context, contact)
        expected_item = value_for_condition # This is the 'value' field from config
        result = False
        if isinstance(actual_value, str) and isinstance(expected_item, str): result = expected_item in actual_value
        elif isinstance(actual_value, list) and expected_item is not None: result = expected_item in actual_value
        
        logger.debug(
            f"Contact {contact.id}, Flow {transition.current_step.flow.id}, Step {transition.current_step.id}: "
            f"Condition 'variable_contains' check for '{variable_name}'. "
            f"Container: '{str(actual_value)[:100]}' (type: {type(actual_value).__name__}), "
            f"Expected item: '{expected_item}'. Result: {result}"
        )
        return result

    elif condition_type == 'nfm_response_field_equals' and nfm_response_data:
        field_path = config.get('field_path')
        if not field_path: return False
        actual_val_from_nfm = nfm_response_data
        for part in field_path.split('.'):
            if isinstance(actual_val_from_nfm, dict): actual_val_from_nfm = actual_val_from_nfm.get(part)
            else: actual_val_from_nfm = None; break
        return actual_val_from_nfm == value_for_condition

    elif condition_type == 'question_reply_is_valid':
        # This condition is now implicitly handled by the logic within _handle_active_flow_step
        # when it processes a reply for a question. If flow_context has the saved variable,
        # it means the reply was valid according to the question's own reply_config.
        # The transition would then typically check if that variable_exists or variable_equals.
        # However, to directly use this condition type, we'd need to re-evaluate validity here.
        # For now, assume a question step saves valid reply to context, then use 'variable_exists'
        # or 'variable_equals' on the saved variable in the transition.
        # If value_for_condition is True, check if the specific variable for the current question (if any) was set.
        question_expectation = flow_context.get('_question_awaiting_reply_for')
        if question_expectation and isinstance(question_expectation, dict):
            var_name = question_expectation.get('variable_name')
            # If value is True, we check if the variable was set (implying valid reply)
            # If value is False, we check if the variable was *not* set (implying invalid reply)
            is_var_set = var_name in flow_context
            return is_var_set if value_for_condition is True else not is_var_set
        return False # No question was being awaited or config mismatch

    elif condition_type == 'user_requests_human':
        human_request_keywords = config.get('keywords', ['help', 'support', 'agent', 'human', 'operator'])
        if user_text and isinstance(human_request_keywords, list):
            user_text_lower = user_text.lower()
            for keyword in human_request_keywords:
                if isinstance(keyword, str) and keyword.strip() and keyword.strip().lower() in user_text_lower:
                    logger.info(f"User requested human agent with keyword: '{keyword}'")
                    return True
        return False

    elif condition_type == 'contact_is_admin':
        # This is a custom security check for admin flows.
        # It checks if the contact is linked to an active staff user.
        # The Contact model should have a OneToOneField to the User model named 'user'.
        is_linked_staff_user = hasattr(contact, 'user') and contact.user is not None and contact.user.is_staff and contact.user.is_active
        result = is_linked_staff_user
        logger.info(f"Condition 'contact_is_admin' check for contact {contact.id}. Linked staff user: {is_linked_staff_user}. Result: {result}")
        return result

    logger.warning(f"Unknown or unhandled condition type: '{condition_type}' for transition {transition.id} or condition logic not met.")
    return False


def _transition_to_step(contact_flow_state: ContactFlowState, next_step: FlowStep, current_flow_context: dict, contact: Contact, message_data: dict) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    logger.info(f"Transitioning contact {contact.whatsapp_id} from '{contact_flow_state.current_step.name}' to '{next_step.name}' in flow '{contact_flow_state.current_flow.name}'.")
    
    # Clear question-specific context from the *previous* step if it was a question
    if contact_flow_state.current_step.step_type == 'question':
        current_flow_context.pop('_question_awaiting_reply_for', None)
        current_flow_context.pop('_fallback_count', None)
        logger.debug(f"Cleared question expectation and fallback count from previous step '{contact_flow_state.current_step.name}'.")

    # --- FIX: Save the new step and the context from the previous step's answer ---
    # This ensures the contact is officially at the new step before we execute its actions.
    contact_flow_state.current_step = next_step
    contact_flow_state.flow_context_data = current_flow_context
    # Use transaction.atomic to ensure that the state update and subsequent actions
    # are treated as a single unit of work where possible.
    # The save() here commits the move to the new step.
    contact_flow_state.save()

    actions_from_new_step, context_after_new_step_execution = _execute_step_actions(
        next_step, contact, current_flow_context.copy() # Pass a copy to avoid modification by reference if new step also modifies
    )
    
    # Re-fetch state to see if it was cleared or changed by _execute_step_actions (e.g., by end_flow, human_handover, switch_flow)
    # This is a critical check for robustness.
    with transaction.atomic():
        current_db_state = ContactFlowState.objects.select_for_update().filter(contact=contact).first()

        if current_db_state and current_db_state.pk == contact_flow_state.pk:
            # If the state still exists and belongs to this flow, then save the context
            # that resulted from executing this 'next_step'.
            if current_db_state.flow_context_data != context_after_new_step_execution:
                current_db_state.flow_context_data = context_after_new_step_execution
                current_db_state.save(update_fields=['flow_context_data', 'last_updated_at'])
                logger.debug(f"Saved updated context for contact {contact.whatsapp_id} after executing step '{next_step.name}'.")
        elif not current_db_state:
            logger.info(f"ContactFlowState for contact {contact.whatsapp_id} was cleared during execution of step '{next_step.name}'. No final context to save.")
        else: # State exists but is different (e.g., switched flow)
            logger.info(f"ContactFlowState for contact {contact.whatsapp_id} changed during execution of step '{next_step.name}'. New state: {current_db_state}")
        
    return actions_from_new_step, context_after_new_step_execution


def _update_contact_data(contact: Contact, field_path: str, value_to_set: Any):
    if not field_path: 
        logger.warning("Empty field_path provided for _update_contact_data.")
        return
    
    # This logic is simple, but could be expanded to handle nested JSON fields on Contact if needed.
    parts = field_path.split('.')
    target_object = contact
    field_to_update_on_object = None
    
    if len(parts) == 1: # Direct attribute on Contact model
        field_name = parts[0]
        if field_name.lower() in ['id', 'pk', 'whatsapp_id']: # Protected fields
            logger.warning(f"Attempt to update protected Contact field '{field_name}' denied.")
            return
        try:
            if hasattr(contact, field_name):
                setattr(contact, field_name, value_to_set)
                contact.save(update_fields=[field_name])
                logger.info(f"Updated Contact {contact.whatsapp_id} field '{field_name}' to '{value_to_set}'.")
            else:
                logger.warning(f"Contact field '{field_name}' not found.")
        except (DjangoValidationError, TypeError) as e:
            logger.error(f"Failed to update Contact field '{field_name}' for contact {contact.id} with value '{value_to_set}'. Error: {e}", exc_info=False)

            
    elif parts[0] == 'custom_fields': # Handling nested updates in JSONField 'custom_fields'
        if not isinstance(contact.custom_fields, dict):
            contact.custom_fields = {} # Initialize if not a dict
        
        current_level = contact.custom_fields
        for i, key in enumerate(parts[1:-1]): # Navigate to the second to last key
            current_level = current_level.setdefault(key, {})
            if not isinstance(current_level, dict):
                logger.error(f"Path error in Contact.custom_fields: '{key}' is not a dict for path '{field_path}'.")
                return
        
        final_key = parts[-1]
        if len(parts) > 1 : # Ensure there's at least one key after 'custom_fields'
            current_level[final_key] = value_to_set
            contact.save(update_fields=['custom_fields'])
            logger.info(f"Updated Contact {contact.whatsapp_id} custom_fields path '{'.'.join(parts[1:])}' to '{value_to_set}'.")
        else: # Only 'custom_fields' was specified, meaning replace the whole dict
            if isinstance(value_to_set, dict):
                contact.custom_fields = value_to_set
                contact.save(update_fields=['custom_fields'])
                logger.info(f"Replaced Contact {contact.whatsapp_id} custom_fields with: {value_to_set}")
            else:
                logger.warning(f"Cannot replace Contact.custom_fields with a non-dictionary value for path '{field_path}'.")
    else:
        logger.warning(f"Unsupported field path '{field_path}' for updating Contact model.")


def _update_customer_profile_data(contact: Contact, fields_to_update_config: Dict[str, Any], flow_context: dict):
    profile, created = CustomerProfile.objects.get_or_create(contact=contact)
    if created: 
        logger.info(f"Created new CustomerProfile for contact {contact.whatsapp_id}")
        profile.notes = "This is a placeholder profile created automatically. Details will be updated as the customer interacts with the system."
        profile.save(update_fields=['notes'])
        logger.info(f"Added placeholder note to new profile for contact {contact.whatsapp_id}")
        # Manually attach the newly created profile to the in-memory contact object
        # to make it available to subsequent steps in the same flow execution.
        contact.customer_profile = profile

    if not fields_to_update_config or not isinstance(fields_to_update_config, dict):
        logger.debug("_update_customer_profile_data called with no fields to update. Profile ensured to exist.")
        return

    changed_fields = []
    for field_path, value_template in fields_to_update_config.items():
        resolved_value = _resolve_value(value_template, flow_context, contact)
        
        if isinstance(resolved_value, str) and resolved_value.lower() == 'skip':
            resolved_value = None
        
        parts = field_path.split('.')
        if len(parts) == 1: # Direct attribute on CustomerProfile model
            field_name = parts[0]
            if hasattr(profile, field_name) and field_name.lower() not in ['contact', 'contact_id', 'created_at', 'updated_at', 'last_interaction_date']:
                try:
                    field_object = profile._meta.get_field(field_name)
                    if isinstance(field_object, models.DateField) and resolved_value == '':
                        resolved_value = None

                    if isinstance(field_object, models.DecimalField) and resolved_value is not None:
                        try:
                            resolved_value = Decimal(resolved_value)
                        except (InvalidOperation, TypeError):
                            logger.warning(f"Could not convert '{resolved_value}' to Decimal for field '{field_name}'. Skipping update.")
                            continue

                    setattr(profile, field_name, resolved_value)
                    if field_name not in changed_fields: 
                        changed_fields.append(field_name)
                except (DjangoValidationError, TypeError, ValueError) as e:
                    logger.error(f"Validation/Type error updating CustomerProfile field '{field_name}' for contact {contact.id} with value '{resolved_value}'. Error: {e}", exc_info=False)
                    continue
            else:
                logger.warning(f"CustomerProfile field '{field_name}' not found or is protected.")
        elif parts[0] in ['tags', 'custom_attributes'] and len(parts) > 1: # JSONFields
            json_field_name = parts[0]
            json_data = getattr(profile, json_field_name)
            
            if json_field_name == 'tags' and not isinstance(json_data, list):
                json_data = []
            elif json_field_name == 'custom_attributes' and not isinstance(json_data, dict):
                json_data = {}
            
            current_level = json_data
            for key in parts[1:-1]:
                current_level = current_level.setdefault(key, {})
                if not isinstance(current_level, dict):
                    logger.warning(f"Path error in CustomerProfile.{json_field_name} at '{key}'. Expected dict, found {type(current_level)}.")
                    current_level = None
                    break
            
            if current_level is not None:
                final_key = parts[-1]
                if isinstance(current_level, dict):
                    current_level[final_key] = resolved_value
                elif isinstance(current_level, list):
                    logger.warning(f"Direct key assignment ('{final_key}') on a list (tags) is not supported. Replacing list.")
                    json_data = resolved_value if isinstance(resolved_value, list) else [resolved_value]

                setattr(profile, json_field_name, json_data)
                if json_field_name not in changed_fields:
                    changed_fields.append(json_field_name)
        else:
            logger.warning(f"Unsupported field path for CustomerProfile: {field_path}")

    if changed_fields:
        profile.save(update_fields=changed_fields)
        logger.info(f"CustomerProfile for {contact.whatsapp_id} updated fields: {changed_fields}")


@transaction.atomic
def process_message_for_flow(contact: Contact, message_data: dict, incoming_message_obj: Message) -> List[Dict[str, Any]]:
    """
    Main entry point to process an incoming message for a contact against flows.
    Determines if the contact is in an active flow, an AI conversation mode, or if a new flow should be triggered.
    """
    # --- AI Conversation Mode Handling ---
    # This is a fast path to delegate to the AI handler if the contact is not in a standard flow.
    # It's already efficient and correctly placed.
    if contact.conversation_mode != 'flow':
        user_text = message_data.get('text', {}).get('body', '').strip().lower()
        exit_keywords = ['exit', 'menu', 'stop', 'quit']

        if user_text in exit_keywords:
            logger.info(f"Contact {contact.id} is exiting AI mode with keyword '{user_text}'.")
            contact.conversation_mode = 'flow'
            contact.conversation_context = {}
            contact.save(update_fields=['conversation_mode', 'conversation_context'])
            
            # Clear any residual flow state
            _clear_contact_flow_state(contact)
            
            # Send a confirmation message and re-trigger the main menu
            actions_to_perform = [{
                'type': 'send_whatsapp_message',
                'recipient_wa_id': contact.whatsapp_id,
                'message_type': 'text',
                'data': {'body': "You are now back in the main menu."}
            }]
            
            # Simulate a 'menu' message to re-trigger the main flow
            menu_message_data = {'type': 'text', 'text': {'body': 'menu'}}
            flow_was_triggered = _trigger_new_flow(contact, menu_message_data, incoming_message_obj)
            if flow_was_triggered:
                contact_flow_state = ContactFlowState.objects.select_related('current_flow', 'current_step').get(contact=contact)
                entry_step = contact_flow_state.current_step
                entry_actions, updated_context = _execute_step_actions(entry_step, contact, contact_flow_state.flow_context_data.copy())
                actions_to_perform.extend(entry_actions)
                contact_flow_state.flow_context_data = updated_context
                contact_flow_state.save()

            return actions_to_perform
        else:
            # Not an exit command, so process as part of the AI conversation
            logger.info(f"Contact {contact.id} is in '{contact.conversation_mode}' mode. Triggering AI conversation task.")
            from .tasks import handle_ai_conversation_task # Local import to avoid circular dependency issues
            handle_ai_conversation_task.delay(contact_id=contact.id, message_id=incoming_message_obj.id)
            return [] # Stop further flow processing

    # --- Original Flow Logic Starts Here ---
    # Initialize the list of actions to be performed at the very beginning.
    # This list accumulates actions from multiple steps if fall-through occurs.
    actions_to_perform = []

    # --- SPECIAL CASE: Order Receiver Number ---
    # If the message was sent TO the dedicated order receiver number, bypass all normal
    # flow logic and immediately trigger the simple_add_order flow for the sender.
    order_receiver_phone_id = getattr(settings, 'ORDER_RECEIVER_PHONE_ID', None)
    message_app_config = incoming_message_obj.app_config

    if order_receiver_phone_id and message_app_config and message_app_config.phone_number_id == order_receiver_phone_id:
        logger.info(f"Message received on Order Receiver Number from {contact.whatsapp_id}. Triggering 'simple_add_order' flow.")
        
        # Force this contact into the simple_add_order flow, overwriting any existing state.
        _clear_contact_flow_state(contact)
        
        try:
            simple_add_order_flow = Flow.objects.get(name='simple_add_order', is_active=True)
            entry_point_step = simple_add_order_flow.steps.filter(is_entry_point=True).first()
            if not entry_point_step:
                raise Flow.DoesNotExist("Flow has no entry point.")

            order_number_from_message = message_data.get('text', {}).get('body', '').strip()
            if not order_number_from_message:
                logger.warning("Received empty message on order receiver number. Ignoring.")
                return []

            # Create a temporary flow state for this one-time execution. The main loop will process it.
            contact_flow_state = ContactFlowState.objects.create(
                contact=contact, current_flow=simple_add_order_flow, current_step=entry_point_step,
                flow_context_data={'order_number_from_message': order_number_from_message}
            )

            # FIX: Manually execute the entry step actions, just like a normal flow trigger,
            # to ensure the context is populated before the main loop evaluates transitions.
            entry_actions, updated_context = _execute_step_actions(entry_point_step, contact, contact_flow_state.flow_context_data.copy())
            actions_to_perform.extend(entry_actions)
            contact_flow_state.flow_context_data = updated_context
            contact_flow_state.save(update_fields=['flow_context_data'])
        except Flow.DoesNotExist:
            logger.error("The 'simple_add_order' flow is required for the Order Receiver Number but is not found or is inactive.")
            return []
    # --- END SPECIAL CASE ---

    """
    Main entry point to process an incoming message for a contact against flows.
    Determines if the contact is in an active flow or if a new flow should be triggered.
    This function is wrapped in a transaction.atomic decorator.
    """
    if contact.needs_human_intervention:
        logger.info(
            f"Flow processing is paused for contact {contact.id} ({contact.whatsapp_id}) "
            "as they require human intervention. No automated actions will be taken."
        )
        # By returning an empty list, we stop any further flow logic from executing.
        return []

    # actions_to_perform = [] # This is now initialized at the top of the function.
    
    # --- OPTIMIZATION: Use prefetch_related to get all necessary data in fewer queries. ---
    # We fetch the current step's outgoing transitions and their respective next steps.
    # This avoids hitting the database for transitions inside the main processing loop.
    prefetch_query = models.Prefetch(
        'current_step__outgoing_transitions',
        queryset=FlowTransition.objects.select_related('next_step').order_by('priority')
    )
    contact_flow_state = ContactFlowState.objects.select_related('current_flow', 'current_step').prefetch_related(prefetch_query).filter(contact=contact).first()

    try:
        # If no active flow, try to trigger one. This is the only time a user message can start a flow.
        if not contact_flow_state:
            logger.info(f"No active flow state for contact {contact.whatsapp_id}. Attempting to trigger a new flow.")
            flow_was_triggered = _trigger_new_flow(contact, message_data, incoming_message_obj)
            
            if flow_was_triggered:
                # A new flow was started. Execute its entry step's actions now.
                contact_flow_state = ContactFlowState.objects.select_related('current_flow', 'current_step').prefetch_related(prefetch_query).filter(contact=contact).first()
                if not contact_flow_state:
                    logger.warning(f"Flow was triggered for contact {contact.id} but no state was found immediately after (likely ended on first step). Exiting.")
                    return []

                entry_step = contact_flow_state.current_step
                initial_context = contact_flow_state.flow_context_data or {}
                
                entry_actions, updated_context = _execute_step_actions(entry_step, contact, initial_context.copy())
                actions_to_perform.extend(entry_actions)
                
                contact_flow_state.flow_context_data = updated_context
                contact_flow_state.save(update_fields=['flow_context_data', 'last_updated_at'])
                
                # If the entry step was a question or ends the flow, we are done with this message.
                if entry_step.step_type in ['question', 'end_flow', 'human_handover']:
                    # A question step should not fall through. It should wait for the next message.
                    # So we process its actions and exit, preventing the main loop from running on the same message.
                    # The same applies for end_flow and human_handover, which terminate the flow logic for this cycle.
                    final_actions_for_meta_view = []
                    for action in actions_to_perform:
                        if action.get('type') == '_internal_command_clear_flow_state':
                            _clear_contact_flow_state(contact)
                            logger.debug(f"Contact {contact.id}: Processed internal command to clear flow state from entry step.")
                        elif action.get('type') == 'send_whatsapp_message':
                            final_actions_for_meta_view.append(action)
                    
                    return final_actions_for_meta_view
                else:
                    # It's a fall-through step. We need to enter the main processing loop
                    # with an "internal" message to check for transitions.
                    message_data = {'type': 'internal_flow_start'}
            else:
                # No flow triggered, nothing more to do.
                return []

        # --- Start of Main Flow Processing Loop ---
        # This loop will continue as long as the contact is in an active flow state.
        # It allows for "fall-through" steps (like 'action' steps) to be processed immediately.
        while True:
            # Re-fetch state in each loop iteration for robustness
            is_internal_message = message_data.get('type', '').startswith('internal_') # type: ignore
            contact_flow_state = ContactFlowState.objects.select_related('current_flow', 'current_step').filter(contact=contact).first()

            if not contact_flow_state:
                logger.info(f"Flow state was cleared, exiting processing loop for contact {contact.id}.")
                break # Flow was ended inside the loop.
            
            current_step = contact_flow_state.current_step
            flow_context = contact_flow_state.flow_context_data if contact_flow_state.flow_context_data is not None else {}
            
            logger.debug(f"Handling active flow. Contact: {contact.whatsapp_id}, Current Step: '{current_step.name}' (Type: {current_step.step_type}). Context: {flow_context}")

            # --- Step 1: Process incoming message if the current step is a question ---
            if current_step.step_type == 'question' and '_question_awaiting_reply_for' in flow_context:
                # If we've arrived at a question step via an internal transition (fallthrough/switch),
                # we must stop and wait for the user's actual reply. We should not process the
                # internal message as if it were a user's answer.
                if is_internal_message:
                    logger.debug(f"Reached question step '{current_step.name}' via internal transition. Breaking loop to await user reply.")
                    break
                # A question is NOT a pass-through step; it must wait for a reply.
                question_expectation = flow_context['_question_awaiting_reply_for']
                variable_to_save_name = question_expectation.get('variable_name')
                expected_reply_type = question_expectation.get('expected_type')
                validation_regex_ctx = question_expectation.get('validation_regex')
                
                user_text = message_data.get('text', {}).get('body', '').strip() if message_data.get('type') == 'text' else None
                interactive_reply_id = None
                if message_data.get('type') == 'interactive':
                    interactive_payload = message_data.get('interactive', {})
                    interactive_type = interactive_payload.get('type')
                    if interactive_type == 'button_reply':
                        interactive_reply_id = interactive_payload.get('button_reply', {}).get('id')
                    elif interactive_type == 'list_reply':
                        interactive_reply_id = interactive_payload.get('list_reply', {}).get('id')
                    elif interactive_type == 'nfm_reply': # Handle Native Flow Message reply
                        response_json_str = interactive_payload.get('nfm_reply', {}).get('response_json')
                        if response_json_str:
                            try: 
                                nfm_response_data = json.loads(response_json_str)
                            except json.JSONDecodeError: 
                                logger.warning(f"Could not parse nfm_reply response_json for question step {current_step.name}")
                
                
                
                image_payload = message_data.get('image') if message_data.get('type') == 'image' else None
                location_payload = message_data.get('location') if message_data.get('type') == 'location' else None

                reply_is_valid = False
                value_to_save = None

                if expected_reply_type == 'text' and user_text:
                    # For text, first check regex if it exists
                    if validation_regex_ctx:
                        if re.match(validation_regex_ctx, user_text):
                            value_to_save = user_text
                            reply_is_valid = True
                    else: # No regex, any text is valid
                        value_to_save = user_text
                        reply_is_valid = True
                elif expected_reply_type == 'email':
                    email_r = validation_regex_ctx or r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if user_text and re.match(email_r, user_text):
                        value_to_save = user_text
                        reply_is_valid = True
                elif expected_reply_type == 'number' and user_text:
                    try:
                        parsed_num = float(user_text) if '.' in user_text or (validation_regex_ctx and '.' in validation_regex_ctx) else int(user_text)
                        # Now check regex against the string representation of the parsed number
                        if validation_regex_ctx:
                            if re.match(validation_regex_ctx, str(parsed_num)):
                                value_to_save = parsed_num
                                reply_is_valid = True
                        else:
                            value_to_save = parsed_num
                            reply_is_valid = True
                    except ValueError:
                        pass # reply_is_valid remains False
                elif expected_reply_type == 'interactive_id' and interactive_reply_id:
                    value_to_save = interactive_reply_id
                    reply_is_valid = True
                elif expected_reply_type == 'image' and image_payload:
                    value_to_save = image_payload.get('id') # Save the WhatsApp Media ID
                    if value_to_save:
                        reply_is_valid = True
                elif expected_reply_type == 'location' and location_payload:
                    value_to_save = location_payload
                    if value_to_save and 'latitude' in value_to_save and 'longitude' in value_to_save:
                        reply_is_valid = True
                elif expected_reply_type == 'nfm_reply' and nfm_response_data is not None:
                    value_to_save = nfm_response_data
                    reply_is_valid = True
                
                if reply_is_valid and variable_to_save_name:
                    flow_context[variable_to_save_name] = value_to_save
                    logger.info(f"Saved valid reply for '{variable_to_save_name}' in question step '{current_step.name}': {value_to_save}")
                    flow_context.pop('_question_awaiting_reply_for', None)
                    flow_context.pop('_fallback_count', None)
                else:
                    logger.info(f"Reply for question step '{current_step.name}' was not valid. Expected: {expected_reply_type}. User text: {user_text}. Interactive ID: {interactive_reply_id}")
            
            # If this was a user message that was just processed (valid or not),
            # we should not continue falling through steps in the same cycle.
            # The next actions depend on the transition from the user's reply.
            if not is_internal_message:
                just_triggered_flow = False # Unset flag if it was set

            # --- Step 2: Evaluate transitions from the current step ---
            # --- OPTIMIZATION: Use the prefetched transitions instead of a new query. ---
            # The original query was: FlowTransition.objects.filter(current_step=current_step)...
            # Now, we access the prefetched data from the step object.
            transitions = current_step.outgoing_transitions.all()

            next_step_to_transition_to = None
            for transition in transitions:
                if _evaluate_transition_condition(transition, contact, message_data, flow_context, incoming_message_obj):
                    next_step_to_transition_to = transition.next_step
                    logger.info(f"Transition condition met: From '{current_step.name}' to '{next_step_to_transition_to.name}'.")
                    break
            
            if next_step_to_transition_to:
                actions, flow_context = _transition_to_step(contact_flow_state, next_step_to_transition_to, flow_context, contact, message_data)
                # Check for a switch_flow command specifically to handle it within the loop.
                switch_action = next((a for a in actions if a.get('type') == '_internal_command_switch_flow'), None)
                if switch_action:
                    logger.info(f"Contact {contact.id}: Processing internal command to switch flow within the main loop.")
                    try:
                        _clear_contact_flow_state(contact) # Clear old state

                        new_flow_name = switch_action.get('target_flow_name')
                        initial_context_for_new_flow = switch_action.get('initial_context', {})

                        target_flow = Flow.objects.get(name=new_flow_name, is_active=True)
                        entry_point_step = FlowStep.objects.filter(flow=target_flow, is_entry_point=True).first()

                        if not entry_point_step:
                            raise ValueError(f"Flow '{new_flow_name}' is active but has no entry point step defined.")
                        
                        logger.info(f"Contact {contact.id}: Switching to flow '{target_flow.name}' at entry step '{entry_point_step.name}'.")
                        
                        new_contact_flow_state = ContactFlowState.objects.create(
                            contact=contact,
                            current_flow=target_flow,
                            current_step=entry_point_step,
                            flow_context_data=initial_context_for_new_flow,
                            started_at=timezone.now()
                        )

                        # Manually execute the actions for the new entry point step.
                        # This ensures that 'action' steps at the start of a flow are run immediately
                        # after a switch, before the loop continues to evaluate transitions.
                        entry_actions, updated_context = _execute_step_actions(
                            entry_point_step, contact, initial_context_for_new_flow.copy()
                        )
                        actions_to_perform.extend(entry_actions)
                        
                        # Save the context after this first execution
                        new_contact_flow_state.flow_context_data = updated_context
                        new_contact_flow_state.save(update_fields=['flow_context_data', 'last_updated_at'])
                        logger.debug(f"Contact {contact.id}: Executed entry step '{entry_point_step.name}' and saved context.")
                        
                        # Check if the new entry point immediately ended the flow.
                        # If so, break the main loop to allow the clear_state command to be processed.
                        if any(action.get('type') == '_internal_command_clear_flow_state' for action in entry_actions):
                            break
                        
                        # The message is "consumed" by the first step that uses it.
                        # For subsequent automatic steps in the new flow, we need to prevent reprocessing the original message.
                        message_data = {'type': 'internal_switch_flow'}
                        incoming_message_obj = None
                        
                        continue # Restart the loop to process the new flow's entry point

                    except (Flow.DoesNotExist, ValueError) as e:
                        logger.error(f"Contact {contact.id}: Failed to switch flow to '{switch_action.get('target_flow_name')}'. Error: {e}", exc_info=True)
                        _clear_contact_flow_state(contact, error=True) # Ensure state is cleared on failure
                        actions_to_perform.append({
                            'type': 'send_whatsapp_message', 'recipient_wa_id': contact.whatsapp_id, 'message_type': 'text',
                            'data': {'body': 'I seem to be having some technical difficulties. Please try again in a moment.'}
                        })
                        break # Exit loop on failure
                else:
                    # No switch command, so process actions normally and check for other control commands
                    actions_to_perform.extend(actions) # Add actions from the transitioned step
                    if any(action.get('type') == '_internal_command_clear_flow_state' for action in actions):
                        break # Exit the while loop for end_flow or human_handover

            else:
                logger.info(f"No transition met for step '{current_step.name}'. Engaging fallback logic for contact {contact.id}.")
                fallback_actions = _handle_fallback(current_step, contact, flow_context, contact_flow_state)
                actions_to_perform.extend(fallback_actions)
                break # Fallback always breaks the loop
            
            # --- Step 3: Loop Control ---
            # If the new step is a question, or if the flow state was cleared (e.g., end_flow), break the loop.
            new_state = ContactFlowState.objects.filter(contact=contact).first()
            if not new_state or new_state.current_step.step_type in ['question', 'end_flow', 'human_handover']:
                break
            
            # The message_data is "consumed" by the first step that uses it (the question step).
            # For subsequent automatic "fall-through" steps, we use an empty message_data.
            message_data = {'type': 'internal_fallthrough'}
            incoming_message_obj = None
            is_internal_message = True
    except Exception as e:
        logger.error(f"Critical error in process_message_for_flow for contact {contact.whatsapp_id}: {e}", exc_info=True)
        # Clear state on unhandled error to prevent loops and allow re-triggering or human intervention
        _clear_contact_flow_state(contact, error=True)
        # Notify user of an issue
        actions_to_perform = [{ # Reset actions to only send an error message
            'type': 'send_whatsapp_message',
            'recipient_wa_id': contact.whatsapp_id,
            'message_type': 'text',
            'data': {'body': 'I seem to be having some technical difficulties. Please try again in a moment.'}
        }]

    # Process internal commands generated by _execute_step_actions or _handle_active_flow_step
    final_actions_for_meta_view = []
    for action in actions_to_perform: # actions_to_perform could be modified by switch_flow
        if action.get('type') == '_internal_command_clear_flow_state':
            # Actually clear the state when the command is processed.
            _clear_contact_flow_state(contact)
            logger.debug(f"Contact {contact.id}: Processed internal command to clear flow state.")
        elif action.get('type') == 'send_whatsapp_message': # Only pass valid message actions
            final_actions_for_meta_view.append(action)
        else:
            logger.warning(f"Unhandled action type in final processing: {action.get('type')}")
            
    return final_actions_for_meta_view
