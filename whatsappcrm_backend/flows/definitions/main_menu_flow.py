# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "main_menu",
    "friendly_name": "Main Menu",
    "description": "The primary navigation menu for customers, directing them to different services.",
    "trigger_keywords": ['menu', 'help', 'hi', 'hello', 'start', 'main menu', 'start over'],
    "is_active": True,
    "steps": [
        {
            "name": "ensure_customer_profile_exists",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {}
                }]
            },
            "transitions": [
                {"to_step": "show_main_menu", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "show_main_menu",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Pfungwa Main Menu"},
                        "body": {
                            "text": "Hello {{ contact.name | default('there') }}! I'm Hanna, your personal AI assistant for Pfungwa.\n\nHow can I help you today? Please select an option from the menu below."
                        },
                        "footer": {"text": "Session expires after 5 mins of inactivity"},
                        "action": {
                            "button": "Select an Option",
                            "sections": [
                                {
                                    "title": "Our Services",
                                    "rows": [
                                        {"id": "purchase_product", "title": "🛒 Shop Products", "description": "Browse and buy solar products."},
                                        {"id": "request_installation", "title": "🛠️ Request Installation", "description": "Schedule a Solar or Starlink installation."},
                                        {"id": "site_assessment", "title": "📋 Book Site Assessment", "description": "Book a site visit with our experts."},
                                        {"id": "solar_cleaning", "title": "💧 Solar Panel Cleaning", "description": "Request a cleaning service."},
                                        {"id": "apply_for_loan", "title": "💰 Apply for Loan", "description": "Apply for a cash or product loan."}
                                    ]
                                },
                                {
                                    "title": "Support & Information",
                                    "rows": [
                                        {"id": "request_warranty", "title": "🛡️ Request Warranty", "description": "Claim warranty for a product. (Coming Soon)"},
                                        {"id": "ai_troubleshooter", "title": "🤖 AI Troubleshooter", "description": "Get instant help from our AI assistant."},
                                        {"id": "about_pfungwa", "title": "ℹ️ About Pfungwa", "description": "Learn more about our company."}
                                    ]
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "menu_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_purchase_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "purchase_product"}},
                {"to_step": "show_installation_submenu", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_installation"}},
                {"to_step": "switch_to_assessment_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "site_assessment"}},
                {"to_step": "switch_to_cleaning_flow", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "solar_cleaning"}},
                {"to_step": "switch_to_loan_application_flow", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "apply_for_loan"}},
                {"to_step": "show_coming_soon", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_warranty"}},
                {"to_step": "start_ai_troubleshooting_session", "priority": 6, "condition_config": {"type": "interactive_reply_id_equals", "value": "ai_troubleshooter"}},
                {"to_step": "show_about_pfungwa", "priority": 7, "condition_config": {"type": "interactive_reply_id_equals", "value": "about_pfungwa"}}
            ]
        },
        {
            "name": "show_installation_submenu",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Installation Services"},
                        "body": {"text": "Great! Which type of installation service do you need?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "switch_to_solar_install", "title": "☀️ Solar"}},
                                {"type": "reply", "reply": {"id": "switch_to_starlink_install", "title": "🛰️ Starlink"}},
                                {"type": "reply", "reply": {"id": "go_back_to_main_menu", "title": "Go Back"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_solar_installation_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "switch_to_solar_install"}},
                {"to_step": "switch_to_starlink_installation_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "switch_to_starlink_install"}},
                {"to_step": "show_main_menu", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "go_back_to_main_menu"}}
            ]
        },
        {
            "name": "start_ai_troubleshooting_session",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_contact_field",
                        "field_path": "conversation_mode",
                        "value_template": "ai_troubleshooting"
                    }
                ]
            },
            "transitions": [
                {"to_step": "send_ai_welcome_message", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_ai_welcome_message",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "You are now connected to Hanna, our AI technical expert.\n\n"
                            "To get started, please describe the issue, including:\n"
                            "1. *Product Model*\n"
                            "   (e.g., `Solar Flex`, `Hanchu`, or `Beesman`)\n"
                            "2. *The Primary Symptom*\n"
                            "   (e.g., `Red light is flashing three times`)\n\n"
                            "You can also send a photo or video of the issue.\n\n"
                            "Type 'menu' at any time to exit this session."
                }
            },
            "transitions": [
                {"to_step": "end_flow_after_ai_handoff", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_after_ai_handoff",
            "type": "end_flow",
            "config": {
                # No final message is needed here, as the welcome message was already sent.
                # The flow simply needs to terminate.
            },
            "transitions": []
        },
        {
            "name": "switch_to_purchase_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "lead_generation",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_solar_installation_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "solar_installation_inquiry",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_starlink_installation_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "starlink_installation_request",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_assessment_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "site_inspection_request",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_cleaning_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "solar_cleaning_request",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_loan_application_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "loan_application_flow",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "show_coming_soon",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "This feature is coming soon! Please check back later. Type 'menu' to return to the main menu."}
            },
            "transitions": []
        },
        {
            "name": "show_about_pfungwa",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Pfungwa is a leading provider of renewable energy solutions, committed to powering a brighter, sustainable future for everyone. Type 'menu' to return to the main menu."}
            },
            "transitions": []
        }
    ]
}