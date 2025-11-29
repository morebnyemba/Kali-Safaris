# whatsappcrm_backend/flows/definitions/site_inspection_flow.py

SITE_INSPECTION_FLOW = {
    "name": "site_inspection_request",
    "friendly_name": "Site Assessment Request",
    "description": "Initiates the WhatsApp interactive flow for site assessment requests (message-based fallback).",
    "trigger_keywords": ['site assessment', 'assessment', 'book assessment', 'site inspection'],
    "is_active": True,
    "steps": [
        {
            "name": "check_whatsapp_flow",
            "is_entry_point": True,
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "query_model", "app_label": "flows", "model_name": "WhatsAppFlow", "variable_name": "site_inspection_whatsapp_flow", "filters_template": {"name": "site_inspection_whatsapp", "sync_status": "published"}, "fields_to_return": ["flow_id", "friendly_name"], "limit": 1}]},
            "transitions": [
                {"to_step": "send_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "site_inspection_whatsapp_flow.0"}},
                {"to_step": "fallback_to_legacy", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_whatsapp_flow",
            "type": "send_message",
            "config": {"message_type": "interactive", "interactive": {"type": "flow", "body": {"text": "Please complete our site assessment request form to get started."}, "action": {"name": "flow", "parameters": {"flow_message_version": "3", "flow_token": "{{ contact.id }}-site-inspection-{{ now().timestamp() }}", "flow_id": "{{ site_inspection_whatsapp_flow.0.flow_id }}", "flow_cta": "Start Request", "flow_action": "navigate", "flow_action_payload": {"screen": "WELCOME"}}}}},
            "transitions": [
                {"to_step": "wait_for_whatsapp_response", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "wait_for_whatsapp_response",
            "type": "action",
            "config": {
                "actions_to_run": [],
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please complete the WhatsApp form. We will continue once your submission is received."
                    }
                }
            },
            "transitions": [
                {"to_step": "collect_location_pin", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "collect_location_pin",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_contact_context_variable", "variable_name": "awaiting_location_for_assessment", "value_template": "pending"}
                ],
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please send your site location pin using WhatsApp's location feature. This helps our team find your site easily."}
                }
            },
            "transitions": [
                {"to_step": "generate_assessment_id", "condition_config": {"type": "location_pin_received"}}
            ]
        },
        {
            "name": "fallback_to_legacy",
            "type": "send_message",
            "config": {"message_type": "text", "text": {"body": "Sorry, the interactive form is currently unavailable. We'll collect details here instead."}},
            "transitions": [{"to_step": "start_assessment_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "start_assessment_request",
            "type": "question",
            "config": {"message_config": {"message_type": "text", "text": {"body": "You've requested a site assessment. Let's get a few details.\n\nWhat is your *full name*?"}}, "reply_config": {"expected_type": "text", "save_to_variable": "assessment_full_name"}},
            "transitions": [{"to_step": "ask_assessment_type", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_full_name"}}]
        },
        {
            "name": "ask_assessment_type",
            "type": "question",
            "config": {"message_config": {"message_type": "text", "text": {"body": "What is the *assessment type*? Reply with one: starlink, commercial_solar, hybrid_starlink_solar, custom_furniture."}}, "reply_config": {"expected_type": "text", "save_to_variable": "assessment_type"}},
            "transitions": [{"to_step": "ask_assessment_day", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_type"}}]
        },
        {
            "name": "ask_assessment_day",
            "type": "question",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you, {{ assessment_full_name }}. What is your *preferred day* for the assessment?"}}, "reply_config": {"expected_type": "text", "save_to_variable": "assessment_preferred_day"}},
            "transitions": [{"to_step": "ask_assessment_company", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_preferred_day"}}]
        },
        {
            "name": "ask_assessment_company",
            "type": "question",
            "config": {"message_config": {"message_type": "text", "text": {"body": "What is your *company name*? (If not applicable, please type 'N/A')"}}, "reply_config": {"expected_type": "text", "save_to_variable": "assessment_company_name"}},
            "transitions": [{"to_step": "ask_assessment_address", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_company_name"}}]
        },
        {
            "name": "ask_assessment_address",
            "type": "question",
            "config": {"message_config": {"message_type": "text", "text": {"body": "What is the *full address* for the site assessment?"}}, "reply_config": {"expected_type": "text", "save_to_variable": "assessment_address"}},
            "transitions": [{"to_step": "ask_assessment_contact", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_address"}}]
        },
        {
            "name": "ask_assessment_contact",
            "type": "question",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Finally, what is the best *contact number* for our team to use?"}}, "reply_config": {"expected_type": "text", "save_to_variable": "assessment_contact_info"}},
            "transitions": [{"to_step": "generate_assessment_id", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_contact_info"}}]
        },
        {
            "name": "generate_assessment_id",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "generate_unique_assessment_id", "params_template": {"save_to_variable": "generated_assessment_id_raw"}}]},
            "transitions": [{"to_step": "prefix_assessment_id", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "prefix_assessment_id",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "generated_assessment_id", "value_template": "SA-{{ generated_assessment_id_raw }}"}]},
            "transitions": [{"to_step": "save_assessment_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "save_assessment_request",
            "type": "action",
            "config": {"actions_to_run": [
                {"action_type": "create_model_instance", "app_label": "customer_data", "model_name": "SiteAssessmentRequest", "fields_template": {"customer": "current", "assessment_id": "{{ generated_assessment_id }}", "full_name": "{{ assessment_full_name }}", "company_name": "{{ assessment_company_name }}", "address": "{{ assessment_address }}", "contact_info": "{{ assessment_contact_info }}", "preferred_day": "{{ assessment_preferred_day }}", "assessment_type": "{{ assessment_type }}"}, "save_to_variable": "created_assessment_request"},
                {"action_type": "send_group_notification", "params_template": {"group_names": ["Technical Admin", "Sales Team"], "template_name": "hanna_new_site_assessment_request"}}
            ]},
            "transitions": [{"to_step": "end_flow_assessment_success", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_assessment_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you! Your site assessment request (#{{ generated_assessment_id }}) for *{{ assessment_type }}* has been submitted. Our team will contact you shortly to confirm the schedule."}}},
            "transitions": []
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you! Please complete the form to submit your site assessment request. Our team will contact you shortly to confirm the schedule."}}}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Your request has been cancelled. Type 'menu' to start over."}}}
        }
    ]
}
