# whatsappcrm_backend/flows/definitions/booking_flow.py


BOOKING_FLOW = {
    "name": "booking_flow",
    "friendly_name": "Tour Booking",
    "description": "Guides a user through booking a specific tour and collecting traveler details.",
    "trigger_keywords": [], # This flow is triggered by a switch, not keywords
    "is_active": True,
    "steps": [
        # Step 1: Entry point, initialize traveler list
        {
            "name": "start_booking",
            "is_entry_point": True,
            "type": "action",
            "config": { # Ensure customer profile exists before proceeding
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "travelers_details", "value_template": []},
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "email": "{{ contact.customer_profile.email if contact.customer_profile.email else '' }}"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "ask_number_of_travelers", "condition_config": {"type": "always_true"}}]
        },
        # Step 2: Ask how many people are traveling
        {
            "name": "ask_number_of_travelers",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Great choice! You're booking the *{{ tour_name }}* tour.\n\nHow many people will be traveling in total (including yourself)?"}
                },
                "reply_config": {
                    "expected_type": "number",
                    "save_to_variable": "num_travelers",
                    "validation_regex": "^[1-9][0-9]*$"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid number (e.g., 2)."
                }
            },
            "transitions": [{"to_step": "calculate_total_cost", "condition_config": {"type": "always_true"}}]
        },
        # Step 3: Initialize the loop counter for collecting traveler details
        {
            "name": "initialize_traveler_loop",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "traveler_index", "value_template": 1}
                ]
            },
            "transitions": [
                {"to_step": "ask_traveler_name", "priority": 1, "condition_config": {"type": "variable_greater_than", "variable_name": "num_travelers", "value": "1"}},
                {"to_step": "ask_travel_dates", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "calculate_total_cost",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "total_cost", "value_template": "{{ tour_base_price * num_travelers }}"}
                ]
            },
            "transitions": [{"to_step": "initialize_traveler_loop", "condition_config": {"type": "always_true"}}]
        },
        # Step 4: Ask for the current traveler's full name
        {
            "name": "ask_traveler_name",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Let's get the details for Traveler {{ traveler_index }} of {{ num_travelers }}.\n\nWhat is their full name?"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "current_traveler_name"}
            },
            "transitions": [{"to_step": "ask_traveler_age", "condition_config": {"type": "always_true"}}]
        },
        # Step 5: Ask for the current traveler's age
        {
            "name": "ask_traveler_age",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thanks. And what is the age of *{{ current_traveler_name }}*?"}
                },
                "reply_config": {"expected_type": "number", "save_to_variable": "current_traveler_age"}
            },
            "transitions": [{"to_step": "add_traveler_to_list", "condition_config": {"type": "always_true"}}]
        },
        # Step 6: Add the collected details to the list and increment the counter
        {
            "name": "add_traveler_to_list",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "travelers_details",
                        "value_template": "{{ travelers_details + [{'name': current_traveler_name, 'age': current_traveler_age}] }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "traveler_index",
                        "value_template": "{{ traveler_index + 1 }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "ask_traveler_name", "priority": 1, "condition_config": {"type": "variable_less_than_or_equal", "variable_name": "traveler_index", "value_template": "{{ num_travelers }}"}},
                {"to_step": "ask_travel_dates", "priority": 2, "condition_config": {"type": "always_true"}} # Corrected transition
            ]
        },
        # Step 7: Ask for preferred travel dates
        {
            "name": "ask_travel_dates",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "{% if num_travelers|int > 1 %}All traveler details collected! ✅{% endif %}\n\nWhat are your preferred travel dates? (e.g., 'mid-June 2025', 'any time in September')"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "inquiry_dates"}
            },
            "transitions": [{"to_step": "ask_email", "condition_config": {"type": "always_true"}}]
        },
        # Step 8: Ask for contact email
        {
            "name": "ask_email",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Perfect. What is the best email address to send the quote and itinerary to?"}
                },
                "reply_config": {"expected_type": "email", "save_to_variable": "inquiry_email"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid email address."}
            },
            "transitions": [
                {"to_step": "update_profile_with_email", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "inquiry_email"}},
                {"to_step": "ask_payment_option", "priority": 2, "condition_config": {"type": "always_true"}} # Skip if no email provided
            ]
        },
        {
            "name": "update_profile_with_email",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {"email": "{{ inquiry_email }}"}
                }]
            },
            "transitions": [{"to_step": "ask_payment_option", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_payment_option",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Confirm & Pay"},
                        "body": {"text": "Your tour total is *${{ '%.2f'|format(total_cost|float) }}*.\n\nHow would you like to proceed?"},
                        "footer": {"text": "Select an option"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "pay_full", "title": "Pay Full Amount"}},
                                {"type": "reply", "reply": {"id": "pay_deposit", "title": "Pay 50% Deposit"}},
                                {"type": "reply", "reply": {"id": "get_quote", "title": "Just Get a Quote"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_choice"}
            },
            "transitions": [
                {"to_step": "set_payment_amount_full", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_full"}},
                {"to_step": "set_payment_amount_deposit", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_deposit"}},
                {"to_step": "create_inquiry_record_only", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "get_quote"}}
            ]
        },
        {
            "name": "set_payment_amount_full",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "amount_to_pay", "value_template": "{{ total_cost }}"}]},
            "transitions": [{"to_step": "create_booking_record", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_payment_amount_deposit",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "amount_to_pay", "value_template": "{{ total_cost|float * 0.5 }}"}]},
            "transitions": [{"to_step": "create_booking_record", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "create_booking_record",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "fields_template": {
                        "customer": "current",
                        "tour_name": "{{ tour_name }}",
                        "tour_id": "{{ tour_id }}",
                        "start_date": "1900-01-01", # Placeholder
                        "end_date": "1900-01-01", # Placeholder
                        "number_of_adults": "{{ num_travelers }}",
                        "total_amount": "{{ total_cost }}",
                        "payment_status": "pending",
                        "source": "whatsapp",
                        "notes": "Booking via WhatsApp. Dates: {{ inquiry_dates }}. Travelers: {% for p in travelers_details %}{{ p.name }} ({{ p.age }}){% if not loop.last %}, {% endif %}{% endfor %}"
                    },
                    "save_to_variable": "created_booking"
                }]
            },
            "transitions": [{"to_step": "initiate_payment", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "initiate_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "initiate_tour_payment",
                    "params_template": {
                        "booking_context_var": "created_booking",
                        "amount_to_pay_var": "amount_to_pay",
                        "save_to_variable": "payment_result"
                    }
                }]
            },
            "transitions": [
                {"to_step": "send_payment_link", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "payment_result.poll_url"}},
                {"to_step": "handle_payment_failure", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_payment_link",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! Your booking (Ref: #{{ created_booking.booking_reference }}) is confirmed.\n\nPlease use the secure link below to complete your payment of *${{ '%.2f'|format(amount_to_pay|float) }}*.\n\n{{ payment_result.poll_url }}\n\nThe link is valid for a short time. We will notify you once payment is received."}
                }
            }
        },
        {
            "name": "handle_payment_failure",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Apologies, we couldn't generate a payment link right now. Your booking (Ref: #{{ created_booking.booking_reference }}) has been saved.\n\nA consultant will contact you via WhatsApp and email (*{{ inquiry_email }}*) shortly to assist with payment."}
                }
            }
        },
        {
            "name": "create_inquiry_record_only",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "TourInquiry",
                        "fields_template": {
                            "customer": "current",
                            "destination": "{{ tour_name }}",
                            "number_of_travelers": "{{ num_travelers }}",
                            "preferred_travel_dates": "{{ inquiry_dates }}",
                            "notes": "Quote requested via WhatsApp. Travelers: {% for p in travelers_details %}{{ p.name }} ({{ p.age }}){% if not loop.last %}, {% endif %}{% endfor %}. Contact Email: {{ inquiry_email }}.",
                            "status": "new"
                        },
                        "save_to_variable": "created_inquiry"
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "group_names": ["Sales Team"], "template_name": "new_tour_inquiry_alert"
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "generate_quote_pdf", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "generate_quote_pdf",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "generate_and_save_quote_pdf",
                    "params_template": {
                        "save_to_variable": "quote_pdf_url"
                    }
                }]
            },
            "transitions": [
                {"to_step": "send_quote_pdf", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "quote_pdf_url"}},
                {"to_step": "end_quote_request_no_pdf", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_quote_pdf",
            "type": "send_message",
            "config": {
                "message_type": "document",
                "document": {
                    "link": "{{ quote_pdf_url }}",
                    "filename": "Kalai_Safaris_Quote_{{ created_inquiry.id }}.pdf",
                    "caption": "Thank you, {{ contact.name }}! Here is the preliminary quote for your *{{ tour_name }}* tour (Ref: #{{ created_inquiry.id }}).\n\nA travel specialist will also email a detailed itinerary to *{{ inquiry_email }}* shortly."
                }
            },
            "transitions": [{"to_step": "end_booking_flow_final", "condition_config": {"type": "always_true"}}]
        },
        # Step 10: Final confirmation message
        {
            "name": "end_quote_request_no_pdf",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you, {{ contact.name }}! Your inquiry for the *{{ tour_name }}* tour has been received (Ref: #{{ created_inquiry.id }}).\n\nWe had an issue generating the PDF, but a travel specialist will email a detailed quote to *{{ inquiry_email }}* shortly.\n\nType *menu* to return to the main menu."}
                }
            }
        },
        {
            "name": "end_booking_flow_final",
            "type": "end_flow"
        }
    ]
}