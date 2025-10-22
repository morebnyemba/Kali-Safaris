# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "kalai_safaris_main_menu",
    "friendly_name": "Kalai Safaris - Main Menu",
    "description": "The main entry point for users, presenting the primary options.",
    "trigger_keywords": ['menu', 'start', 'hello', 'hi', 'main menu'],
    "is_active": True,
    "steps": [
        {
            "name": "start_main_menu",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {
                            "type": "text",
                            "text": "Welcome to Kalai Safaris! 🦒"
                        },
                        "body": {
                            "text": "Your adventure starts here! How can I help you today?"
                        },
                        "footer": {
                            "text": "Please select an option"
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "view_tours", "title": "🏞️ View Tours"}},
                                {"type": "reply", "reply": {"id": "my_bookings", "title": "🎫 My Bookings"}},
                                {"type": "reply", "reply": {"id": "faq", "title": "❓ FAQ"}},
                            ]
                        }
                    }
                },
                "reply_config": {
                    "expected_type": "interactive_id",
                    "save_to_variable": "main_menu_choice"
                }
            },
            "transitions": [
                {"to_step": "switch_to_view_tours", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "view_tours"}},
                {"to_step": "switch_to_my_bookings", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "my_bookings"}},
                {"to_step": "switch_to_faq", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq"}},
            ]
        },
        {
            "name": "switch_to_view_tours",
            "type": "switch_flow",
            "config": {"target_flow_name": "view_available_tours"}
        },
        {
            "name": "switch_to_my_bookings",
            "type": "switch_flow",
            "config": {"target_flow_name": "my_bookings_flow"}
        },
        {
            "name": "switch_to_faq",
            "type": "switch_flow",
            "config": {"target_flow_name": "faq_flow"}
        }
    ]
}