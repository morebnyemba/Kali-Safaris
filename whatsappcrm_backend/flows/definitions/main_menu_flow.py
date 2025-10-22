# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "kali_safaris_main_menu",
    "friendly_name": "Kali Safaris: Main Menu",
    "description": "The primary navigation menu for Kali Safaris customers.",
    "trigger_keywords": ['menu', 'help', 'hi', 'hello', 'start', 'main menu', 'start over'],
    "is_active": True,
    "steps": [
        {
            "name": "ensure_customer_profile_exists",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "customer_data", "model_name": "CustomerProfile", "fields_template": {"contact": "current"}, "on_conflict": "do_nothing"
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
                        "header": {"type": "text", "text": "Kali Safaris"},
                        "body": {"text": "Welcome to Kali Safaris, {{ contact.name | default('adventurer') }}! 🦒\n\nI'm your virtual assistant. How can I help you plan your next unforgettable experience?"},
                        "footer": {"text": "Please select an option"},
                        "action": {
                            "button": "Choose an Option",
                            "sections": [
                                {
                                    "title": "Explore & Plan",
                                    "rows": [
                                        {"id": "view_tours", "title": "🏞️ View Available Tours", "description": "See our list of curated tour packages."},
                                        {"id": "plan_custom_tour", "title": "🦁 Plan a Custom Tour", "description": "Let us build a personalized trip for you."},
                                        {"id": "special_events", "title": "🎉 Special Events", "description": "Check for upcoming special offers and events."}
                                    ]
                                },
                                {
                                    "title": "My Account & Support",
                                    "rows": [
                                        {"id": "my_tours", "title": "📄 My Bookings", "description": "Check the status of your existing bookings."},
                                        {"id": "speak_to_agent", "title": "🗣️ Speak to an Agent", "description": "Get help from one of our travel experts."}
                                    ]
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "menu_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_view_tours_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "view_tours"}},
                {"to_step": "switch_to_inquiry_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "plan_custom_tour"}},
                {"to_step": "show_coming_soon", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "special_events"}},
                {"to_step": "show_coming_soon", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "my_tours"}},
                {"to_step": "trigger_human_handover", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "speak_to_agent"}}
            ]
        },
        {
            "name": "trigger_human_handover",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Sales Team", "System Admins"],
                            "template_name": "human_handover_flow",
                            "context_template": {
                                "last_bot_message": "User requested to speak with an agent from the main menu."
                            }
                        }
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_after_handover", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_after_handover",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you. I've notified our team and one of our travel experts will be with you shortly."}
                }
            }
        },
        {
            "name": "switch_to_inquiry_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "tour_inquiry_flow",
                "initial_context_template": {"source_flow": "main_menu"}
            },
            "transitions": []
        },
        {
            "name": "switch_to_view_tours_flow",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "view_available_tours_flow",
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
        }
    ]
}