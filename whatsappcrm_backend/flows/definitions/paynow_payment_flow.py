PAYNOW_PAYMENT_FLOW = {
    "name": "ecocash_payment_flow",
    "friendly_name": "EcoCash Payment",
    "description": "Booking payment flow for EcoCash.",
    "trigger_keywords": ["ecocash payment", "mobile money payment"],
    "is_active": True,
    "steps": [
        {
            "name": "start_payment",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_target", "value_template": "{{ payment_target if payment_target else 'booking' }}"}
                ]
            },
            "transitions": [
                {"to_step": "unsupported_inquiry_payment", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "payment_target", "value": "inquiry"}},
                {"to_step": "welcome_message", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "unsupported_inquiry_payment",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Inquiry payments are not enabled yet for EcoCash. Please contact our team and we will send you the correct payment instructions manually."}
                }
            }
        },
        {
            "name": "welcome_message",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "Welcome to EcoCash Payment!\n\nYou can pay your booking using EcoCash.\n\nPlease enter your booking reference to continue."
                }
            },
            "transitions": [{"to_step": "ask_booking_reference", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_booking_reference",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please enter your booking reference number."}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "booking_reference"}
            },
            "transitions": [{"to_step": "find_booking_by_reference", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "find_booking_by_reference",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "variable_name": "found_booking",
                    "filters_template": {"booking_reference__iexact": "{{ booking_reference }}"},
                    "fields_to_return": ["id", "booking_reference", "tour_name", "total_amount", "amount_paid"]
                }]
            },
            "transitions": [
                {"to_step": "prepare_booking_payment_details", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_booking.0"}},
                {"to_step": "handle_booking_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_booking_not_found",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "❌ We could not find a booking with reference *{{ booking_reference }}*. Please check the reference and try again."}
                }
            }
        },
        {
            "name": "prepare_booking_payment_details",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "balance_due", "value_template": "{{ found_booking.0.total_amount|float - found_booking.0.amount_paid|float }}"}
                ]
            },
            "transitions": [{"to_step": "ask_payment_amount", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_payment_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "✅ Booking found: *{{ found_booking.0.booking_reference }}*\nTour: {{ found_booking.0.tour_name }}\nBalance Due: *${{ '%.2f'|format(balance_due|float) }}*\n\nHow much would you like to pay?"
                    }
                },
                "reply_config": {
                    "expected_type": "number",
                    "save_to_variable": "payment_amount",
                    "validation_regex": "^[0-9]+(\\.[0-9]{1,2})?$"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid amount, for example 150 or 150.00."
                }
            },
            "transitions": [{"to_step": "ask_payment_method", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_payment_method",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Choose EcoCash Number"},
                        "body": {"text": "Select EcoCash to pay *${{ '%.2f'|format(payment_amount|float) }}*."},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "ecocash", "title": "💵 EcoCash"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_method"}
            },
            "transitions": [{"to_step": "ask_payment_phone", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_payment_phone",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Enter the mobile number to charge in the format *2637XXXXXXXX*."}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "payment_phone", "validation_regex": "^2637[0-9]{8}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid Zimbabwe mobile number starting with 2637."}
            },
            "transitions": [{"to_step": "ask_payment_email", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_payment_email",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Enter your email address for the payment receipt."}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "payment_email", "validation_regex": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid email address."}
            },
            "transitions": [
                {"to_step": "initiate_cbz_payment_api", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "initiate_cbz_payment_api",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "initiate_cbz_ecocash_payment",
                    "params_template": {
                        "booking_reference": "{{ found_booking.0.booking_reference }}",
                        "amount": "{{ payment_amount }}",
                        "currency": "USD",
                        "msisdn": "{{ payment_phone }}"
                    }
                }]
            },
            "transitions": [
                {"to_step": "cbz_payment_success_message", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "cbz_payment_status", "value": "approved"}},
                {"to_step": "cbz_payment_pending_message", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "cbz_payment_status", "value": "pending"}},
                {"to_step": "cbz_payment_failed_message", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "cbz_payment_success_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "🎉 Payment confirmed successfully!\n\n*Booking Reference:* #{{ found_booking.0.booking_reference }}\n*Amount:* ${{ '%.2f'|format(payment_amount|float) }}\n*Payment Method:* EcoCash\n*Payment Ref:* {{ cbz_payment_reference }}"}
                }
            }
        },
        {
            "name": "cbz_payment_pending_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "⏳ Payment initiated.\n\n*Booking Reference:* #{{ found_booking.0.booking_reference }}\n*Amount:* ${{ '%.2f'|format(payment_amount|float) }}\n*Payment Method:* EcoCash\n*Payment Ref:* {{ cbz_payment_reference }}\n\nPlease complete the EcoCash prompt sent to *{{ payment_phone }}*."}
                }
            }
        },
        {
            "name": "cbz_payment_failed_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "⚠️ EcoCash payment could not be completed.\n\n*Booking Reference:* #{{ found_booking.0.booking_reference }}\n*Reason:* {{ cbz_payment_error_message or 'Payment was not approved.' }}{% if cbz_payment_result_code %}\n*Error Code:* {{ cbz_payment_result_code }}{% endif %}"}
                }
            }
        }
    ]
}