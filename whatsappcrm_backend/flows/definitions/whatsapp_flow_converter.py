# whatsappcrm_backend/flows/definitions/whatsapp_flow_converter.py

"""
Helper functions to convert traditional flow definitions to WhatsApp Flow JSON format.
WhatsApp Flows use a screen-based JSON schema as defined by Meta.
"""

from typing import Dict, List, Any


def create_text_input(name: str, label: str, required: bool = True, 
                       helper_text: str = None, input_type: str = "text") -> Dict[str, Any]:
    """
    Creates a text input component for WhatsApp Flow.
    
    Args:
        name: Field name/ID
        label: Display label
        required: Whether field is required
        helper_text: Optional helper text
        input_type: Type of input (text, number, email, phone)
    """
    component = {
        "type": "TextInput",
        "name": name,
        "label": label,
        "required": required,
        "input-type": input_type
    }
    
    if helper_text:
        component["helper-text"] = helper_text
    
    return component


def create_dropdown(name: str, label: str, options: List[Dict[str, str]], 
                    required: bool = True) -> Dict[str, Any]:
    """
    Creates a dropdown component for WhatsApp Flow.
    
    Args:
        name: Field name/ID
        label: Display label
        options: List of options with 'id' and 'title'
        required: Whether field is required
    """
    return {
        "type": "Dropdown",
        "name": name,
        "label": label,
        "required": required,
        "data-source": options
    }


def create_radio_buttons(name: str, label: str, options: List[Dict[str, str]], 
                         required: bool = True) -> Dict[str, Any]:
    """
    Creates radio button group for WhatsApp Flow.
    
    Args:
        name: Field name/ID
        label: Display label
        options: List of options with 'id' and 'title'
        required: Whether field is required
    """
    return {
        "type": "RadioButtonsGroup",
        "name": name,
        "label": label,
        "required": required,
        "data-source": options
    }


def create_checkbox_group(name: str, label: str, options: List[Dict[str, str]], 
                          required: bool = False) -> Dict[str, Any]:
    """
    Creates checkbox group for WhatsApp Flow.
    
    Args:
        name: Field name/ID
        label: Display label
        options: List of options with 'id' and 'title'
        required: Whether field is required
    """
    return {
        "type": "CheckboxGroup",
        "name": name,
        "label": label,
        "required": required,
        "data-source": options
    }


def create_date_picker(name: str, label: str, required: bool = True) -> Dict[str, Any]:
    """
    Creates a date picker component for WhatsApp Flow.
    
    Args:
        name: Field name/ID
        label: Display label
        required: Whether field is required
    """
    return {
        "type": "DatePicker",
        "name": name,
        "label": label,
        "required": required
    }


def create_text_body(text: str) -> Dict[str, Any]:
    """
    Creates a text body component for displaying information.
    
    Args:
        text: The text to display
    """
    return {
        "type": "TextBody",
        "text": text
    }


def create_text_heading(text: str) -> Dict[str, Any]:
    """
    Creates a text heading component.
    
    Args:
        text: The heading text
    """
    return {
        "type": "TextHeading",
        "text": text
    }


def create_screen(screen_id: str, title: str, data: Dict[str, Any], 
                  layout: List[Dict[str, Any]], terminal: bool = False,
                  success: bool = False) -> Dict[str, Any]:
    """
    Creates a complete screen for WhatsApp Flow.
    
    Args:
        screen_id: Unique screen identifier
        title: Screen title
        data: Screen data definitions
        layout: List of components in the screen
        terminal: Whether this is a terminal screen (no navigation)
        success: Whether this is a success screen
    """
    screen = {
        "id": screen_id,
        "title": title,
        "data": data,
        "layout": {
            "type": "SingleColumnLayout",
            "children": layout
        }
    }
    
    if terminal:
        screen["terminal"] = True
    
    if success:
        screen["success"] = True
    
    return screen


def create_footer(label: str, on_click_action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a footer with navigation button.
    
    Args:
        label: Button label
        on_click_action: Action to perform on click
    """
    return {
        "type": "Footer",
        "label": label,
        "on-click-action": on_click_action
    }


def create_navigate_action(next_screen: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Creates a navigate action.
    
    Args:
        next_screen: ID of the screen to navigate to
        payload: Optional payload to pass
    """
    action = {
        "name": "navigate",
        "next": {
            "type": "screen",
            "name": next_screen
        }
    }
    
    if payload:
        action["payload"] = payload
    
    return action


def create_complete_action() -> Dict[str, Any]:
    """
    Creates a complete action to finish the flow.
    """
    return {
        "name": "complete"
    }
