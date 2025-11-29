# whatsappcrm_backend/flows/definitions/starlink_installation_flow.py

STARLINK_INSTALLATION_FLOW = {
    "name": "starlink_installation_request",
    "friendly_name": "Request Starlink Installation",
    "description": "Initiates the WhatsApp interactive flow for Starlink installation.",
    "trigger_keywords": ['request starlink', 'starlink installation'],
    "is_active": True,
    "steps": [
        {
            "name": "ensure_customer_profile",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {}
                }]
            },
            "transitions": [
                {"to_step": "query_whatsapp_flow", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "starlink_whatsapp_flow",
                    "filters_template": {
                        "name": "starlink_installation_whatsapp",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "send_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "starlink_whatsapp_flow.0"}},
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
                    "header": {
                        "type": "text",
                        "text": "Starlink Installation"
                    },
                    "body": {
                        "text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %}\n\nPlease complete our Starlink installation form to get started."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-starlink-install-{{ 'now'|date:'U' }}",
                            "flow_id": "{{ starlink_whatsapp_flow.0.flow_id }}",
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
                {"to_step": "wait_for_whatsapp_response", "priority": 1, "condition_config": {"type": "always_true"}}
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
                {"to_step": "map_whatsapp_response_fields", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "map_whatsapp_response_fields",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "install_full_name", "value_template": "{{ whatsapp_flow_data.full_name }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_phone", "value_template": "{{ whatsapp_flow_data.contact_phone }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_kit_type", "value_template": "{{ whatsapp_flow_data.kit_type }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_mount_location", "value_template": "{{ whatsapp_flow_data.mount_location }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_datetime", "value_template": "{{ whatsapp_flow_data.preferred_date }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_availability", "value_template": "{{ whatsapp_flow_data.availability }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_address", "value_template": "{{ whatsapp_flow_data.address }}"}
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
                "text": {"body": "Sorry, the interactive form is currently unavailable. Please contact our support team to request a Starlink installation."}
            },
            "transitions": [{"to_step": "end_flow_cancelled", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "legacy_start_starlink_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Starlink Installation"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %}\n\nLet's get your Starlink installation scheduled. To start, I need to collect a few details."},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "proceed", "title": "Let's Begin"}},
                                {"type": "reply", "reply": {"id": "cancel", "title": "Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "start_choice"}
            },
            "transitions": [
                {"to_step": "ask_client_name", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "proceed"}},
                {"to_step": "end_flow_cancelled", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel"}}
            ]
        },
        {
            "name": "ask_client_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Great! What is the *Full Name* for the installation booking?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_full_name", "validation_regex": "^.{3,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid name (at least 3 characters)."}
            },
            "transitions": [
                {"to_step": "ask_client_phone", "condition_config": {"type": "variable_exists", "variable_name": "install_full_name"}}
            ]
        },
        {
            "name": "ask_client_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you, {{ install_full_name.split(' ')[0] }}. What is the best *contact number* for this installation? (e.g., +263771234567)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_phone", "validation_regex": "^\\+?[1-9]\\d{8,14}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid phone number (e.g., +263...)"}
            },
            "transitions": [
                {"to_step": "ask_client_name", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_kit_type", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_phone"}}
            ]
        },
        {
            "name": "ask_kit_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Starlink Kit Type"},
                        "body": {"text": "What type of Starlink kit do you have?\n\n(Type 'back' to change the phone number.)"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "standard", "title": "Standard"}},
                            {"type": "reply", "reply": {"id": "high_performance", "title": "High Performance"}},
                            {"type": "reply", "reply": {"id": "other", "title": "Other/Not Sure"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_kit_type"}
            },
            "transitions": [
                {"to_step": "ask_client_phone", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_install_location", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_kit_type"}}
            ]
        },
        {
            "name": "ask_install_location",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Where on the property would you like the dish installed? (e.g., On the roof, on a pole in the yard, etc.)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_mount_location"}
            },
            "transitions": [
                {"to_step": "ask_kit_type", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_install_date", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_mount_location"}}
            ]
        },
        {
            "name": "ask_install_date",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your preferred installation date? (e.g., Tomorrow, 25 December)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_datetime"}
            },
            "transitions": [
                {"to_step": "ask_install_location", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_availability", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_datetime"}}
            ]
        },
        {
            "name": "ask_availability",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "And is morning or afternoon better for you on that day?"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "morning", "title": "Morning"}},
                            {"type": "reply", "reply": {"id": "afternoon", "title": "Afternoon"}},
                            {"type": "reply", "reply": {"id": "go_back", "title": "Go Back"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_availability"}
            },
            "transitions": [
                {"to_step": "ask_install_date", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "go_back"}},
                {"to_step": "ask_install_address", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_availability"}}
            ]
        },
        {
            "name": "ask_install_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the full installation address?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_address", "validation_regex": "^.{10,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please provide a more detailed address."}
            },
            "transitions": [
                {"to_step": "ask_availability", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_location_pin", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_address"}}
            ]
        },
        {
            "name": "ask_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Finally, please share your location pin for accurate directions. You can also type 'skip'."}},
                "reply_config": {"expected_type": "location", "save_to_variable": "install_location_pin"}
            },
            "transitions": [
                {"to_step": "set_skipped_location", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "skip"}},
                {"to_step": "confirm_installation_request", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_location_pin"}}
            ]
        },
        {
            "name": "set_skipped_location",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "install_location_pin", "value_template": {"latitude": None, "longitude": None}}]},
            "transitions": [{"to_step": "confirm_installation_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "confirm_installation_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Please review your details:\n\n*Name*: {{ install_full_name }}\n*Phone*: {{ install_phone }}\n*Kit Type*: {{ install_kit_type|title }}\n*Install Location*: {{ install_mount_location }}\n*Date*: {{ install_datetime }} ({{ install_availability|title }})\n*Address*: {{ install_address }}"},
                        "action": {"buttons": [
                            {"type": "reply", "reply": {"id": "confirm_install", "title": "Confirm & Submit"}},
                            {"type": "reply", "reply": {"id": "go_back_to_pin", "title": "Go Back"}},
                            {"type": "reply", "reply": {"id": "cancel_install", "title": "Cancel"}}
                        ]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_confirmation"}
            },
            "transitions": [
                {"to_step": "save_installation_request", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_install"}},
                {"to_step": "ask_location_pin", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "go_back_to_pin"}},
                {"to_step": "end_flow_cancelled", "priority": 3, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_installation_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "InstallationRequest",
                        "fields_template": {
                            "customer_id": "{{ contact.id }}",
                            "installation_type": "starlink",
                            "full_name": "{{ install_full_name }}",
                            "contact_phone": "{{ install_phone }}",
                            "notes": "Kit Type: {{ install_kit_type|title }}. Mount Location: {{ install_mount_location }}.",
                            "address": "{{ install_address }}",
                            "latitude": "{{ install_location_pin.latitude }}",
                            "longitude": "{{ install_location_pin.longitude }}",
                            "preferred_datetime": "{{ install_datetime }}",
                            "availability": "{{ install_availability }}"
                        },
                        "save_to_variable": "created_installation_request"
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "first_name": "{{ install_full_name.split(' ')[0] if ' ' in install_full_name else install_full_name }}", "last_name": "{{ ' '.join(install_full_name.split(' ')[1:]) if ' ' in install_full_name else '' }}", "address_line_1": "{{ install_address }}",
                            "notes": "Profile updated from Starlink Installation Request flow."
                        }
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Pfungwa Staff", "System Admins"],
                            "template_name": "hanna_new_starlink_installation_request"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you! Please complete the form to submit your Starlink installation request. Our team will contact you shortly to confirm the schedule."}}}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Your request has been cancelled. Type 'menu' to start over."}}}
        }
    ]
}