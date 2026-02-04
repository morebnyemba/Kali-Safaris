# whatsappcrm_backend/flows/definitions/manual_payment_flow.py

MANUAL_PAYMENT_FLOW = {
    "name": "manual_payment_flow",
    "friendly_name": "Record Manual Payment",
    "description": "Allows a user to record a manual payment (e.g., bank transfer, Omari) for an existing booking.",
    "trigger_keywords": ["manual payment", "record payment", "paid"],
    "is_active": True,
    "steps": [
        {
            "name": "start_manual_payment",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "💰 *Record Your Payment*\n\nTo help me find your booking, please enter your Booking Reference number.\n\n📝 Example: BK-SLYKER-TECH-20251023\n\n(Type *menu* to cancel)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "booking_reference_input"}
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
                    "filters_template": {"booking_reference__iexact": "{{ booking_reference_input }}"},
                    "fields_to_return": ["id", "booking_reference", "tour_name", "total_amount", "amount_paid", "start_date"]
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
                "text": {"body": "❌ *Booking Not Found*\n\nI couldn't find a booking with reference: *{{ booking_reference_input }}*\n\n💡 *Tips:*\n• Check the reference number for typos\n• Make sure you have the complete reference\n• Reference format: BK-XXX-XXX-XXXXXXXX\n\n🔄 Type *manual payment* to try again\n📱 Type *menu* to return to main menu"}
            },
            "transitions": [{"to_step": "end_manual_payment", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "display_booking_and_ask_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": """✅ *Booking Found!*

📋 *Booking Details*
Reference: #{{ found_booking.0.booking_reference }}
Tour: *{{ found_booking.0.tour_name }}*
{% if found_booking.0.start_date %}Date: {{ found_booking.0.start_date|date:'F d, Y' }}{% endif %}

💰 *Payment Status*
Total Cost: ${{ "%.2f"|format(found_booking.0.total_amount|float) }}
Already Paid: ${{ "%.2f"|format(found_booking.0.amount_paid|float) }}
━━━━━━━━━━━━━━━━
*Balance Due: ${{ "%.2f"|format(found_booking.0.total_amount|float - found_booking.0.amount_paid|float) }}*

How much did you pay?
(Enter amount in dollars, e.g., 500)"""
                    }
                },
                "reply_config": {"expected_type": "number", "save_to_variable": "payment_amount"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "❌ Please enter a valid number for the amount.\n\n📝 Example: 500 or 1000.50"}
            },
            "transitions": [{"to_step": "confirm_amount", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "confirm_amount",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "💵 Confirm Payment Amount"},
                        "body": {"text": "You entered: *${{ '%.2f'|format(payment_amount|float) }}*\n\nIs this amount correct?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "amount_correct", "title": "✅ Yes, Correct"}},
                                {"type": "reply", "reply": {"id": "amount_wrong", "title": "❌ No, Re-enter"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "amount_confirmation"}
            },
            "transitions": [
                {"to_step": "ask_payment_method", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "amount_correct"}},
                {"to_step": "display_booking_and_ask_amount", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "amount_wrong"}}
            ]
        },
        {
            "name": "ask_payment_method",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "💳 Payment Method"},
                        "body": {"text": "Payment amount: *${{ '%.2f'|format(payment_amount|float) }}*\n\nWhich payment method did you use?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "bank_transfer", "title": "🏦 Bank Transfer"}},
                                {"type": "reply", "reply": {"id": "omari", "title": "📱 Omari Payment"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_method_choice"}
            },
            "transitions": [
                {"to_step": "set_method_manual", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "bank_transfer"}},
                {"to_step": "set_method_omari", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "omari"}}
            ]
        },
        {
            "name": "set_method_manual",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "payment_method_name", "value_template": "Bank Transfer"}]},
            "transitions": [{"to_step": "ask_for_pop", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_method_omari",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "payment_method_name", "value_template": "Omari"}]},
            "transitions": [{"to_step": "ask_for_pop", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_for_pop",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "📸 *Proof of Payment*\n\nPlease upload a clear screenshot or photo of your payment confirmation.\n\n💡 *Tips for a good photo:*\n• Transaction reference visible\n• Amount clearly shown\n• Date of payment visible\n• Good lighting, not blurry"}},
                "reply_config": {"expected_type": "image", "save_to_variable": "pop_image_id"}
            },
            "transitions": [{"to_step": "show_payment_summary", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "show_payment_summary",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "📋 Payment Summary"},
                        "body": {"text": """Please review your payment details:

*Booking Reference:* #{{ found_booking.0.booking_reference }}
*Tour:* {{ found_booking.0.tour_name }}
*Payment Amount:* ${{ '%.2f'|format(payment_amount|float) }}
*Payment Method:* {{ payment_method_name }}
*Proof:* ✅ Uploaded

Is everything correct?"""},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "submit_payment", "title": "✅ Submit"}},
                                {"type": "reply", "reply": {"id": "cancel_payment", "title": "❌ Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "final_confirmation"}
            },
            "transitions": [
                {"to_step": "create_payment_record", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "submit_payment"}},
                {"to_step": "end_manual_payment", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_payment"}}
            ]
        },
        {
            "name": "create_payment_record",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "Payment",
                        "fields_template": {
                            "booking_id": "{{ found_booking.0.id }}",
                            "amount": "{{ payment_amount }}",
                            "status": "pending",
                            "payment_method": "{{ payment_method_name }}",
                            "notes": "Payment recorded via WhatsApp by {{ contact.name }}. Proof of payment image was uploaded by the user."
                        },
                        "save_to_variable": "created_payment"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Finance Team", "System Admins"],
                            "template_name": "manual_payment_recorded_alert"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": """✅ *Payment Recorded Successfully!*

We've received your payment submission:

💰 Amount: ${{ '%.2f'|format(payment_amount|float) }}
📋 Booking: #{{ found_booking.0.booking_reference }}
💳 Method: {{ payment_method_name }}

🔍 *What happens next?*
1. Our finance team will verify your payment
2. You'll receive a confirmation once approved
3. A receipt will be sent to you

⏱️ *Processing Time:* Usually within 24 hours

Thank you for your payment! Type *menu* to return to the main menu."""}
                }
            }
        },
        {
            "name": "end_manual_payment",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Payment recording cancelled. Type *menu* to return to the main menu or *manual payment* to try again."}
                }
            }
        }
    ]
}