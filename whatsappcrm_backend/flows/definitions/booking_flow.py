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
                # Placeholder for missing step: end_booking_flow_final (if not already present)
                # (No action needed if already present)
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
        { # Combined asking for adults and children
            "name": "ask_number_of_travelers",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Great choice! You're booking the *{{ tour_name }}* tour.\n\nHow many adults (18+) will be traveling?"}
                },
                "reply_config": {"expected_type": "number", "save_to_variable": "num_adults", "validation_regex": "^[1-9][0-9]*$"},
                "fallback_config": {"re_prompt_message_text": "Please enter a valid number for adults (e.g., 2)."}
            },
            "transitions": [{"to_step": "ask_number_of_children", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_number_of_children",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "And how many children (under 18) will be traveling?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "num_children", "validation_regex": "^[0-9]+$"},
                "fallback_config": {"re_prompt_message_text": "Please enter a valid number for children (e.g., 0, 1)."}
            },
            "transitions": [{"to_step": "ask_travel_dates", "condition_config": {"type": "always_true"}}]
        },
        # Step 7: Ask for preferred travel dates using Native Flow
        {
            "name": "ask_travel_dates",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "flow",
                        "header": {"type": "text", "text": "Select Your Dates"},
                        "body": {"text": "Please select your desired start and end dates for the tour."},
                        "footer": {"text": "Click the button to open the date picker."},
                        "action": {
                            "name": "flow",
                            "parameters": {
                                "flow_message_version": "3",
                                "flow_token": "a_unique_token_for_this_interaction",
                                "flow_id": "{{ get_whatsapp_flow_id('date_picker_whatsapp_flow') }}",
                                "flow_cta": "Select Dates",
                                "flow_action": "navigate",
                                "flow_action_payload": {
                                    "screen": "Date_Picker_Screen",
                                    "data": {
                                        "date_picker_config": {
                                            "type": "range",
                                            "title": "Select Tour Dates",
                                            "description": "Choose the start and end dates for your adventure.",
                                            "range": {
                                                "min": "{{ now() | strftime('%Y-%m-%d') }}",
                                                "max": "{{ (now() + timedelta(days=730)) | strftime('%Y-%m-%d') }}"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "reply_config": {"expected_type": "nfm_reply", "save_to_variable": "date_selection_response"}
            },
            "transitions": [{"to_step": "process_date_selection", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "process_date_selection",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "start_date", "value_template": "{{ date_selection_response.start_date }}"},
                    {"action_type": "set_context_variable", "variable_name": "end_date", "value_template": "{{ date_selection_response.end_date }}"},
                    {
                        "action_type": "query_model",
                        "app_label": "products_and_services",
                        "model_name": "SeasonalTourPrice",
                        "variable_name": "seasonal_price",
                        "filters_template": {
                            "tour_id": "{{ tour_id }}",
                            "start_date__lte": "{{ date_selection_response.start_date }}",
                            "end_date__gte": "{{ date_selection_response.start_date }}"
                        },
                        "fields_to_return": ["price_per_adult", "price_per_child"],
                        "limit": 1
                    }
                ]
            },
            "transitions": [
                {"to_step": "calculate_total_cost", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "seasonal_price.0"}},
                {"to_step": "handle_no_price_for_date", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 3: Initialize the loop counter for collecting traveler details
        {
            "name": "initialize_traveler_loop",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "traveler_index", "value_template": 1},
                    {"action_type": "set_context_variable", "variable_name": "num_travelers", "value_template": "{{ num_adults|int + num_children|int }}"}
                ]
            },
            "transitions": [{"to_step": "ask_traveler_name", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "calculate_total_cost",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "total_cost",
                        "value_template": "{{ (seasonal_price.0.price_per_adult * num_adults) + ((seasonal_price.0.price_per_child or seasonal_price.0.price_per_adult) * num_children) }}"
                    }
                ]
            },
            "transitions": [{"to_step": "ask_email", "condition_config": {"type": "always_true"}}]
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
                "reply_config": {"expected_type": "text", "save_to_variable": "current_traveler_name"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid name."}
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
                "reply_config": {"expected_type": "number", "save_to_variable": "current_traveler_age", "validation_regex": "^[0-9]{1,3}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid age (e.g., 34)."}
            },
            "transitions": [{"to_step": "ask_traveler_nationality", "condition_config": {"type": "always_true"}}]
        },
        # Step 5b: Ask for nationality
        {
            "name": "ask_traveler_nationality",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "What is the nationality of *{{ current_traveler_name }}*?"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "current_traveler_nationality"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid nationality."}
            },
            "transitions": [{"to_step": "ask_traveler_medical", "condition_config": {"type": "always_true"}}]
        },
        # Step 5c: Ask for dietary/medical needs
        {
            "name": "ask_traveler_medical",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Does *{{ current_traveler_name }}* have any dietary restrictions or medical needs? (Type 'none' if not)"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "current_traveler_medical"}
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
                        "value_template": "{{ travelers_details + [{'name': current_traveler_name, 'age': current_traveler_age, 'nationality': current_traveler_nationality, 'medical': current_traveler_medical}] }}"
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
                {"to_step": "ask_travel_dates", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
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
                {"to_step": "ask_email_support", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 8b: If no email, offer support
        {
            "name": "ask_email_support",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "If you have trouble providing an email, please contact our support team at bookings@kalaisafaris.com or type 'menu' to return to the main menu."}
            },
            "transitions": [{"to_step": "end_booking_flow_final", "condition_config": {"type": "always_true"}}]
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
        # Step 9: Show booking summary and confirm
        {
            "name": "show_booking_summary",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please review your booking details:\n\n*Tour:* {{ tour_name }}\n*Dates:* {{ start_date }} to {{ end_date }}\n*Guests:* {{ num_adults }} Adult(s), {{ num_children }} Child(ren)\n*Travelers:*\n{% for t in travelers_details %}- {{ t.name }}, Age: {{ t.age }}, Nationality: {{ t.nationality }}, Medical: {{ t.medical }}\n{% endfor %}\n*Email:* {{ inquiry_email }}\n*Total Cost:* *${{ '%.2f'|format(total_cost|float) }}*\n\nIs everything correct?"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "summary_confirmation"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please reply 'yes' to confirm or 'edit' to make changes."}
            },
            "transitions": [
                {"to_step": "ask_payment_option", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "summary_confirmation", "value": "yes"}},
                {"to_step": "edit_booking_details", "priority": 2, "condition_config": {"type": "variable_equals", "variable_name": "summary_confirmation", "value": "edit"}},
                {"to_step": "show_booking_summary", "priority": 3, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 9b: Edit booking details (simple restart for now)
        {
            "name": "edit_booking_details",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Let's start over so you can update your details. Type 'menu' at any time to return to the main menu."}
            },
            "transitions": [{"to_step": "start_booking", "condition_config": {"type": "always_true"}}]
        },
        # Step 10: Payment options
        {
            "name": "ask_payment_option",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Confirm & Pay"},
                        "body": {
                            "text": "Select a payment option below."
                        },
                        "footer": {"text": "Select an option"},
                        "action": {
                            "button": "Payment Options",
                            "sections": [
                                {
                                    "title": "Online Payment",
                                    "rows": [
                                        {"id": "pay_full", "title": "Pay Full Amount Now"},
                                        {"id": "pay_deposit", "title": "Pay 50% Deposit Now"},
                                        {"id": "manual_omari", "title": "Pay with Omari"}
                                    ]
                                },
                                {
                                    "title": "Manual Payment",
                                    "rows": [
                                        {"id": "manual_bank", "title": "Manual/Bank Transfer"}
                                    ]
                                },
                                {"title": "Other", "rows": [{"id": "get_quote", "title": "Just Get a Quote"}]}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_choice"}
            },
            "transitions": [
                {"to_step": "set_payment_amount_full", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_full"}},
                {"to_step": "set_payment_amount_deposit", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "pay_deposit"}},
                {"to_step": "set_payment_amount_full", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_omari"}},
                {"to_step": "create_booking_for_manual_payment", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_bank"}},
                {"to_step": "create_inquiry_record_only", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "get_quote"}}
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
                        "tour_id": "{{ tour_id }}", # Ensure tour_id is passed from view_tours_flow
                        "start_date": "{{ start_date }}",
                        "end_date": "{{ end_date }}",
                        "number_of_adults": "{{ num_adults }}",
                        "number_of_children": "{{ num_children }}",
                        "total_amount": "{{ total_cost }}",
                        "payment_status": "pending",
                        "source": "whatsapp",
                        "notes": "Booking via WhatsApp. Travelers: {{ num_adults }} adults, {{ num_children }} children."
                    },
                    "save_to_variable": "created_booking"
                }]
            },
            "transitions": [{"to_step": "initiate_payment", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "create_booking_for_manual_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "fields_template": {
                        "customer": "current",
                        "tour_name": "{{ tour_name }}",
                        "tour_id": "{{ tour_id }}", # Ensure tour_id is passed from view_tours_flow
                        "start_date": "{{ start_date }}",
                        "end_date": "{{ end_date }}",
                        "number_of_adults": "{{ num_adults }}",
                        "number_of_children": "{{ num_children }}",
                        "total_amount": "{{ total_cost }}",
                        "payment_status": "pending_manual",
                        "source": "whatsapp",
                        "notes": "Booking via WhatsApp. Manual payment selected. Travelers: {{ num_adults }} adults, {{ num_children }} children."
                    },
                    "save_to_variable": "created_booking"
                }]
            },
            "transitions": [
                {"to_step": "send_manual_payment_instructions", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "send_manual_payment_instructions",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Thank you! Your booking (Ref: #{{ created_booking.booking_reference }}) is confirmed pending payment.\n\nPlease make a bank transfer for *${{ '%.2f'|format(total_cost|float) }}* to:\n\nBank: *Example Bank*\nAccount Name: *Kalai Safaris*\nAccount Number: *1234567890*\nBranch Code: *001122*\n\nUse your booking reference as the payment reference. Please send proof of payment to this number."}
                }
            }
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
                            "number_of_travelers": "{{ num_adults|int + num_children|int }}",
                            "preferred_dates": "{{ start_date }} to {{ end_date }}",
                            "notes": "Quote requested via WhatsApp for a pre-defined tour. Contact Email: {{ inquiry_email }}.",
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
            "name": "handle_no_price_for_date",
            "type": "end_flow",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "We're sorry, but pricing is not available for the selected dates. A travel expert has been notified and will contact you shortly to assist with a custom quote.\n\nType 'menu' to return to the main menu."}}
                # Optionally, add a 'send_group_notification' action here to alert the sales team.
            }
        },
        {
            "name": "end_booking_flow_final",
            "type": "end_flow"
        }
    ]
}