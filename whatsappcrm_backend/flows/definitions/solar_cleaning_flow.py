# whatsappcrm_backend/flows/definitions/solar_cleaning_flow.py

SOLAR_CLEANING_FLOW = {
    "name": "solar_cleaning_request",
    "friendly_name": "Solar Panel Cleaning Request",
    "description": "Initiates the WhatsApp interactive flow for solar panel cleaning service.",
    "trigger_keywords": ["solar cleaning", "clean panels"],
    "is_active": True,
    "steps": [
        {
            "name": "start_cleaning_request",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "solar_cleaning_whatsapp_flow",
                    "filters_template": {
                        "name": "solar_cleaning_whatsapp",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "send_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "solar_cleaning_whatsapp_flow.0"}},
                {"to_step": "fallback_to_legacy", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_whatsapp_flow",
            "type": "send_message",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "flow",
                    "body": {
                        "text": "Please complete our solar panel cleaning request form to get started."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-solar-cleaning-{{ 'now'|date:'U' }}",
                            "flow_id": "{{ solar_cleaning_whatsapp_flow.0.flow_id }}",
                            "flow_cta": "Start Request",
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": "WELCOME"
                            }
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "wait_for_whatsapp_response", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "wait_for_whatsapp_response",
            "type": "action",
            "config": {
                "actions_to_run": [],
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please complete the WhatsApp form. We will continue once your submission is received."
                    }
                }
            },
            "transitions": [
                {"to_step": "map_whatsapp_response_to_context", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "map_whatsapp_response_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "cleaning_full_name", "value_template": "{{ whatsapp_flow_data.full_name }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_phone", "value_template": "{{ whatsapp_flow_data.contact_phone }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_roof_type", "value_template": "{{ whatsapp_flow_data.roof_type }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_panel_type", "value_template": "{{ whatsapp_flow_data.panel_type }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_panel_count", "value_template": "{{ whatsapp_flow_data.panel_count }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_date", "value_template": "{{ whatsapp_flow_data.preferred_date }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_availability", "value_template": "{{ whatsapp_flow_data.availability }}"},
                    {"action_type": "set_context_variable", "variable_name": "cleaning_address", "value_template": "{{ whatsapp_flow_data.address }}"}
                ]
            },
            "transitions": [
                {"to_step": "ask_location_pin", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "fallback_to_legacy",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Sorry, the interactive form is currently unavailable. Please contact our support team to request a solar panel cleaning service."}
            },
            "transitions": [{"to_step": "end_flow_cancelled", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "legacy_start_cleaning_request",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "You've requested our solar panel cleaning service. Let's get a few details to provide you with a quote.\n\nFirst, what is your *full name*?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "cleaning_full_name"}
            },
            "transitions": [{"to_step": "ask_contact_phone", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_full_name"}}]
        },
        {
            "name": "ask_contact_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thanks, {{ cleaning_full_name }}. What is the best *contact number* for you?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "cleaning_phone", "validation_regex": "^\\+?[1-9]\\d{8,14}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid phone number (e.g., +263...)"}
            },
            "transitions": [{"to_step": "ask_roof_type", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_phone"}}]
        },
        {
            "name": "ask_roof_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Roof Type"},
                        "body": {"text": "What type of roof do you have?"},
                        "action": {
                            "button": "Select Roof Type",
                            "sections": [{"title": "Common Roof Types", "rows": [
                                {"id": "tile", "title": "Tile Roof"},
                                {"id": "ibr_metal", "title": "IBR / Metal Sheet"},
                                {"id": "flat_concrete", "title": "Flat Concrete"},
                                {"id": "other", "title": "Other / Not Sure"}
                            ]}]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "cleaning_roof_type"}
            },
            "transitions": [{"to_step": "ask_panel_type", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_roof_type"}}]
        },
        {
            "name": "ask_panel_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "What type of solar panels do you have?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "monocrystalline", "title": "Monocrystalline"}},
                                {"type": "reply", "reply": {"id": "polycrystalline", "title": "Polycrystalline"}},
                                {"type": "reply", "reply": {"id": "not_sure", "title": "I'm Not Sure"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "cleaning_panel_type"}
            },
            "transitions": [{"to_step": "ask_panel_count", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_panel_type"}}]
        },
        {
            "name": "ask_panel_count",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Got it. How many *solar panels* do you have?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "cleaning_panel_count"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid number (e.g., 8)."}
            },
            "transitions": [{"to_step": "ask_availability_date", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_panel_count"}}]
        },
        {
            "name": "ask_availability_date",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your *preferred date* for the cleaning service?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "cleaning_date"}
            },
            "transitions": [{"to_step": "ask_availability_time", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_date"}}]
        },
        {
            "name": "ask_availability_time",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "And is morning or afternoon better for you on that day?"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "morning", "title": "Morning"}},
                            {"type": "reply", "reply": {"id": "afternoon", "title": "Afternoon"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "cleaning_availability"}
            },
            "transitions": [{"to_step": "ask_address", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_availability"}}]
        },
        {
            "name": "ask_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the *full address* where the cleaning will take place?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "cleaning_address", "validation_regex": "^.{10,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please provide a more detailed address."}
            },
            "transitions": [{"to_step": "ask_location_pin", "condition_config": {"type": "variable_exists", "variable_name": "cleaning_address"}}]
        },
        {
            "name": "ask_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Finally, please share your *location pin* for accurate directions. You can also type 'skip' if you prefer not to."}},
                "reply_config": {"expected_type": "location", "save_to_variable": "cleaning_location_pin"}
            },
            "transitions": [
                {"to_step": "set_skipped_location", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "skip"}},
                {"to_step": "confirm_cleaning_request", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "cleaning_location_pin"}}
            ]
        },
        {
            "name": "set_skipped_location",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "cleaning_location_pin", "value_template": {"latitude": None, "longitude": None}}]},
            "transitions": [{"to_step": "confirm_cleaning_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "confirm_cleaning_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Please review and confirm your request:\n\n*Name*: {{ cleaning_full_name }}\n*Phone*: {{ cleaning_phone }}\n*Roof*: {{ cleaning_roof_type|replace('_', ' ')|title }}\n*Panels*: {{ cleaning_panel_count }} x {{ cleaning_panel_type|replace('_', ' ')|title }}\n*Date*: {{ cleaning_date }} ({{ cleaning_availability|title }})\n*Address*: {{ cleaning_address }}"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "confirm_cleaning", "title": "Confirm & Submit"}},
                            {"type": "reply", "reply": {"id": "go_back", "title": "Go Back"}},
                            {"type": "reply", "reply": {"id": "cancel_cleaning", "title": "Cancel"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "cleaning_confirmation"}
            },
            "transitions": [
                {"to_step": "save_cleaning_request", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_cleaning"}},
                {"to_step": "ask_location_pin", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "go_back"}},
                {"to_step": "end_flow_cancelled", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_cleaning_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "SolarCleaningRequest",
                        "fields_template": {
                            "customer": "current",
                            "full_name": "{{ cleaning_full_name }}",
                            "contact_phone": "{{ cleaning_phone }}",
                            "roof_type": "{{ cleaning_roof_type }}",
                            "panel_type": "{{ cleaning_panel_type }}",
                            "panel_count": "{{ cleaning_panel_count }}",
                            "preferred_date": "{{ cleaning_date }}",
                            "availability": "{{ cleaning_availability }}",
                            "address": "{{ cleaning_address }}",
                            "latitude": "{{ cleaning_location_pin.latitude }}",
                            "longitude": "{{ cleaning_location_pin.longitude }}"
                        },
                        "save_to_variable": "created_cleaning_request"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Pfungwa Staff", "System Admins"],
                            "template_name": "hanna_new_solar_cleaning_request"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you! Please complete the form to submit your solar panel cleaning request. Our team will contact you shortly to confirm the schedule and provide a quote."}}}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Your request has been cancelled. Type 'menu' to start over."}}}
        }
    ]
}