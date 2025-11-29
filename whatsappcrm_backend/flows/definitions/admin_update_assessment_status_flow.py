# whatsappcrm_backend/flows/definitions/admin_update_assessment_status_flow.py

ADMIN_UPDATE_ASSESSMENT_STATUS_FLOW = {
    "name": "admin_update_assessment_status",
    "friendly_name": "Admin: Update Assessment Status",
    "description": "An internal flow for admins to change the status of an existing site assessment.",
    "trigger_keywords": ["update assessment", "assessment status"],
    "is_active": True,
    "steps": [
        {
            "name": "start_update_assessment",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Let's update a site assessment status. Please enter the Assessment ID (e.g., SA-123456)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "target_assessment_id"}
            },
            "transitions": [{"to_step": "find_assessment", "condition_config": {"type": "variable_exists", "variable_name": "target_assessment_id"}}]
        },
        {
            "name": "find_assessment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "SiteAssessmentRequest",
                    "variable_name": "found_assessment",
                    "filters_template": {"assessment_id__iexact": "{{ target_assessment_id }}"},
                    "fields_to_return": ["id", "assessment_id", "full_name", "status", "customer_id"],
                    "limit": 1
                }]
            },
            "transitions": [{"to_step": "check_if_assessment_exists", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_if_assessment_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "get_customer_contact", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_assessment.0"}},
                {"to_step": "handle_assessment_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "get_customer_contact",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "conversations",
                    "model_name": "Contact",
                    "variable_name": "assessment_contact",
                    "filters_template": {"id": "{{ found_assessment.0.customer_id }}"},
                    "fields_to_return": ["id", "whatsapp_id"],
                    "limit": 1
                }]
            },
            "transitions": [{"to_step": "ask_for_new_status", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_for_new_status",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Update Assessment Status"},
                        "body": {"text": "Found Assessment: *{{ found_assessment.0.assessment_id }}* for *{{ found_assessment.0.full_name }}*\nCurrent Status: *{{ found_assessment.0.status|title }}*\n\nPlease select the new status:"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "scheduled", "title": "🗓️ Mark as Scheduled"}},
                                {"type": "reply", "reply": {"id": "assessed", "title": "✅ Mark as Assessed"}},
                                {"type": "reply", "reply": {"id": "cancelled", "title": "❌ Mark as Cancelled"}},
                                {"type": "reply", "reply": {"id": "cancel_update", "title": "Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "new_assessment_status"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_update"}},
                {"to_step": "update_assessment_status", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "update_assessment_status",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_model_instance",
                        "app_label": "customer_data",
                        "model_name": "SiteAssessmentRequest",
                        "instance_id_template": "{{ found_assessment.0.id }}",
                        "fields_to_update_template": {"status": "{{ new_assessment_status }}"}
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "template_name": "hanna_assessment_status_updated",
                            "contact_ids": ["{{ assessment_contact.0.id }}"],
                            "template_context": {
                                "assessment_id": "{{ found_assessment.0.assessment_id }}",
                                "new_status": "{{ new_assessment_status|title }}"
                            }
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "handle_assessment_not_found",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Sorry, I couldn't find a site assessment with the ID '{{ target_assessment_id }}'. Please check the ID and try again."}}}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Assessment update cancelled."}}}
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Success! The status for assessment '{{ found_assessment.0.assessment_id }}' has been updated to *{{ new_assessment_status|title }}*.\n\nThe customer has been notified."}
                }
            }
        }
    ]
}