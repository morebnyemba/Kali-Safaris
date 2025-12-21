# whatsappcrm_backend/flows/definitions/main_menu_flow.py

MAIN_MENU_FLOW = {
    "name": "main_menu",
    "friendly_name": "Main Menu",
    "description": "The main navigation menu for Kalai Safaris customers, directing them to tour booking and related services.",
    "trigger_keywords": ["menu", "help", "hi", "hello", "start", "main menu", "book tour", "safari", "tour"],
    "is_active": True,
    "steps": [
        {
            "name": "show_main_menu",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Kalai Safaris Main Menu"},
                        "body": {"text": "Welcome{% if contact.name %}, {{ contact.name }}{% endif %}! How can we help you plan your next adventure? Please select an option below."},
                        "footer": {"text": "Session expires after 5 mins of inactivity"},
                        "action": {
                            "button": "Select an Option",
                            "sections": [
                                {
                                    "title": "Bookings & Tours",
                                    "rows": [
                                        {"id": "book_tour", "title": "🦁 Book a Tour", "description": "Start a new safari or custom tour booking."},
                                        {"id": "view_tours", "title": "🌍 View Available Tours", "description": "See all our upcoming and featured tours."},
                                        {"id": "special_offers", "title": "🎉 Special Offers", "description": "Check out our latest deals and discounts."}
                                    ]
                                },
                                {
                                    "title": "Management",
                                    "rows": [
                                        {"id": "my_bookings", "title": "📖 My Bookings", "description": "View or manage your existing bookings."},
                                        {"id": "payment_options", "title": "💳 Make a Payment", "description": "Pay for your booking via multiple payment methods."}
                                    ]
                                },
                                {
                                    "title": "Support & Info",
                                    "rows": [
                                        {"id": "faq", "title": "❓ FAQs", "description": "Frequently asked questions about Kalai Safaris."},
                                        {"id": "contact_support", "title": "🆘 Contact Support", "description": "Get help from our team."},
                                        {"id": "about_kalai", "title": "ℹ️ About Kalai Safaris", "description": "Learn more about us."}
                                    ]
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "menu_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_booking_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "book_tour"}},
                {"to_step": "switch_to_view_tours_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "view_tours"}},
                {"to_step": "switch_to_special_offers_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "special_offers"}},
                {"to_step": "switch_to_my_bookings_flow", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "my_bookings"}},
                {"to_step": "show_payment_options", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "payment_options"}},
                {"to_step": "switch_to_faq_flow", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq"}},
                {"to_step": "switch_to_contact_support_flow", "priority": 6, "condition_config": {"type": "interactive_reply_id_equals", "value": "contact_support"}},
                {"to_step": "show_about_kalai", "priority": 7, "condition_config": {"type": "interactive_reply_id_equals", "value": "about_kalai"}}
            ]
        },
        {
            "name": "switch_to_booking_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "booking_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_view_tours_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "view_available_tours_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_special_offers_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "special_offers_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_my_bookings_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "my_bookings_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_faq_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "faq_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_omari_payment_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "omari_payment_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_paynow_payment_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "paynow_payment_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "switch_to_manual_payment_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "manual_payment_flow", "initial_context_template": {"source_flow": "main_menu"}},
            "transitions": []
        },
        {
            "name": "show_payment_options",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Payment Options"},
                        "body": {"text": "How would you like to pay for your booking?"},
                        "footer": {"text": "Select a payment method below"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "omari_payment", "title": "💳 Omari"}},
                                {"type": "reply", "reply": {"id": "paynow_payment", "title": "📱 Ecocash, Innbucks, OneMoney"}},
                                {"type": "reply", "reply": {"id": "manual_payment", "title": "🏦 Manual Payment"}},
                                {"type": "reply", "reply": {"id": "back_to_main", "title": "Back to Menu"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_omari_payment_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "omari_payment"}},
                {"to_step": "switch_to_paynow_payment_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "paynow_payment"}},
                {"to_step": "switch_to_manual_payment_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_payment"}},
                {"to_step": "show_main_menu", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "back_to_main"}}
            ]
        },
        {
            "name": "switch_to_contact_support_flow",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Our support team is here to help! Please describe your issue, or email bookings@kalaisafaris.com."}
            },
            "transitions": []
        },
        {
            "name": "show_about_kalai",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Kalai Safaris is dedicated to providing unforgettable safari experiences across Africa. Our expert guides, eco-friendly practices, and passion for wildlife ensure every journey is safe, educational, and inspiring. Type 'menu' to return to the main menu."}
            },
            "transitions": []
        }
    ]
}