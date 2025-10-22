# whatsappcrm_backend/flows/definitions/tour_inquiry_flow.py

TOUR_INQUIRY_FLOW = {
    "name": "tour_inquiry_flow",
    "friendly_name": "Tour Inquiry",
    "description": "Guides a user through creating a custom tour inquiry.",
    "trigger_keywords": ["custom tour", "inquiry", "plan a tour"],
    "is_active": True,
    "steps": [
        {
            "name": "start_inquiry",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "I can help with that! To create a personalized tour for you, I'll need a few details.\n\nFirst, what is the full name of the lead traveler?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_full_name"}
            },
            "transitions": [{"to_step": "ask_destination", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_destination",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Great, {{ inquiry_full_name }}. Which destinations are you interested in? (e.g., Victoria Falls, Hwange, Mana Pools)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_destination"}
            },
            "transitions": [{"to_step": "ask_travelers", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_travelers",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "How many people will be traveling (adults and children)?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_travelers"}
            },
            "transitions": [{"to_step": "ask_dates", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_dates",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What are your preferred travel dates? (e.g., 'mid-June 2025', 'any time in September')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_dates"}
            },
            "transitions": [{"to_step": "ask_notes", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_notes",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Perfect. Is there anything else you'd like us to know? (e.g., interests like photography, specific lodges, budget)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_notes"}
            },
            "transitions": [{"to_step": "confirm_and_save_inquiry", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "confirm_and_save_inquiry",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "TourInquiry",
                        "fields_template": {
                            "customer": "current",
                            "lead_traveler_name": "{{ inquiry_full_name }}",
                            "destinations": "{{ inquiry_destination }}",
                            "number_of_travelers": "{{ inquiry_travelers }}",
                            "preferred_dates": "{{ inquiry_dates }}",
                            "notes": "{{ inquiry_notes }}",
                            "status": "new"
                        },
                        "save_to_variable": "created_inquiry"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Sales Team", "System Admins"],
                            "template_name": "new_tour_inquiry_alert"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_inquiry_message", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_inquiry_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! We've received your inquiry (Ref: #{{ created_inquiry.id }}). One of our travel specialists will review your request and get back to you shortly with a personalized itinerary."}
                }
            }
        }
    ]
}