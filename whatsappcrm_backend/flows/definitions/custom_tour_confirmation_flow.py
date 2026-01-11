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
                        "header": {"type": "text", "text": "Confirm Your Inquiry"},
                        "body": {
                            "text": """Thank you, {{ inquiry_full_name }}! Please review your custom tour inquiry:

*Destination:* {{ inquiry_destination }}
*Travelers:* {{ inquiry_travelers }}
*Dates:* {{ inquiry_dates }}
*Notes:* {{ inquiry_notes }}

Shall I proceed and create a booking request for you? A travel expert will then finalize the details and send you a quote."""
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
                    "message_type": "text",
                    "text": {"body": "Here is a summary of your custom tour inquiry:\n\n*Destinations:* {{ destinations }}\n*Preferred Dates:* {{ preferred_dates }}\n*Number of Travelers:* {{ number_of_travelers }}\n*Notes:* {{ notes }}\n\nIs everything correct? (yes/edit)"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "summary_confirmation"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please reply 'yes' to confirm or 'edit' to make changes."}
            },
            "transitions": [
                {"to_step": "submit_custom_tour_inquiry", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "summary_confirmation", "value": "yes"}},
                {"to_step": "edit_custom_tour_details", "priority": 2, "condition_config": {"type": "variable_equals", "variable_name": "summary_confirmation", "value": "edit"}},
                {"to_step": "custom_tour_support", "priority": 3, "condition_config": {"type": "invalid_or_no_selection"}},
                {"to_step": "show_custom_tour_summary", "priority": 4, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "custom_tour_support",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "If you need help or want to start over, type 'menu' or contact bookings@kalaisafaris.com."}
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
                "text": {"body": "Let's edit your custom tour details. Please provide the updated information or type 'menu' to return to the main menu."}
            },
            "transitions": [{"to_step": "show_custom_tour_summary", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_custom_tour_confirmation",
            "type": "end_flow",
            "config": {},
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
                    "text": {"body": "Excellent! Your booking request (Ref: #{{ created_booking_from_inquiry.booking_reference }}) has been created. A travel specialist will be in touch shortly to finalize your itinerary and provide a detailed quote.\n\nType 'menu' to return to the main menu."}
                }
            }
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Your inquiry has been cancelled. If you change your mind, just type 'menu' to start over."}
                }
            }
        }
    ]
}