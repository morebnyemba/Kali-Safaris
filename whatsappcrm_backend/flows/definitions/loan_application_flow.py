# whatsappcrm_backend/flows/definitions/loan_application_flow.py

LOAN_APPLICATION_FLOW = {
    "name": "loan_application_flow",
    "friendly_name": "Loan Application",
    "description": "Initiates the WhatsApp interactive flow for loan applications.",
    "trigger_keywords": ["loan", "apply for loan"],
    "is_active": True,
    "steps": [
        {
            "name": "ensure_customer_profile",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {}
                }]
            },
            "transitions": [
                {"to_step": "check_whatsapp_flow", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "loan_application_whatsapp_flow",
                    "filters_template": {
                        "name": "loan_application_whatsapp",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "send_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "loan_application_whatsapp_flow.0"}},
                {"to_step": "fallback_to_legacy", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_whatsapp_flow",
            "type": "send_message",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "flow",
                    "body": {
                        "text": "Please complete our loan application form to get started."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-loan-application-{{ 'now'|date:'U' }}",
                            "flow_id": "{{ loan_application_whatsapp_flow.0.flow_id }}",
                            "flow_cta": "Start Application",
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": "WELCOME"
                            }
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "wait_for_whatsapp_response", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "wait_for_whatsapp_response",
            "type": "action",
            "config": {
                "actions_to_run": [],
                "wait_for": "whatsapp_flow_response"
            },
            "transitions": [
                {"to_step": "confirm_application_details", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "fallback_to_legacy",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Sorry, the interactive form is currently unavailable. Please contact our support team to apply for a loan."}
            },
            "transitions": [{"to_step": "end_flow_cancelled", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "start_loan_application",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Loan Application"},
                        "body": {"text": "Welcome to our loan application service. Are you applying for a *Cash Loan* or a *Product Loan*?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "cash_loan", "title": "💵 Cash Loan"}},
                                {"type": "reply", "reply": {"id": "product_loan", "title": "📦 Product Loan"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "loan_type"}
            },
            "transitions": [
                {"to_step": "ask_full_name", "condition_config": {"type": "variable_exists", "variable_name": "loan_type"}}
            ]
        },
        {
            "name": "ask_full_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Let's get some personal details. What is your *full name*?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "loan_applicant_name"}
            },
            "transitions": [
                {"to_step": "ask_national_id", "condition_config": {"type": "variable_exists", "variable_name": "loan_applicant_name"}}
            ]
        },
        {
            "name": "ask_national_id",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you, {{ loan_applicant_name }}. Please enter your *National ID number*."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "loan_national_id"}
            },
            "transitions": [
                {"to_step": "ask_employment_status", "condition_config": {"type": "variable_exists", "variable_name": "loan_national_id"}}
            ]
        },
        {
            "name": "ask_employment_status",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "What is your current employment status?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "employed", "title": "Employed"}},
                                {"type": "reply", "reply": {"id": "self_employed", "title": "Self-Employed"}},
                                {"type": "reply", "reply": {"id": "unemployed", "title": "Other"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "loan_employment_status"}
            },
            "transitions": [
                {"to_step": "ask_monthly_income", "condition_config": {"type": "variable_exists", "variable_name": "loan_employment_status"}}
            ]
        },
        {
            "name": "ask_monthly_income",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your estimated *monthly income* in USD?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "loan_monthly_income"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid number for your income."}
            },
            "transitions": [
                {"to_step": "ask_loan_amount", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "loan_type", "value": "cash_loan"}},
                {"to_step": "ask_product_of_interest", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "loan_type", "value": "product_loan"}}
            ]
        },
        {
            "name": "ask_loan_amount",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "How much cash are you applying for (in USD)?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "loan_request_amount"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid number for the loan amount."}
            },
            "transitions": [
                {"to_step": "confirm_application_details", "condition_config": {"type": "variable_exists", "variable_name": "loan_request_amount"}}
            ]
        },
        {
            "name": "ask_product_of_interest",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Which product are you interested in financing?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "loan_product_interest"}
            },
            "transitions": [
                {"to_step": "confirm_application_details", "condition_config": {"type": "variable_exists", "variable_name": "loan_product_interest"}}
            ]
        },
        {
            "name": "confirm_application_details",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Confirm Your Application"},
                        "body": {
                            "text": (
                                "Please review your application details:\n\n"
                                "*Name*: {{ loan_applicant_name }}\n"
                                "*National ID*: {{ loan_national_id or 'N/A' }}\n"
                                "*Loan Type*: {{ loan_type.replace('_', ' ')|title }}\n"
                                "*Employment*: {{ loan_employment_status.replace('_', ' ')|title }}\n"
                                "*Monthly Income*: ${{ loan_monthly_income }}\n"
                                "{% if loan_request_amount %}*Amount Requested*: ${{ loan_request_amount }}{% endif %}\n"
                                "{% if loan_product_interest %}*Product*: {{ loan_product_interest }}{% endif %}"
                            )
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_loan_app", "title": "✅ Submit Application"}},
                                {"type": "reply", "reply": {"id": "cancel_loan_app", "title": "❌ Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "loan_confirmation"}
            },
            "transitions": [
                {"to_step": "save_loan_application", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_loan_app"}},
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_loan_application",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "LoanApplication",
                        "fields_template": {
                            "customer_id": "{{ contact.customer_profile.contact_id }}",
                            "full_name": "{{ loan_applicant_name }}",
                            "national_id": "{{ loan_national_id }}",
                            "loan_type": "{{ loan_type }}",
                            "employment_status": "{{ loan_employment_status }}",
                            "monthly_income": "{{ loan_monthly_income }}",
                            "requested_amount": "{{ loan_request_amount }}",
                            "product_of_interest": "{{ loan_product_interest }}",
                            "status": "pending_review"
                        },
                        "save_to_variable": "created_loan_application"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Finance Team", "System Admins"],
                            "template_name": "hanna_new_loan_application"
                        }
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "Thank you for your application! 🙏\n\n"
                            "Your loan application has been submitted for review. "
                            "Our finance team will contact you within 24-48 hours with the next steps."
                        )
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
                    "text": {"body": "Your loan application has been cancelled. Type 'menu' to see other options."}
                }
            }
        },
        {
            "name": "end_flow_success_interactive",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! Please complete the form to submit your loan application. Our finance team will contact you within 24-48 hours with the next steps."}
                }
            }
        }
    ]
}