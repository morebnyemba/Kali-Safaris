# whatsappcrm_backend/flows/definitions/custom_tour_confirmation_flow.py

CUSTOM_TOUR_CONFIRMATION_FLOW = {
    "name": "custom_tour_confirmation_flow",
    "friendly_name": "Custom Tour Confirmation",
    "description": "Confirms a custom tour inquiry and converts it to a booking.",
    "trigger_keywords": [],  # This flow is triggered by a switch
    "is_active": True,
    "steps": [
        {
            "name": "start_confirmation",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "🌍 Custom Tour Inquiry"},
                        "body": {
                            "text": """Thank you, *{{ inquiry_full_name }}*! ✨

Please review your custom tour inquiry:

📍 *Destination:* {{ inquiry_destination }}
👥 *Travelers:* {{ inquiry_travelers }}
📅 *Dates:* {{ inquiry_dates }}
📝 *Special Requests:* {{ inquiry_notes }}

━━━━━━━━━━━━━━━━

🎯 *What happens next?*
A travel expert will:
1. Review your requirements
2. Design a personalized itinerary
3. Send you a detailed quote

Ready to proceed?"""
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_inquiry", "title": "✅ Yes, Proceed"}},
                                {"type": "reply", "reply": {"id": "cancel_inquiry", "title": "❌ Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "confirmation_choice"}
            },
            "transitions": [
                {"to_step": "create_booking_from_inquiry_action", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_inquiry"}},
                {"to_step": "end_flow_cancelled", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_inquiry"}}
            ]
        },
        {
            "name": "show_custom_tour_summary",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "📋 Your Custom Tour Details"},
                        "body": {
                            "text": """Here's a summary of your custom tour inquiry:

📍 *Destinations:* {{ destinations }}
📅 *Preferred Dates:* {{ preferred_dates }}
👥 *Number of Travelers:* {{ number_of_travelers }}
📝 *Additional Notes:* {{ notes }}

━━━━━━━━━━━━━━━━

Is everything correct?"""
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_details", "title": "✅ Confirm"}},
                                {"type": "reply", "reply": {"id": "edit_details", "title": "✏️ Edit"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "summary_confirmation"}
            },
            "transitions": [
                {"to_step": "submit_custom_tour_inquiry", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_details"}},
                {"to_step": "edit_custom_tour_details", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "edit_details"}},
                {"to_step": "custom_tour_support", "priority": 3, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "custom_tour_support",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "💡 *Need Help?*\n\nIf you need assistance or want to start over:\n\n📱 Type *menu* to return to main menu\n📧 Email: bookings@kalaisafaris.com\n📞 Call us for immediate assistance"}
            },
            "transitions": [
                {"to_step": "end_custom_tour_confirmation", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "submit_custom_tour_inquiry",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "noop"}]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "edit_custom_tour_details",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "✏️ *Edit Your Details*\n\nLet's update your custom tour information.\n\nPlease provide the updated details, or type *menu* to return to the main menu."}
            },
            "transitions": [{"to_step": "show_custom_tour_summary", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_custom_tour_confirmation",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Type *menu* to return to the main menu when you're ready."}
                }
            },
            "transitions": []
        },
        {
            "name": "create_booking_from_inquiry_action",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_booking_from_inquiry",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_confirmed",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": """✅ *Booking Request Created!*

Your custom tour inquiry has been successfully submitted.

📋 *Reference Number:* #{{ created_booking_from_inquiry.booking_reference }}

🎯 *What happens next?*
1. ⏱️ A travel specialist will review your request (within 24 hours)
2. 📞 They'll contact you to discuss details
3. 💰 You'll receive a personalized quote
4. ✨ We'll finalize your perfect itinerary

📧 *Track Your Request:*
Save your reference number for easy tracking.

Thank you for choosing us! Type *menu* to explore more options."""}
                }
            }
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "❌ *Inquiry Cancelled*\n\nNo worries! Your inquiry has been cancelled.\n\n🔄 *Want to try again?*\nType *menu* to start over or explore other options.\n\nWe're here whenever you're ready! 🌍✨"}
                }
            }
        },
        {
            "name": "ask_payment_option",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Confirm & Pay"},
                        "body": {"text": "Select a payment option below for your custom tour booking."},
                        "footer": {"text": "Select an option"},
                        "action": {
                            "button": "Payment Options",
                            "sections": [
                                {"title": "EcoCash", "rows": [
                                    {"id": "cbz_full", "title": "EcoCash Full Payment"},
                                    {"id": "cbz_deposit", "title": "EcoCash 50% Deposit"}
                                ]},
                                {"title": "Card (Web Checkout)", "rows": [
                                    {"id": "card_web_full", "title": "Card Full Payment"},
                                    {"id": "card_web_deposit", "title": "Card 50% Deposit"}
                                ]},
                                {"title": "Other Online Payment", "rows": [
                                    {"id": "manual_omari", "title": "Pay with Omari"}
                                ]},
                                {"title": "Manual Payment", "rows": [
                                    {"id": "manual_bank", "title": "Manual/Bank Transfer"}
                                ]},
                                {"title": "Other", "rows": [
                                    {"id": "get_quote", "title": "Just Get a Quote"}
                                ]}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_choice"}
            },
            "transitions": [
                {"to_step": "set_payment_amount_full_cbz", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "cbz_full"}},
                {"to_step": "set_payment_amount_deposit_cbz", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "cbz_deposit"}},
                {"to_step": "set_payment_amount_full_card_web", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "card_web_full"}},
                {"to_step": "set_payment_amount_deposit_card_web", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "card_web_deposit"}},
                {"to_step": "prepare_omari_payment", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_omari"}},
                {"to_step": "create_booking_for_manual_payment", "priority": 6, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_bank"}},
                {"to_step": "create_inquiry_record_only", "priority": 7, "condition_config": {"type": "interactive_reply_id_equals", "value": "get_quote"}}
            ]
        },
        {
            "name": "set_payment_amount_full_cbz",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_payment_amount_full_cbz",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_payment_amount_deposit_cbz",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_payment_amount_deposit_cbz",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_payment_amount_full_card_web",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_payment_amount_full_card_web",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_payment_amount_deposit_card_web",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_payment_amount_deposit_card_web",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "prepare_omari_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "prepare_omari_payment",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "create_booking_for_manual_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_booking_for_manual_payment",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "create_inquiry_record_only",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_inquiry_record_only",
                    "params_template": {
                        "inquiry_context_var": "created_inquiry",
                        "save_booking_to": "created_booking_from_inquiry"
                    }
                }]
            },
            "transitions": [{"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "input_custom_tour_destination",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "✏️ *Custom Tour Destination*\n\nPlease provide your preferred destination in Zimbabwe:\n\nExample: Victoria Falls, Hwange National Park, or Great Zimbabwe."
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "custom_tour_destination"
                }
            },
            "transitions": [
                {
                    "to_step": "create_booking_from_inquiry_action",
                    "priority": 1,
                    "condition_config": {"type": "always_true"}
                }
            ]
        }
    ]
}