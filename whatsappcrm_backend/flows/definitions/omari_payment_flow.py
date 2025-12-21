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
                    {"action_type": "set_context_variable", "variable_name": "has_booking_ref", "value_template": "{% if booking_reference %}true{% else %}false{% endif %}"},
                    {"action_type": "set_context_variable", "variable_name": "has_inquiry_ref", "value_template": "{% if inquiry_reference %}true{% else %}false{% endif %}"},
                    {"action_type": "set_context_variable", "variable_name": "has_payment_target", "value_template": "{% if payment_target %}true{% else %}false{% endif %}"},
                    {"action_type": "set_context_variable", "variable_name": "booking_path_ready", "value_template": "{{ 'true' if payment_target == 'booking' and booking_reference else 'false' }}"},
                    {"action_type": "set_context_variable", "variable_name": "inquiry_path_ready", "value_template": "{{ 'true' if payment_target == 'inquiry' and inquiry_reference else 'false' }}"},
                    # Get current contact phone
                    {"action_type": "set_context_variable", "variable_name": "current_phone", "value_template": "{{ contact.phone_number }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_month", "value_template": "{{ now().strftime('%Y-%m') }}"}
                ]
            },
            "transitions": [
                {"to_step": "find_booking", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "booking_path_ready", "value": "true"}},
                {"to_step": "welcome_message", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "payment_target", "value": "booking"}},
                {"to_step": "find_inquiry", "priority": 2, "condition_config": {"type": "variable_equals", "variable_name": "inquiry_path_ready", "value": "true"}},
                {"to_step": "ask_inquiry_reference", "priority": 3, "condition_config": {"type": "variable_equals", "variable_name": "payment_target", "value": "inquiry"}},
                {"to_step": "ask_payment_target", "priority": 4, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_payment_target",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Choose Payment"},
                        "body": {"text": "Are you paying for a booking or a tour inquiry?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "booking", "title": "Booking Installment"}},
                                {"type": "reply", "reply": {"id": "inquiry", "title": "Tour Inquiry"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_target"}
            },
            "transitions": [
                {"to_step": "welcome_message", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "booking"}},
                {"to_step": "ask_inquiry_reference", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "inquiry"}}
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
            "name": "ask_inquiry_reference",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please enter your Tour Inquiry reference (e.g., IQ-2025-001)."}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_reference"}
            },
            "transitions": [{"to_step": "find_inquiry", "condition_config": {"type": "always_true"}}]
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
                {"to_step": "prepare_booking_payment_details", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_booking.0"}},
                {"to_step": "handle_booking_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "prepare_booking_payment_details",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "balance_due", "value_template": "{{ found_booking.0.total_amount|float - found_booking.0.amount_paid|float }}"},
                    {"action_type": "set_context_variable", "variable_name": "deposit_target", "value_template": "{{ found_booking.0.total_amount|float * 0.5 }}"},
                    {"action_type": "set_context_variable", "variable_name": "deposit_remaining", "value_template": "{{ (found_booking.0.total_amount|float * 0.5) - found_booking.0.amount_paid|float if (found_booking.0.total_amount|float * 0.5) - found_booking.0.amount_paid|float > 0 else 0 }}"},
                    {"action_type": "set_context_variable", "variable_name": "minimum_installment", "value_template": "{{ (found_booking.0.total_amount|float * 0.5) - found_booking.0.amount_paid|float if (found_booking.0.total_amount|float * 0.5) - found_booking.0.amount_paid|float > 0 else (balance_due if balance_due|float < 10 else 10) }}"},
                    {"action_type": "set_context_variable", "variable_name": "deposit_required", "value_template": "{{ 'true' if ((found_booking.0.total_amount|float * 0.5) - found_booking.0.amount_paid|float) > 0 else 'false' }}"}
                ]
            },
            "transitions": [{"to_step": "display_booking_and_ask_amount", "condition_config": {"type": "always_true"}}]
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
            "name": "find_inquiry",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "TourInquiry",
                    "variable_name": "found_inquiry",
                    "filters_template": {"inquiry_reference__iexact": "{{ inquiry_reference }}"},
                    "fields_to_return": ["id", "inquiry_reference", "destinations", "status", "preferred_dates", "number_of_travelers"]
                }]
            },
            "transitions": [
                {"to_step": "display_inquiry_and_ask_amount", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_inquiry.0"}},
                {"to_step": "handle_inquiry_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_inquiry_not_found",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "❌ Sorry, we couldn't find a tour inquiry with reference *{{ inquiry_reference }}*. Please confirm the reference or type *menu* to return."}
            },
            "transitions": [{"to_step": "end_payment_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "display_inquiry_and_ask_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "✅ Inquiry: *{{ found_inquiry.0.inquiry_reference }}*\nDestination: {{ found_inquiry.0.destinations or 'Your custom tour' }}\nStatus: {{ found_inquiry.0.status|upper }}\nTravelers: {{ found_inquiry.0.number_of_travelers or 'n/a' }}\n\nEnter the amount you want to pay (recommended 50% deposit if a quote was shared)."
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
                    "re_prompt_message_text": "Please enter a valid amount (e.g., 120 or 120.50)."
                }
            },
            "transitions": [{"to_step": "ask_payment_channel", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "display_booking_and_ask_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Booking Payment"},
                        "body": {
                            "text": "✅ *{{ found_booking.0.booking_reference }}* — {{ found_booking.0.tour_name }}\n\n💰 Total: ${{ '%.2f'|format(found_booking.0.total_amount|float) }}\n💵 Paid: ${{ '%.2f'|format(found_booking.0.amount_paid|float) }}\n📊 Balance: ${{ '%.2f'|format(balance_due|float) }}\n\nChoose how you want to pay."
                        },
                        "action": {
                            "button": "Payment Plan",
                            "sections": [
                                {
                                    "title": "Recommended",
                                    "rows": [
                                        {"id": "pay_deposit", "title": "Pay 50% Deposit", "description": "{{ 'Deposit required' if deposit_required == 'true' else 'Deposit already covered' }}"},
                                        {"id": "pay_full_balance", "title": "Pay Full Balance", "description": "Settle ${{ '%.2f'|format(balance_due|float) }} now."}
                                    ]
                                },
                                {
                                    "title": "Installments",
                                    "rows": [
                                        {"id": "pay_installment", "title": "Custom Installment", "description": "Min: ${{ '%.2f'|format(minimum_installment|float) }} | Max: ${{ '%.2f'|format(balance_due|float) }}"}
                                    ]
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_plan_choice"}
            },
            "transitions": [
                {"to_step": "set_deposit_payment_amount", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_deposit"}},
                {"to_step": "set_full_balance_amount", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_full_balance"}},
                {"to_step": "ask_installment_amount", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_installment"}}
            ]
        },
        {
            "name": "set_deposit_payment_amount",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_amount", "value_template": "{{ deposit_remaining if deposit_remaining|float > 0 else balance_due }}"},
                    {"action_type": "set_context_variable", "variable_name": "payment_mode", "value_template": "deposit"}
                ]
            },
            "transitions": [
                {"to_step": "deposit_not_required", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "deposit_required", "value": "false"}},
                {"to_step": "ask_payment_channel", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "deposit_not_required",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "You've already covered the 50% deposit. Choose an installment or pay the remaining balance instead."
                }
            },
            "transitions": [{"to_step": "display_booking_and_ask_amount", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_full_balance_amount",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_amount", "value_template": "{{ balance_due }}"},
                    {"action_type": "set_context_variable", "variable_name": "payment_mode", "value_template": "full"}
                ]
            },
            "transitions": [{"to_step": "ask_payment_channel", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_installment_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Enter your installment amount.\n\nMinimum: ${{ '%.2f'|format(minimum_installment|float) }}{{ ' (50% deposit still required)' if deposit_required == 'true' else '' }}\nMaximum: ${{ '%.2f'|format(balance_due|float) }}"
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
                    "re_prompt_message_text": "Please enter a valid amount (e.g., 150 or 150.50)."
                }
            },
            "transitions": [{"to_step": "validate_installment_amount", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "validate_installment_amount",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "is_amount_too_low", "value_template": "{{ 'true' if payment_amount|float < minimum_installment|float else 'false' }}"},
                    {"action_type": "set_context_variable", "variable_name": "is_amount_too_high", "value_template": "{{ 'true' if payment_amount|float > balance_due|float else 'false' }}"}
                ]
            },
            "transitions": [
                {"to_step": "amount_too_low", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "is_amount_too_low", "value": "true"}},
                {"to_step": "amount_too_high", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "is_amount_too_high", "value": "true"}},
                {"to_step": "ask_installment_month", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "amount_too_low",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "Please pay at least ${{ '%.2f'|format(minimum_installment|float) }}. This covers the 50% deposit before installments."
                }
            },
            "transitions": [{"to_step": "ask_installment_amount", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "amount_too_high",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "Please enter an amount up to the balance of ${{ '%.2f'|format(balance_due|float) }}."
                }
            },
            "transitions": [{"to_step": "ask_installment_amount", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_installment_month",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Which month should this installment be applied to?\n\nEnter in the format YYYY-MM (e.g., 2025-02). You cannot select the current month ({{ current_month }})."
                    }
                },
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "installment_month",
                    "validation_regex": "^\\d{4}-\\d{2}$"
                },
                "fallback_config": {
                    "action": "re_prompt",
                    "max_retries": 2,
                    "re_prompt_message_text": "Please use YYYY-MM format (e.g., 2025-02)."
                }
            },
            "transitions": [{"to_step": "check_installment_month", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_installment_month",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "installment_is_current_month", "value_template": "{{ 'true' if installment_month == current_month else 'false' }}"}
                ]
            },
            "transitions": [
                {"to_step": "installment_month_invalid", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "installment_is_current_month", "value": "true"}},
                {"to_step": "ask_payment_channel", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "installment_month_invalid",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "Installments cannot be applied to the current month. Please choose a future month."}
            },
            "transitions": [{"to_step": "ask_installment_month", "condition_config": {"type": "always_true"}}]
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
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Mobile Money Account"},
                        "body": {
                            "text": "Would you like to use the number you're contacting us with (*{{ current_phone }}*) or a different number for the payment?"
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "use_current", "title": "✅ Use Current Number"}},
                                {"type": "reply", "reply": {"id": "use_different", "title": "🔄 Use Different Number"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "phone_choice"}
            },
            "transitions": [
                {"to_step": "set_current_phone", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "use_current"}},
                {"to_step": "ask_alternative_phone", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "use_different"}}
            ]
        },
        {
            "name": "set_current_phone",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_phone", "value_template": "{{ current_phone }}"}
                ]
            },
            "transitions": [{"to_step": "route_payment_by_target", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_alternative_phone",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please enter your mobile money account number in the format *2637XXXXXXXX* (the number registered with your Ecocash, OneMoney, or ZimSwitch account)."
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
            "transitions": [{"to_step": "route_payment_by_target", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "route_payment_by_target",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "is_inquiry_payment", "value_template": "{{ 'true' if payment_target == 'inquiry' else 'false' }}"}
                ]
            },
            "transitions": [
                {"to_step": "inquiry_payment_not_supported", "priority": 0, "condition_config": {"type": "variable_equals", "variable_name": "is_inquiry_payment", "value": "true"}},
                {"to_step": "initiate_payment", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "inquiry_payment_not_supported",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "Thanks! To process payments we need to convert your inquiry into a booking. A consultant will finalize your itinerary and send a payment link shortly."
                }
            },
            "transitions": [{"to_step": "end_payment_flow", "condition_config": {"type": "always_true"}}]
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
Installment Month: *{{ installment_month if installment_month else 'N/A' }}*

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
