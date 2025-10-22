# whatsappcrm_backend/flows/definitions/tour_inquiry_flow.py

TOUR_INQUIRY_FLOW = {
    "name": "tour_inquiry_flow",
    "friendly_name": "Tour Inquiry",
    "description": "Guides a user through making a new tour inquiry.",
    "trigger_keywords": ["inquiry", "plan a trip", "custom tour"],
    "is_active": True,
    "steps": [
        {
            "name": "start_inquiry",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "You'd like to plan a trip! I can help with that. Let's get a few details to start.\n\nFirst, what is your full name?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_full_name"}
            },
            "transitions": [{"to_step": "ask_destination", "condition_config": {"type": "variable_exists", "variable_name": "inquiry_full_name"}}]
        },
        {
            "name": "ask_destination",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thanks, {{ inquiry_full_name }}. What destination or type of safari are you interested in? (e.g., 'Victoria Falls', 'Hwange Safari', 'Cultural tour')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_destination"}
            },
            "transitions": [
                {"to_step": "start_inquiry", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_travelers", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "inquiry_destination"}}
            ]
        },
        {
            "name": "ask_travelers",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "How many people will be traveling?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_travelers", "validation_regex": "^[1-9][0-9]*$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid number (e.g., 2)."}
            },
            "transitions": [
                {"to_step": "ask_destination", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_travel_dates", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "inquiry_travelers"}}
            ]
        },
        {
            "name": "ask_travel_dates",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What are your preferred travel dates? (e.g., 'Mid-December', 'Any time in June')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_dates"}
            },
            "transitions": [
                {"to_step": "ask_travelers", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_notes", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "inquiry_dates"}}
            ]
        },
        {
            "name": "ask_notes",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Is there anything else we should know? (e.g., special occasions, specific interests, budget). Type 'N/A' if not."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_notes"}
            },
            "transitions": [
                {"to_step": "ask_travel_dates", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "save_inquiry", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "inquiry_notes"}}
            ]
        },
        {
            "name": "save_inquiry",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "TourInquiry",
                        "fields_template": {
                            "customer": "current",
                            "destination": "{{ inquiry_destination }}",
                            "tour_type": "{{ inquiry_destination }}",
                            "number_of_travelers": "{{ inquiry_travelers }}",
                            "preferred_travel_dates": "{{ inquiry_dates }}",
                            "notes": "Full Name: {{ inquiry_full_name }}. Notes: {{ inquiry_notes }}"
                        },
                        "save_to_variable": "created_inquiry"
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "first_name": "{{ inquiry_full_name.split(' ')[0] if ' ' in inquiry_full_name else inquiry_full_name }}",
                            "last_name": "{{ ' '.join(inquiry_full_name.split(' ')[1:]) if ' ' in inquiry_full_name else '' }}"
                        }
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
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you, {{ inquiry_full_name }}! Your tour inquiry has been received. One of our travel experts will get in touch with you shortly to help plan your perfect trip."}}}
        }
    ]
}

```

### 2. Revise the Main Menu Flow Definition

Next, let's update your `main_menu_flow.py` to use the new "Kali Safaris" theme and link to the `tour_inquiry_flow` we just created.

```diff
--- a/d:\Chatbot Projects\Kali Safaris\whatsappcrm_backend\flows\definitions\main_menu_flow.py
+++ b/d:\Chatbot Projects\Kali Safaris\whatsappcrm_backend\flows\definitions\main_menu_flow.py