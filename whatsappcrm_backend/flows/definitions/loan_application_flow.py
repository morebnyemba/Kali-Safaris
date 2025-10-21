# whatsappcrm_backend/flows/definitions/loan_application_flow.py

LOAN_APPLICATION_FLOW = {
    "name": "loan_application_flow",
    "friendly_name": "Loan Application",
    "description": "Guides a user through applying for a cash or product loan.",
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
                {"to_step": "start_loan_application", "condition_config": {"type": "always_true"}}
            ]
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
                            "template_name": "new_loan_application"
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
        }
    ]
}