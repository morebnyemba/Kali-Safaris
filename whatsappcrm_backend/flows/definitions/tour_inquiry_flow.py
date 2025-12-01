# whatsappcrm_backend/flows/definitions/tour_inquiry_flow.py

TOUR_INQUIRY_FLOW = {
    "name": "tour_inquiry_flow",
    "friendly_name": "Tour Inquiry Collection Flow",
    "description": "A flow to guide a user through submitting a tour inquiry using an interactive WhatsApp flow.",
    "trigger_keywords": ["inquire", "safari", "trip", "booking", "tour"],
    "is_active": True,
    "steps": [
        {
                # Placeholder for missing step: confirm_and_end (if not already present)
                # (No action needed if already present)
            "name": "entry_point_inquiry",
            "is_entry_point": True,
            "type": "send_message",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "flow",
                    "header": {"type": "text", "text": "Plan Your Dream Safari"},
                    "body": {"text": "Let's get some details to help you plan the perfect trip!"},
                    "footer": {"text": "Tap below to start"},
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "YOUR_UNIQUE_FLOW_TOKEN", # This can be dynamically generated
                            "flow_id": "{{ get_whatsapp_flow_id('tour_inquiry_whatsapp') }}", # Dynamically retrieved from WhatsAppFlow model
                            "flow_cta": "Start Inquiry",
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": "welcome_screen"
                            }
                        }
                    }
                }
            },
            "transitions": [
                {
                    "to_step": "wait_for_flow_response",
                    "condition_config": {"type": "always_true"}
                }
            ]
        },
        {
            "name": "wait_for_flow_response",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "awaiting_inquiry_response",
                        "value_template": True
                    }
                ]
            },
            "transitions": [
                {
                    "to_step": "process_inquiry_data",
                    "priority": 1,
                    "condition_config": {
                        "type": "whatsapp_flow_response_received",
                        "variable_name": "whatsapp_flow_response_received"
                    }
                },
                {
                    "to_step": "inquiry_flow_support",
                    "priority": 2,
                    "condition_config": {"type": "timeout_or_missing_data", "timeout_seconds": 600}
                }
            ]
        },
        # Fallback/support step if WhatsApp flow is incomplete or times out
        {
            "name": "inquiry_flow_support",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "It looks like your inquiry was not completed. If you need help or want to try again, please type 'menu' or contact our team at bookings@kalaisafaris.com."}
            },
            "transitions": [
                {"to_step": "confirm_and_end", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "process_inquiry_data",
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
                            "destinations": "{{ whatsapp_flow_data.destinations }}",
                            "preferred_dates": "{{ whatsapp_flow_data.preferred_dates }}",
                            "number_of_travelers": "{{ whatsapp_flow_data.number_of_travelers }}",
                            "notes": "{{ whatsapp_flow_data.notes }}"
                        },
                        "save_to_variable": "created_inquiry"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Sales", "Admins"],
                            "template_name": "hanna_new_tour_inquiry",
                            "template_context": {
                                "inquiry_id": "{{ created_inquiry.id }}",
                                "customer_name": "{{ contact.name }}",
                                "destinations": "{{ whatsapp_flow_data.destinations }}",
                                "dates": "{{ whatsapp_flow_data.preferred_dates }}"
                            }
                        }
                    }
                ]
            },
            "transitions": [
                {
                    "to_step": "confirm_and_end",
                    "condition_config": {"type": "always_true"}
                }
            ]
        },
        {
            "name": "confirm_and_end",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Thank you for your inquiry! Our team has received your details and will get back to you shortly with a personalized plan. Your inquiry reference is #{{ created_inquiry.id|stringformat:'s'|slice:'-8' }}."
                    }
                }
            }
        }
    ]
}
