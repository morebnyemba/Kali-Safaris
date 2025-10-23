# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "kalai_safaris_main_menu",
    "friendly_name": "Kalai Safaris: Main Menu",
    "description": "The main entry point for users, presenting the primary options.",
    "trigger_keywords": ['menu', 'start', 'hello', 'hi', 'main menu'],
    "is_active": True,
    "steps": [
        {
            "name": "start_main_menu",
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
                        "header": {
                            "type": "text",
                            "text": "Kalai Safaris"
                        },
                        "body": {
                            "text": "Welcome to Kalai Safaris, {{ contact.name | default('adventurer') }}! 🦒\n\nI'm your virtual assistant. How can I help you plan your next unforgettable experience?"
                        },
                        "footer": {
                            "text": "Session resets after 5 mins of inactivity"
                        },
                        "action": {
                            "button": "Choose an Option",
                            "sections": [
                                {
                                    "title": "Explore & Plan",
                                    "rows": [
                                        {"id": "view_tours", "title": "🏞️ View Tours", "description": "See our list of curated tour packages."},
                                        {"id": "plan_custom_tour", "title": "🦁 Plan a Custom Tour", "description": "Let's build a personalized trip for you."},
                                        {"id": "special_events", "title": "🎉 Special Offers", "description": "Check for current deals and events."}
                                    ]
                                },
                                {
                                    "title": "My Account & Support",
                                    "rows": [
                                        {"id": "my_bookings", "title": "📄 My Bookings", "description": "Check the status of your existing bookings."},
                                        {"id": "record_payment", "title": "💵 Record a Payment", "description": "Record a manual payment you have made."},
                                        {"id": "faq", "title": "❓ FAQ", "description": "Find answers to common questions."},
                                        {"id": "about_us", "title": "🏢 About Us", "description": "Learn more about Kalai Safaris."},
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
                {"to_step": "switch_to_special_offers_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "special_events"}},
                {"to_step": "switch_to_my_bookings_flow", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "my_bookings"}},
                {"to_step": "switch_to_manual_payment_flow", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "record_payment"}},
                {"to_step": "switch_to_faq_flow", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq"}},
                {"to_step": "show_about_us", "priority": 6, "condition_config": {"type": "interactive_reply_id_equals", "value": "about_us"}},
                {"to_step": "trigger_human_handover", "priority": 7, "condition_config": {"type": "interactive_reply_id_equals", "value": "speak_to_agent"}}
            ]
        },
        {
            "name": "trigger_human_handover",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "Thank you. I've notified our team and one of our travel experts will be with you shortly.",
                "notification_details": "User requested to speak with an agent from the main menu."
            }
        },
        {
            "name": "switch_to_inquiry_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "tour_inquiry_flow"}
        },
        {
            "name": "switch_to_view_tours_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "view_available_tours_flow"}
        },
        {
            "name": "switch_to_special_offers_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "special_offers_flow"}
        },
        {
            "name": "switch_to_my_bookings_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "my_bookings_flow"}
        },
        {
            "name": "switch_to_manual_payment_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "manual_payment_flow"}
        },
        {
            "name": "switch_to_faq_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "faq_flow"}
        },
        {
            "name": "show_about_us",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Kalai Safaris is a premier tour operator specializing in bespoke African adventures. We are passionate about creating unforgettable experiences that connect you with the wild heart of Africa.\n\nType 'menu' to return."}
            }
        }
    ]
}