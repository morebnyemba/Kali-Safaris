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