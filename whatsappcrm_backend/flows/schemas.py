# whatsappcrm_backend/flows/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Literal, Union

# --- Base Message Component Schemas ---

class TextContent(BaseModel):
    body: str
    preview_url: bool = False

class MediaMessageContent(BaseModel):
    asset_pk: Optional[int] = None
    id: Optional[str] = None
    link: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None # Specific to documents

# Interactive Message Schemas
class InteractiveButton(BaseModel):
    type: Literal['reply'] = 'reply'
    reply: Dict[str, str] # e.g., {"id": "unique-id", "title": "Click me"}

class InteractiveRow(BaseModel):
    id: str
    title: str
    description: Optional[str] = None

class InteractiveSection(BaseModel):
    title: Optional[str] = None
    rows: Union[List[InteractiveRow], str] # Allow string for template

class InteractiveAction(BaseModel):
    buttons: Optional[List[InteractiveButton]] = None
    button: Optional[str] = None # For list messages
    sections: Optional[List[InteractiveSection]] = None
    # For Flow type
    name: Optional[Literal['flow']] = None
    parameters: Optional[Dict[str, Any]] = None

class InteractiveBody(BaseModel):
    text: str

class InteractiveHeader(BaseModel):
    type: Literal['text', 'video', 'image', 'document']
    text: Optional[str] = None
    # TODO: Add media objects for other header types

class InteractiveFooter(BaseModel):
    text: str

class InteractiveMessagePayload(BaseModel):
    type: Literal['button', 'list', 'flow']
    action: InteractiveAction
    body: InteractiveBody
    header: Optional[InteractiveHeader] = None
    footer: Optional[InteractiveFooter] = None

# Template Message Schemas
class TemplateParameter(BaseModel):
    type: str # 'text', 'currency', 'date_time', 'image', 'document', 'video', 'payload'
    text: Optional[str] = None
    payload: Optional[str] = None
    # TODO: Add other parameter types like currency, date_time, image, etc.

class TemplateComponent(BaseModel):
    type: Literal['header', 'body', 'button']
    sub_type: Optional[str] = None # e.g., 'quick_reply', 'url'
    parameters: List[TemplateParameter]

class TemplateLanguage(BaseModel):
    code: str

class TemplateMessagePayload(BaseModel):
    name: str
    language: TemplateLanguage
    components: Optional[List[TemplateComponent]] = None

# Other Message Types
class ContactAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    type: Optional[Literal['HOME', 'WORK']] = None

class ContactEmail(BaseModel):
    email: Optional[str] = None
    type: Optional[Literal['HOME', 'WORK']] = None

class ContactName(BaseModel):
    formatted_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    suffix: Optional[str] = None
    prefix: Optional[str] = None

class ContactOrg(BaseModel):
    company: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

class ContactPhone(BaseModel):
    phone: Optional[str] = None
    type: Optional[Literal['CELL', 'MAIN', 'IPHONE', 'HOME', 'WORK']] = None
    wa_id: Optional[str] = None

class ContactUrl(BaseModel):
    url: Optional[str] = None
    type: Optional[Literal['HOME', 'WORK']] = None

class ContactPayload(BaseModel):
    addresses: Optional[List[ContactAddress]] = None
    birthday: Optional[str] = None # YYYY-MM-DD
    emails: Optional[List[ContactEmail]] = None
    name: ContactName
    org: Optional[ContactOrg] = None
    phones: Optional[List[ContactPhone]] = None
    urls: Optional[List[ContactUrl]] = None

class LocationPayload(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


# --- Main Step Config Schemas ---

class StepConfigSendMessage(BaseModel):
    message_type: Literal['text', 'image', 'document', 'audio', 'video', 'sticker', 'interactive', 'template', 'contacts', 'location']
    text: Optional[TextContent] = None
    image: Optional[MediaMessageContent] = None
    document: Optional[MediaMessageContent] = None
    audio: Optional[MediaMessageContent] = None
    video: Optional[MediaMessageContent] = None
    sticker: Optional[MediaMessageContent] = None
    interactive: Optional[InteractiveMessagePayload] = None
    template: Optional[TemplateMessagePayload] = None
    contacts: Optional[List[ContactPayload]] = None
    location: Optional[LocationPayload] = None

class FallbackConfig(BaseModel):
    """
    Configuration for what happens when a user's reply to a question is invalid.
    """
    action: Literal['re_prompt'] = 're_prompt'
    max_retries: int = Field(2, ge=0, description="Number of times to re-prompt before giving up.")
    re_prompt_message_text: Optional[str] = None
    action_after_retries: Optional[Literal['human_handover', 'end_flow', 'switch_flow']] = Field(None, description="Action to take after all retries are exhausted.")
    config_after_retries: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuration for the action_after_retries (e.g., message for handover).")

class ReplyConfig(BaseModel):
    save_to_variable: str
    expected_type: Literal['text', 'email', 'number', 'interactive_id', 'image', 'location', 'nfm_reply'] = 'text'
    validation_regex: Optional[str] = None

class StepConfigQuestion(BaseModel):
    message_config: Dict[str, Any]
    reply_config: ReplyConfig
    fallback_config: Optional[FallbackConfig] = None

class ActionItem(BaseModel):
    action_type: str
    # Used by 'set_context_variable', 'query_model'
    variable_name: Optional[str] = None
    # Used by 'set_context_variable', 'update_contact_field'
    value_template: Optional[Any] = None
    # Used by 'update_contact_field'
    field_path: Optional[str] = None
    # Used by 'update_customer_profile'
    fields_to_update: Optional[Dict[str, Any]] = None
    # Used by 'send_admin_notification'
    message_template: Optional[str] = None
    # Used by 'query_model'
    app_label: Optional[str] = None
    model_name: Optional[str] = None
    filters_template: Optional[Dict[str, Any]] = None
    order_by: Optional[List[str]] = None
    # Used by 'query_model' for optimization
    fields_to_return: Optional[List[str]] = None
    limit: Optional[int] = None
    # Used by 'create_model_instance'
    fields_template: Optional[Dict[str, Any]] = None
    save_to_variable: Optional[str] = None
    # Used by custom actions
    params_template: Optional[Dict[str, Any]] = None

class StepConfigAction(BaseModel):
    actions_to_run: List[ActionItem]

class StepConfigHumanHandover(BaseModel):
    pre_handover_message_text: Optional[str] = None
    notification_details: Optional[str] = None

class StepConfigEndFlow(BaseModel):
    message_config: Optional[Dict[str, Any]] = None # Can be validated against StepConfigSendMessage

class StepConfigSwitchFlow(BaseModel):
    target_flow_name: str
    initial_context_template: Optional[Dict[str, Any]] = None
    trigger_keyword_to_pass: Optional[str] = None