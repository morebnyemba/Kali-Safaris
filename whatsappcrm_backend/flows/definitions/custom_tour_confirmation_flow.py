# whatsappcrm_backend/flows/definitions/custom_tour_confirmation_flow.py

CUSTOM_TOUR_CONFIRMATION_FLOW = {
    "name": "custom_tour_confirmation_flow",
    "friendly_name": "Custom Tour Inquiry",
    "description": "Collects custom tour requirements, saves an inquiry, and returns a unique reference.",
    "trigger_keywords": [],  # Triggered from main menu switch
    "is_active": True,
    "steps": [
        {
            "name": "ask_custom_tour_destination",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Tell us where in Zimbabwe you would like to visit.\n\nExample: Victoria Falls, Hwange, and Great Zimbabwe."
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "custom_tour_destination"
                },
                "fallback_config": {
                    "re_prompt_message_text": "Please share your preferred destination(s) in Zimbabwe."
                }
            },
            "transitions": [
                {"to_step": "ask_custom_tour_travelers", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_custom_tour_travelers",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "How many travelers are in your group?"
                    }
                },
                "reply_config": {
                    "expected_type": "number",
                    "save_to_variable": "custom_tour_travelers",
                    "validation_regex": "^[1-9][0-9]*$"
                },
                "fallback_config": {
                    "re_prompt_message_text": "Please enter a valid number of travelers (e.g., 2)."
                }
            },
            "transitions": [
                {"to_step": "ask_custom_tour_dates", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_custom_tour_dates",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "What are your preferred travel dates?\n\nExample: 10 Aug 2026 to 15 Aug 2026"
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "custom_tour_dates"
                },
                "fallback_config": {
                    "re_prompt_message_text": "Please share your preferred dates so we can prepare your quote."
                }
            },
            "transitions": [
                {"to_step": "ask_custom_tour_notes", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_custom_tour_notes",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Share any special requirements (budget, accommodation style, activities, transport, dietary needs).\n\nIf none, type *none*."
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "custom_tour_notes"
                }
            },
            "transitions": [
                {"to_step": "ask_custom_tour_email", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_custom_tour_email",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "What is your email address for your quote and itinerary?\n\nIf you prefer WhatsApp only, type *skip*."
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "custom_tour_email"
                }
            },
            "transitions": [
                {"to_step": "confirm_custom_tour_inquiry", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "confirm_custom_tour_inquiry",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Confirm Your Inquiry"},
                        "body": {
                            "text": "Please review your details:\n\n📍 Destination(s): {{ custom_tour_destination }}\n👥 Travelers: {{ custom_tour_travelers }}\n📅 Preferred Dates: {{ custom_tour_dates }}\n📝 Notes: {{ custom_tour_notes }}\n📧 Email: {{ custom_tour_email }}\n\nNo payment is required now. We will send a custom quote first."
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_inquiry", "title": "Submit Inquiry"}},
                                {"type": "reply", "reply": {"id": "edit_inquiry", "title": "Edit Details"}},
                                {"type": "reply", "reply": {"id": "cancel_inquiry", "title": "Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {
                    "expected_type": "interactive_id",
                    "save_to_variable": "custom_inquiry_confirmation_choice"
                }
            },
            "transitions": [
                {
                    "to_step": "create_custom_tour_inquiry_record",
                    "priority": 1,
                    "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_inquiry"}
                },
                {
                    "to_step": "ask_custom_tour_destination",
                    "priority": 2,
                    "condition_config": {"type": "interactive_reply_id_equals", "value": "edit_inquiry"}
                },
                {
                    "to_step": "end_flow_cancelled",
                    "priority": 3,
                    "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_inquiry"}
                }
            ]
        },
        {
            "name": "create_custom_tour_inquiry_record",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "TourInquiry",
                        "fields_template": {
                            "customer": "current",
                            "lead_traveler_name": "{{ contact.name }}",
                            "destinations": "{{ custom_tour_destination }}",
                            "preferred_dates": "{{ custom_tour_dates }}",
                            "number_of_travelers": "{{ custom_tour_travelers }}",
                            "notes": "Custom tour request via WhatsApp.\\nSpecial requirements: {{ custom_tour_notes }}\\nContact email: {{ custom_tour_email }}",
                            "status": "new"
                        },
                        "save_to_variable": "created_inquiry"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Sales Team"],
                            "template_name": "new_tour_inquiry_alert"
                        }
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_confirmed", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_confirmed",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Your custom tour inquiry has been submitted successfully.\n\nReference: #{{ created_inquiry.inquiry_reference }}\n\nA travel specialist will contact you with your personalized quote within 24 hours.\nNo payment is required until you approve the itinerary.\n\nType *menu* to return to the main menu."
                    }
                }
            }
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Inquiry cancelled. If you want to start again, type *menu*."
                    }
                }
            }
        }
    ]
}
