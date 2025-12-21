# whatsappcrm_backend/flows/definitions/omari_payment_flow.py

OMARI_PAYMENT_FLOW = {
    "name": "omari_payment_flow",
    "friendly_name": "Omari Mobile Payment",
    "description": "Automated mobile payment flow using Omari API with OTP verification for existing bookings.",
    "trigger_keywords": ["pay", "payment", "make payment", "omari payment"],
    "is_active": True,
    "steps": [
        {
            "name": "start_payment",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [
                    # Check if booking_reference was passed from another flow
                    {"action_type": "set_context_variable", "variable_name": "has_booking_ref", "value_template": "{% if booking_reference %}true{% else %}false{% endif %}"}
                ]
            },
            "transitions": [
                {"to_step": "find_booking", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "has_booking_ref", "value": "true"}},
                {"to_step": "welcome_message", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "welcome_message",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "Welcome to Omari Mobile Payment! 💳\n\nYou can pay for your booking using:\n• Ecocash\n• OneMoney\n• ZimSwitch\n\nTo get started, I'll need your booking reference number."
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
                    "text": {"body": "Please enter your Booking Reference number (e.g., BK-T001-20251225)."}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "booking_reference"}
            },
            "transitions": [{"to_step": "find_booking", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "find_booking",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "variable_name": "found_booking",
                    "filters_template": {"booking_reference__iexact": "{{ booking_reference }}"},
                    "fields_to_return": ["id", "booking_reference", "tour_name", "total_amount", "amount_paid", "customer_name", "customer_email"]
                }]
            },
            "transitions": [
                {"to_step": "display_booking_and_ask_amount", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_booking.0"}},
                {"to_step": "handle_booking_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_booking_not_found",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "❌ Sorry, I couldn't find a booking with reference *{{ booking_reference }}*.\n\nPlease check the number and try again, or type *menu* to return to the main menu."
                }
            },
            "transitions": [{"to_step": "end_payment_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "display_booking_and_ask_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": """✅ Found Booking: *{{ found_booking.0.booking_reference }}*
Tour: *{{ found_booking.0.tour_name }}*

💰 Total Amount: ${{ "%.2f"|format(found_booking.0.total_amount|float) }}
💵 Amount Paid: ${{ "%.2f"|format(found_booking.0.amount_paid|float) }}
📊 *Balance Due: ${{ "%.2f"|format(found_booking.0.total_amount|float - found_booking.0.amount_paid|float) }}*

How much would you like to pay?"""
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
                    "re_prompt_message_text": "Please enter a valid amount (e.g., 50 or 50.00)."
                }
            },
            "transitions": [{"to_step": "ask_payment_channel", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_payment_channel",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Select Payment Channel"},
                        "body": {
                            "text": "You are paying *${{ '%.2f'|format(payment_amount|float) }}*.\n\nPlease select your mobile money provider:"
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "ecocash", "title": "Ecocash"}},
                                {"type": "reply", "reply": {"id": "onemoney", "title": "OneMoney"}},
                                {"type": "reply", "reply": {"id": "zipit", "title": "ZimSwitch"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_channel"}
            },
            "transitions": [{"to_step": "ask_phone_number", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_phone_number",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please enter your mobile number in the format *2637XXXXXXXX* (the number registered with your mobile money account)."
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "payment_phone",
                    "validation_regex": "^2637[0-9]{8}$"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid Zimbabwe mobile number starting with 2637 (e.g., 263771234567)."
                }
            },
            "transitions": [{"to_step": "initiate_payment", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "initiate_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "initiate_omari_payment",
                    "booking_reference": "{{ booking_reference }}",
                    "amount": "{{ payment_amount }}",
                    "currency": "USD",
                    "channel": "{{ payment_channel|upper }}",
                    "msisdn": "{{ payment_phone }}"
                }]
            },
            "transitions": [
                {"to_step": "payment_initiated_success", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "omari_otp_reference"}},
                {"to_step": "payment_initiation_failed", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "payment_initiated_success",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": """✅ Payment initiated successfully!

📱 An OTP (One-Time Password) has been sent to *{{ payment_phone }}* via SMS.

Please enter the OTP code to complete your payment:

💡 Tip: The OTP is usually 4-6 digits.
⚠️ Type *cancel* to abort this payment."""
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "otp_input"
                }
            },
            "transitions": [
                {"to_step": "cancel_payment", "priority": 1, "condition_config": {"type": "text_contains_any", "values": ["cancel", "stop", "quit", "abort"]}},
                {"to_step": "process_otp", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "process_otp",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "process_otp",
                    "otp": "{{ otp_input }}"
                }]
            },
            "transitions": [
                {"to_step": "payment_success", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "omari_payment_success"}},
                {"to_step": "payment_failed", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "payment_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": """🎉 *Payment Successful!*

Amount Paid: *${{ '%.2f'|format(payment_amount|float) }}*
Booking Ref: *{{ booking_reference }}*
Payment Ref: *{{ omari_payment_reference }}*

✅ Your booking has been updated automatically.

Thank you for choosing Kalai Safaris! We look forward to your adventure.

Type *menu* to return to the main menu or *my bookings* to view your bookings."""
                    }
                }
            }
        },
        {
            "name": "payment_failed",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": """❌ Payment failed.

{{ omari_error_message if omari_error_message else 'The OTP you entered may be incorrect or expired.' }}

Please try again by typing *pay* or contact support if the problem persists.

Type *menu* to return to the main menu."""
                }
            },
            "transitions": [{"to_step": "end_payment_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "payment_initiation_failed",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": """❌ Failed to initiate payment.

{{ omari_error_message if omari_error_message else 'There was a problem connecting to the payment service.' }}

Please try again later or contact support.

Type *menu* to return to the main menu."""
                }
            },
            "transitions": [{"to_step": "end_payment_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "cancel_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "cancel_payment"
                }]
            },
            "transitions": [{"to_step": "payment_cancelled", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "payment_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Payment cancelled. Type *pay* to start a new payment or *menu* to return to the main menu."
                    }
                }
            }
        },
        {
            "name": "end_payment_flow",
            "type": "end_flow"
        }
    ]
}
