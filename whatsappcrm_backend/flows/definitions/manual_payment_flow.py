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
                "message_config": {"message_type": "text", "text": {"body": "To record a payment, please enter the Booking Reference number (e.g., BK-SLYKER-TECH-20251023)."}},
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
                    "fields_to_return": ["id", "booking_reference", "tour_name", "total_amount", "amount_paid"]
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
                "text": {"body": "Sorry, I couldn't find a booking with that reference. Please check the number and try again.\n\nType *menu* to exit."}
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
                        "body": """Found Booking: *#{{ found_booking.0.booking_reference }}*
Tour: *{{ found_booking.0.tour_name }}*

Total: ${{ "%.2f"|format(found_booking.0.total_amount|float) }}
Paid: ${{ "%.2f"|format(found_booking.0.amount_paid|float) }}
*Balance Due: ${{ "%.2f"|format(found_booking.0.total_amount|float - found_booking.0.amount_paid|float) }}*

How much did you pay? Please enter the amount."""
                    }
                },
                "reply_config": {"expected_type": "number", "save_to_variable": "payment_amount"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid number for the amount."}
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
                        "header": {"type": "text", "text": "Select Payment Method"},
                        "body": {"text": "You are recording a payment of *${{ '%.2f'|format(payment_amount|float) }}*.\n\nPlease select the method you used."},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "bank_transfer", "title": "Bank/Manual Transfer"}},
                                {"type": "reply", "reply": {"id": "omari", "title": "Omari Payment"}}
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
                "message_config": {"message_type": "text", "text": {"body": "Thank you. Please upload a screenshot or photo of your proof of payment."}},
                "reply_config": {"expected_type": "image", "save_to_variable": "pop_image_id"}
            },
            "transitions": [{"to_step": "create_payment_record", "condition_config": {"type": "always_true"}}]
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
                    "text": {"body": "Thank you! We have recorded your payment of *${{ '%.2f'|format(payment_amount|float) }}* for booking *#{{ found_booking.0.booking_reference }}*.\n\nOur finance team will verify it and update your booking status shortly. You will receive a confirmation and a receipt once it's approved."}
                }
            }
        },
        {
            "name": "end_manual_payment",
            "type": "end_flow"
        }
    ]
}