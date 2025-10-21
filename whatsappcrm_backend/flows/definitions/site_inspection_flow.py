# whatsappcrm_backend/flows/definitions/site_inspection_flow.py

SITE_INSPECTION_FLOW = {
    "name": "site_inspection_request",
    "friendly_name": "Site Assessment Request",
    "description": "Guides a user through booking a site assessment for a solar installation.",
    "trigger_keywords": ['site assessment', 'assessment', 'book assessment', 'site inspection'],
    "is_active": True,
    "steps": [
        {
            "name": "start_assessment_request",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "You've requested a site assessment. Let's get a few details to schedule your visit.\n\nWhat is your *full name*?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_full_name"}
            },
            "transitions": [{"to_step": "ask_assessment_day", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_full_name"}}]
        },
        {
            "name": "ask_assessment_day",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you, {{ assessment_full_name }}. What is your *preferred day* for the assessment?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_preferred_day"}
            },
            "transitions": [{"to_step": "ask_assessment_company", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_preferred_day"}}]
        },
        {
            "name": "ask_assessment_company",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your *company name*? (If not applicable, please type 'N/A')"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_company_name"}
            },
            "transitions": [{"to_step": "ask_assessment_address", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_company_name"}}]
        },
        {
            "name": "ask_assessment_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the *full address* for the site assessment?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_address"}
            },
            "transitions": [{"to_step": "ask_assessment_contact", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_address"}}]
        },
        {
            "name": "ask_assessment_contact",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Finally, what is the best *contact number* for our team to use?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_contact_info"}
            },
            "transitions": [{"to_step": "generate_assessment_id", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "assessment_contact_info"}}]
        },
        {
            "name": "generate_assessment_id",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "generate_unique_assessment_id", "params_template": {"save_to_variable": "generated_assessment_id_raw"}}]
            },
            "transitions": [{"to_step": "prefix_assessment_id", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "prefix_assessment_id",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "generated_assessment_id", "value_template": "SA-{{ generated_assessment_id_raw }}"}]
            },
            "transitions": [{"to_step": "save_assessment_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "save_assessment_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "SiteAssessmentRequest",
                        "fields_template": {
                            "customer": "current", "assessment_id": "{{ generated_assessment_id }}", "full_name": "{{ assessment_full_name }}",
                            "company_name": "{{ assessment_company_name }}", "address": "{{ assessment_address }}",
                            "contact_info": "{{ assessment_contact_info }}", "preferred_day": "{{ assessment_preferred_day }}"
                        },
                        "save_to_variable": "created_assessment_request"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Technical Admin", "Sales Team"],
                            "template_name": "new_site_assessment_request"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow_assessment_success", "priority": 0, "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_assessment_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you! Your site assessment request (#{{ generated_assessment_id }}) has been submitted. Our team will contact you shortly to confirm the schedule."}}},
            "transitions": []
        }
    ]
}