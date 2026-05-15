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
                        "header": {"type": "text", "text": "🌍 Kalai Safaris Menu"},
                        "body": {"text": "Welcome{% if contact.name %}, *{{ contact.name }}*{% endif %}! 🦁\n\nHow can we help you plan your next adventure?\n\n💡 *Quick tip:* All options are organized by category below."},
                        "footer": {"text": "⏱️ Session expires after 5 mins of inactivity"},
                        "action": {
                            "button": "Select an Option",
                            "sections": [
                                {
                                    "title": "🎯 Bookings & Tours",
                                    "rows": [
                                        {"id": "view_tours", "title": "🌍 View Available Tours", "description": "Browse all our upcoming and featured tours"},
                                        {"id": "book_tour", "title": "🦁 Book a Tour", "description": "Start a new safari or custom tour booking (~5 min)"},
                                        {"id": "special_offers", "title": "🎉 Special Offers", "description": "Check out our latest deals and discounts"}
                                    ]
                                },
                                {
                                    "title": "📋 My Account",
                                    "rows": [
                                        {"id": "my_bookings", "title": "📖 My Bookings", "description": "View or manage your existing bookings"},
                                        {"id": "payment_options", "title": "💳 Make a Payment", "description": "Pay via Omari, EcoCash, or bank transfer"}
                                    ]
                                },
                                {
                                    "title": "🆘 Support & Info",
                                    "rows": [
                                        {"id": "faq", "title": "❓ FAQs", "description": "Frequently asked questions & answers"},
                                        {"id": "contact_support", "title": "📞 Contact Support", "description": "Get help from our friendly team"},
                                        {"id": "about_kalai", "title": "ℹ️ About Us", "description": "Learn more about Kalai Safaris"}
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
                {"to_step": "ask_payment_target", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "payment_options"}},
                {"to_step": "switch_to_faq_flow", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "faq"}},
                {"to_step": "switch_to_contact_support_flow", "priority": 6, "condition_config": {"type": "interactive_reply_id_equals", "value": "contact_support"}},
                {"to_step": "show_about_kalai", "priority": 7, "condition_config": {"type": "interactive_reply_id_equals", "value": "about_kalai"}}
            ]
        },
        {
            "name": "ask_payment_target",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "💳 Payment Type"},
                        "body": {"text": "What would you like to pay for?\n\n📝 *Note:* Have your booking or inquiry reference ready."},
                        "action": {
                            "button": "Select Payment Type",
                            "sections": [
                                {
                                    "title": "💰 Payments",
                                    "rows": [
                                        {"id": "booking_payment", "title": "Pay for Booking", "description": "Pay deposit or balance for your safari booking"}
                                    ]
                                },
                                {
                                    "title": "📋 Inquiries",
                                    "rows": [
                                        {"id": "tour_inquiry_payment", "title": "Pay for Inquiry", "description": "Pay against a custom tour inquiry reference"}
                                    ]
                                },
                                {
                                    "title": "◀️ Navigation",
                                    "rows": [
                                        {"id": "back_to_main", "title": "Back to Main Menu", "description": "Return to main menu"}
                                    ]
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_target"}
            },
            "transitions": [
                {"to_step": "set_payment_target_booking", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "booking_payment"}},
                {"to_step": "set_payment_target_inquiry", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "tour_inquiry_payment"}},
                {"to_step": "show_main_menu", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "back_to_main"}}
            ]
        },
        {
            "name": "set_payment_target_booking",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_target", "value_template": "booking"}
                ]
            },
            "transitions": [{"to_step": "show_payment_options", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_payment_target_inquiry",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_target", "value_template": "inquiry"}
                ]
            },
            "transitions": [{"to_step": "show_payment_options", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "switch_to_booking_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "custom_tour_confirmation_flow", "initial_context_template": {"source_flow": "main_menu"}},
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
            "config": {"target_flow_name": "omari_payment_flow", "initial_context_template": {"source_flow": "main_menu", "payment_target": "{{ payment_target }}"}},
            "transitions": []
        },
        {
            "name": "switch_to_ecocash_payment_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "ecocash_payment_flow", "initial_context_template": {"source_flow": "main_menu", "payment_target": "{{ payment_target }}"}},
            "transitions": []
        },
        {
            "name": "switch_to_manual_payment_flow",
            "type": "switch_flow",
            "config": {"target_flow_name": "manual_payment_flow", "initial_context_template": {"source_flow": "main_menu", "payment_target": "{{ payment_target }}"}},
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
                        "header": {"type": "text", "text": "💳 Choose Payment Method"},
                        "body": {"text": "Select how you'd like to pay:\n\n💡 *All methods are secure and instant*"},
                        "footer": {"text": "Your payment will be confirmed within minutes"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "omari_payment", "title": "💳 Omari"}},
                                {"type": "reply", "reply": {"id": "ecocash_payment", "title": "EcoCash"}},
                                {"type": "reply", "reply": {"id": "manual_payment", "title": "🏦 Bank Transfer"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_omari_payment_flow", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "omari_payment"}},
                {"to_step": "switch_to_ecocash_payment_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "ecocash_payment"}},
                {"to_step": "switch_to_manual_payment_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_payment"}},
                {"to_step": "show_main_menu", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "back_to_main"}}
            ]
        },
        {
            "name": "switch_to_contact_support_flow",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "📞 *Contact Support*\n\nOur team is here to help you!\n\n📧 *Email:* bookings@kalaisafaris.com\n📱 *WhatsApp:* Reply here with your question\n⏰ *Hours:* Mon-Fri 8AM-6PM, Sat 9AM-1PM\n\n💬 *Quick Help:*\nDescribe your issue and we'll respond as soon as possible."},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "back_to_main_support", "title": "Main Menu"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "support_nav_choice"},
                "fallback_config": {"re_prompt_message_text": "Please tap Main Menu to continue."}
            },
            "transitions": [
                {"to_step": "show_main_menu", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "back_to_main_support"}},
                {"to_step": "show_main_menu", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "show_about_kalai",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "🌍 *About Kalai Safaris*\n\nWelcome to Africa's premier safari experience! ✨\n\n🦁 *Our Mission:*\nProviding unforgettable, sustainable safari adventures across Africa's most spectacular landscapes.\n\n⭐ *What Makes Us Special:*\n• Expert local guides with years of experience\n• Eco-friendly practices protecting wildlife\n• Small group sizes for personalized attention\n• Flexible itineraries tailored to you\n• 24/7 support during your journey\n\n🏆 *Awards & Recognition:*\nTop-rated safari operator | Certified eco-tourism partner\n\n📍 *Coverage:* Victoria Falls, Hwange, Kruger, Serengeti, and more!"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "back_to_main_about", "title": "Main Menu"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "about_nav_choice"},
                "fallback_config": {"re_prompt_message_text": "Please tap Main Menu to continue."}
            },
            "transitions": [
                {"to_step": "show_main_menu", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "back_to_main_about"}},
                {"to_step": "show_main_menu", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        }
    ]
}