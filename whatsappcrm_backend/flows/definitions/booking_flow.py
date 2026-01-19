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
            "transitions": [{"to_step": "query_tour_details", "condition_config": {"type": "always_true"}}]
        },
        # Step 1b: Query tour details to get duration and base price
        {
            "name": "query_tour_details",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Tour",
                    "variable_name": "tour_details",
                    "filters_template": {
                        "id": "{{ tour_id }}"
                    },
                    "fields_to_return": ["duration_days", "name", "base_price"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "set_tour_duration", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "tour_details.0"}},
                {"to_step": "ask_number_of_travelers", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 1c: Set tour duration variable for easy access
        {
            "name": "set_tour_duration",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "tour_duration_days", "value_template": "{{ tour_details.0.duration_days }}"}
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
                    "text": {"body": "Great choice! You're booking the *{{ tour_name }}* tour.\n\nHow many adults (12+) will be traveling?"}
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
                "message_config": {"message_type": "text", "text": {"body": "And how many children (under 12) will be traveling?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "num_children", "validation_regex": "^[0-9]+$"},
                "fallback_config": {"re_prompt_message_text": "Please enter a valid number for children (e.g., 0, 1)."}
            },
            "transitions": [{"to_step": "query_date_picker_whatsapp_flow", "condition_config": {"type": "always_true"}}]
        },
        # Step 3: Query the WhatsApp Flow from database
        {
            "name": "query_date_picker_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "date_picker_whatsapp_flow",
                    "filters_template": {
                        "name": "date_picker_whatsapp_flow",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "ask_travel_dates", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "date_picker_whatsapp_flow.0"}},
                {"to_step": "fallback_ask_dates_text", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 4: Ask for preferred travel start date using Native Flow
        {
            "name": "ask_travel_dates",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "flow",
                        "header": {"type": "text", "text": "Select Start Date"},
                        "body": {"text": "Please select your desired start date for the tour. The tour duration is {{ tour_duration_days }} day(s)."},
                        "footer": {"text": "Click the button to open the date picker."},
                        "action": {
                            "name": "flow",
                            "parameters": {
                                "flow_message_version": "3",
                                "flow_token": "{{ contact.id }}-booking-{{ now().timestamp()|int }}",
                                "flow_id": "{{ date_picker_whatsapp_flow.0.flow_id }}",
                                "flow_cta": "Select Date",
                                "flow_action": "navigate",
                                "flow_action_payload": {
                                    "screen": "WELCOME",
                                    "data": {
                                        "date_picker_config": {
                                            "type": "single",
                                            "title": "Select Tour Start Date",
                                            "description": "Choose the start date for your adventure.",
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
        # Step 5: Fallback if WhatsApp Flow is not available
        {
            "name": "fallback_ask_dates_text",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please enter your preferred start date for the tour (e.g., 2025-12-25 or December 25, 2025). The tour duration is {{ tour_duration_days }} day(s)."}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "start_date_text"}
            },
            "transitions": [{"to_step": "process_fallback_dates", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "process_fallback_dates",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "start_date", "value_template": "{{ start_date_text }}"},
                    {"action_type": "set_context_variable", "variable_name": "end_date", "value_template": "{{ (start_date_text | parse_date + timedelta(days=tour_duration_days|int - 1)) | strftime('%Y-%m-%d') }}"}
                ]
            },
            "transitions": [{"to_step": "confirm_selected_dates", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "process_date_selection",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "start_date", "value_template": "{{ date_selection_response['selected_date'] }}"},
                    {"action_type": "set_context_variable", "variable_name": "end_date", "value_template": "{{ (date_selection_response['selected_date'] | parse_date + timedelta(days=tour_duration_days|int - 1)) | strftime('%Y-%m-%d') }}"}
                ]
            },
            "transitions": [{"to_step": "confirm_selected_dates", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "confirm_selected_dates",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {
                            "text": "You have selected the following dates:\n\n*Start Date:* {{ start_date }}\n*End Date:* {{ end_date }}\n*Duration:* {{ tour_duration_days }} day(s)\n\nAre these dates correct?"
                        },
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "confirm_dates",
                                        "title": "Confirm"
                                    }
                                },
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "edit_dates",
                                        "title": "Edit Dates"
                                    }
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "date_confirmation"}
            },
            "transitions": [
                {"to_step": "query_seasonal_pricing", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_dates"}},
                {"to_step": "query_date_picker_whatsapp_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "edit_dates"}},
                {"to_step": "query_seasonal_pricing", "priority": 3, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_seasonal_pricing",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "query_model",
                        "app_label": "products_and_services",
                        "model_name": "SeasonalTourPrice",
                        "variable_name": "seasonal_price",
                        "filters_template": {
                            "tour_id": "{{ tour_id }}",
                            "start_date__lte": "{{ start_date }}",
                            "end_date__gte": "{{ start_date }}",
                            "is_active": True
                        },
                        "fields_to_return": ["price_per_adult", "price_per_child"],
                        "limit": 1
                    }
                ]
            },
            "transitions": [
                {"to_step": "calculate_total_cost", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "seasonal_price.0"}},
                {"to_step": "use_base_pricing", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 2b: Use base pricing as fallback when seasonal pricing is not available
        {
            "name": "use_base_pricing",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "price_per_adult",
                        "value_template": "{{ tour_details.0.base_price }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "price_per_child",
                        "value_template": "{{ tour_details.0.base_price }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "calculate_total_cost_base", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "tour_details.0.base_price"}},
                {"to_step": "handle_missing_price_data", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 2c: Calculate total cost using base pricing
        {
            "name": "calculate_total_cost_base",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "total_cost",
                        "value_template": "{{ ((price_per_adult|float) * (num_adults|int)) + ((price_per_child|float) * (num_children|int)) }}"
                    }
                ]
            },
            "transitions": [{"to_step": "initialize_traveler_loop", "condition_config": {"type": "always_true"}}]
        },
        # Step 3: Initialize the loop counter for collecting traveler details
        {
            "name": "initialize_traveler_loop",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "traveler_index", "value_template": 1},
                    {"action_type": "set_context_variable", "variable_name": "num_travelers", "value_template": "{{ num_adults|int + num_children|int }}"},
                    {"action_type": "set_context_variable", "variable_name": "adult_index", "value_template": 1},
                    {"action_type": "set_context_variable", "variable_name": "child_index", "value_template": 1}
                ]
            },
            "transitions": [{"to_step": "query_traveler_details_whatsapp_flow", "condition_config": {"type": "always_true"}}]
        },
        # Step 3b: Query the Traveler Details WhatsApp Flow from database
        {
            "name": "query_traveler_details_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "traveler_details_whatsapp_flow",
                    "filters_template": {
                        "name": "traveler_details_whatsapp_flow",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "ask_traveler_details_via_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "traveler_details_whatsapp_flow.0"}},
                {"to_step": "ask_traveler_name", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 3c: Ask for traveler details using WhatsApp Flow
        {
            "name": "ask_traveler_details_via_flow",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "flow",
                        "header": {"type": "text", "text": "Traveler {{ traveler_index }} of {{ num_travelers }}"},
                        "body": {"text": "Please provide the details for traveler {{ traveler_index }}."},
                        "footer": {"text": "Click the button to continue."},
                        "action": {
                            "name": "flow",
                            "parameters": {
                                "flow_message_version": "3",
                                "flow_token": "{{ contact.id }}-traveler-{{ traveler_index }}-{{ now().timestamp()|int }}",
                                "flow_id": "{{ traveler_details_whatsapp_flow.0.flow_id }}",
                                "flow_cta": "Enter Details",
                                "flow_action": "navigate",
                                "flow_action_payload": {
                                    "screen": "TRAVELER_INFO",
                                    "data": {
                                        "traveler_number": "",
                                        "total_travelers": "",
                                        "traveler_name": "",
                                        "traveler_age": "",
                                        "traveler_nationality": "",
                                        "traveler_medical": "",
                                        "traveler_gender": "",
                                        "traveler_id_number": ""
                                    }
                                }
                            }
                        }
                    }
                },
                "reply_config": {"expected_type": "nfm_reply", "save_to_variable": "traveler_details_response"}
            },
            "transitions": [{"to_step": "process_traveler_details_response", "condition_config": {"type": "always_true"}}]
        },
        # Step 3d: Process traveler details response from WhatsApp Flow
        {
            "name": "process_traveler_details_response",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_name", "value_template": "{{ (traveler_details_response or {}).get('traveler_name', '') }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_age", "value_template": "{{ (traveler_details_response or {}).get('traveler_age', '') }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_nationality", "value_template": "{{ (traveler_details_response or {}).get('traveler_nationality', '') }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_medical", "value_template": "{{ (traveler_details_response or {}).get('traveler_medical', 'No special requirements') }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_gender", "value_template": "{{ (traveler_details_response or {}).get('traveler_gender', '') }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_id_number", "value_template": "{{ (traveler_details_response or {}).get('traveler_id_number', '') }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_traveler_id_document", "value_template": "{{ (traveler_details_response or {}).get('id_document_photo', '') }}"}
                ]
            },
            "transitions": [
                {"to_step": "confirm_traveler_details", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "traveler_details_response.traveler_name"}},
                {"to_step": "ask_traveler_name", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        # Step 3e: Confirm traveler details with buttons
        {
            "name": "confirm_traveler_details",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {
                            "text": "Please confirm the details for Traveler {{ traveler_index }}:\n\n*Name:* {{ current_traveler_name }}\n*Age:* {{ current_traveler_age }}\n*Nationality:* {{ current_traveler_nationality }}\n*Gender:* {{ current_traveler_gender|capitalize }}\n*ID/Passport:* {{ (current_traveler_id_number|string)|length > 4 and ('***' ~ (current_traveler_id_number|string)[-4:]) or (current_traveler_id_number|string) }}\n*Medical/Dietary:* {{ 'Provided' if current_traveler_medical and (current_traveler_medical|lower) not in ['none', 'no', 'n/a', 'na'] else 'None' }}\n\nAre these details correct?"
                        },
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "confirm_traveler",
                                        "title": "Confirm"
                                    }
                                },
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "edit_traveler",
                                        "title": "Edit"
                                    }
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "traveler_confirmation"}
            },
            "transitions": [
                {"to_step": "add_traveler_to_list", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_traveler"}},
                {"to_step": "query_traveler_details_whatsapp_flow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "edit_traveler"}},
                {"to_step": "add_traveler_to_list", "priority": 3, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "calculate_total_cost",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "price_per_adult",
                        "value_template": "{{ seasonal_price.0.price_per_adult }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "price_per_child",
                        "value_template": "{{ seasonal_price.0.price_per_child or seasonal_price.0.price_per_adult }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "total_cost",
                        "value_template": "{{ ((seasonal_price.0.price_per_adult|float) * (num_adults|int)) + (((seasonal_price.0.price_per_child or seasonal_price.0.price_per_adult)|float) * (num_children|int)) }}"
                    }
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
                    "text": {"body": "Let's get the details for {% if adult_index <= num_adults|int %}Adult {{ adult_index }} of {{ num_adults }}{% else %}Child {{ child_index }} of {{ num_children }}{% endif %}.\n\nWhat is their full name?"}
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
            "transitions": [{"to_step": "ask_traveler_gender", "condition_config": {"type": "always_true"}}]
        },
        # Step 5c: Ask for gender
        {
            "name": "ask_traveler_gender",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "What is the gender of *{{ current_traveler_name }}*? (Male/Female/Other)"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "current_traveler_gender", "validation_regex": "^(?i)(male|female|other|m|f)$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid gender (Male, Female, Other, or M/F)."}
            },
            "transitions": [{"to_step": "ask_traveler_id_number", "condition_config": {"type": "always_true"}}]
        },
        # Step 5d: Ask for ID/Passport number
        {
            "name": "ask_traveler_id_number",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "What is the ID or Passport number for *{{ current_traveler_name }}*?"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "current_traveler_id_number", "validation_regex": "^[A-Za-z0-9]{5,20}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid ID or Passport number (5-20 alphanumeric characters)."}
            },
            "transitions": [{"to_step": "ask_traveler_medical", "condition_config": {"type": "always_true"}}]
        },
        # Step 5e: Ask for dietary/medical needs
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
            "transitions": [{"to_step": "confirm_traveler_details", "condition_config": {"type": "always_true"}}]
        },
        # Step 6: Add the collected details to the list and increment the counter
        # Note: This step tracks both overall traveler_index (1 to num_travelers) and separate
        # adult_index and child_index counters. Adults are collected first (traveler_index 1 to num_adults),
        # then children (traveler_index num_adults+1 to num_travelers).
        {
            "name": "add_traveler_to_list",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "travelers_details",
                        "value_template": "{{ travelers_details + [{'name': current_traveler_name, 'age': current_traveler_age|string, 'nationality': current_traveler_nationality, 'medical': current_traveler_medical, 'gender': current_traveler_gender, 'id_number': current_traveler_id_number, 'id_document': current_traveler_id_document, 'type': ('adult' if (traveler_index|int) <= (num_adults|int) else 'child')}] }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "traveler_index",
                        "value_template": "{{ (traveler_index|int) + 1 }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "adult_index",
                        "value_template": "{{ (adult_index|int) + 1 if (traveler_index|int) <= (num_adults|int) else (adult_index|int) }}"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "child_index",
                        "value_template": "{{ (child_index|int) + 1 if (traveler_index|int) > (num_adults|int) else (child_index|int) }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "query_traveler_details_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_less_than_or_equal", "variable_name": "traveler_index", "value_template": "{{ num_travelers|int }}"}},
                {"to_step": "ask_email", "priority": 2, "condition_config": {"type": "always_true"}}
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
            "transitions": [{"to_step": "show_booking_summary", "condition_config": {"type": "always_true"}}]
        },
        # Step 9: Show booking summary and confirm
        {
            "name": "show_booking_summary",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {
                            "text": "Please review your booking details:\n\n*Tour:* {{ tour_name }}\n*Dates:* {{ start_date }} to {{ end_date }}\n*Guests:* {{ num_adults }} Adult(s), {{ num_children }} Child(ren)\n\n*Pricing:*\n- Price per Adult: ${{ '%.2f'|format((price_per_adult or tour_details.0.base_price)|float) }}\n- Price per Child: ${{ '%.2f'|format(((price_per_child or price_per_adult or tour_details.0.base_price))|float) }}\n- Subtotal Adults: ${{ '%.2f'|format(((price_per_adult or tour_details.0.base_price)|float * (num_adults|int))) }}\n- Subtotal Children: ${{ '%.2f'|format((((price_per_child or price_per_adult or tour_details.0.base_price)|float) * (num_children|int))) }}\n\n*Travelers:*\n{% set valid_travelers = travelers_details | selectattr('name', 'defined') | selectattr('name') | list %}{% for t in valid_travelers[:10] %}\n- {{ t.name }} (Age: {{ t.age }}){% endfor %}{% if valid_travelers|length > 10 %}\n... and {{ valid_travelers|length - 10 }} more traveler(s){% endif %}\n\n*Email:* {{ inquiry_email }}\n*Total Cost:* *${{ '%.2f'|format(total_cost|float) }}*\n\nIs everything correct?"
                        },
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "confirm_booking",
                                        "title": "Confirm"
                                    }
                                },
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "edit_booking",
                                        "title": "Edit Details"
                                    }
                                }
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "summary_confirmation"}
            },
            "transitions": [
                {"to_step": "ask_payment_option", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_booking"}},
                {"to_step": "edit_booking_details", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "edit_booking"}},
                {"to_step": "ask_payment_option", "priority": 3, "condition_config": {"type": "always_true"}}
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
                                    "title": "Mobile Money (Paynow)",
                                    "rows": [
                                        {"id": "paynow_full", "title": "Pay Full via Paynow"},
                                        {"id": "paynow_deposit", "title": "Pay 50% Deposit Paynow"}
                                    ]
                                },
                                {
                                    "title": "Other Online Payment",
                                    "rows": [
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
                {"to_step": "set_payment_amount_full_paynow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "paynow_full"}},
                {"to_step": "set_payment_amount_deposit_paynow", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "paynow_deposit"}},
                {"to_step": "prepare_omari_payment", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_omari"}},
                {"to_step": "create_booking_for_manual_payment", "priority": 4, "condition_config": {"type": "interactive_reply_id_equals", "value": "manual_bank"}},
                {"to_step": "create_inquiry_record_only", "priority": 5, "condition_config": {"type": "interactive_reply_id_equals", "value": "get_quote"}}
            ]
        },
        # New step to prepare booking for Omari payment
        {
            "name": "prepare_omari_payment",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "is_omari_user", "value_template": "unknown"},
                    {"action_type": "set_context_variable", "variable_name": "amount_to_pay", "value_template": "{{ total_cost }}"},
                    {"action_type": "set_context_variable", "variable_name": "current_phone", "value_template": "{{ contact.phone_number }}"}
                ]
            },
            "transitions": [
                {"to_step": "create_booking_for_omari", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "omari_payment_error",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "We ran into a problem verifying your Omari account. Please try again in a moment or choose another payment method."
                }
            },
            "transitions": [
                {"to_step": "ask_payment_option", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "omari_not_eligible",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": "{{ omari_not_eligible_message }}"
                }
            },
            "transitions": [{"to_step": "ask_payment_option", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "create_booking_for_omari",
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
                        "start_date": "{{ start_date | parse_date }}",
                        "end_date": "{{ end_date | parse_date }}",
                        "number_of_adults": "{{ num_adults }}",
                        "number_of_children": "{{ num_children }}",
                        "total_amount": "{{ total_cost }}",
                        "payment_status": "pending",
                        "booking_reference": "PENDING-{{ contact.id }}-{{ now().timestamp() }}",
                        "source": "whatsapp",
                        "notes": "Booking via WhatsApp. Omari payment selected. Travelers: {{ num_adults }} adults, {{ num_children }} children."
                    },
                    "save_to_variable": "created_booking"
                }]
            },
            "transitions": [{"to_step": "save_travelers_to_omari_booking", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "save_travelers_to_omari_booking",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "save_travelers_to_booking",
                    "params_template": {
                        "booking_context_var": "created_booking",
                        "travelers_context_var": "travelers_details"
                    }
                }]
            },
                "transitions": [{"to_step": "omari_ask_alternative_phone", "condition_config": {"type": "always_true"}}]
        },


            {
                "name": "omari_ask_alternative_phone",
                "type": "question",
                "config": {
                    "message_config": {
                        "message_type": "text",
                        "text": {"body": "Enter the mobile money number to charge (format 2637XXXXXXXX)."}
                    },
                    "reply_config": {"expected_type": "text", "save_to_variable": "payment_phone", "validation_regex": "^2637[0-9]{8}$"},
                    "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid Zimbabwe mobile number starting with 2637 (e.g., 263771234567)."}
                },
                "transitions": [{"to_step": "omari_validate_phone_format", "condition_config": {"type": "always_true"}}]
            },
            {
                "name": "omari_validate_phone_format",
                "type": "action",
                "config": {
                    "actions_to_run": [
                        {"action_type": "validate_omari_phone", "phone_variable": "payment_phone"}
                    ]
                },
                "transitions": [
                    {"to_step": "omari_set_payment_reference", "condition_config": {"type": "variable_exists", "variable_name": "payment_phone_valid"}},
                    {"to_step": "omari_payment_validation_failed", "condition_config": {"type": "always_true"}}
                ]
            },
            {
                "name": "omari_payment_validation_failed",
                "type": "end_flow",
                "config": {
                    "message_config": {
                        "message_type": "text",
                        "text": {"body": "Invalid mobile number format. Please try again with a valid Zimbabwe mobile number (format 2637XXXXXXXX)."}
                    }
                }
            },
            {
                "name": "omari_set_payment_reference",
                "type": "action",
                "config": {
                    "actions_to_run": [
                        {"action_type": "set_context_variable", "variable_name": "payment_booking_reference", "value_template": "{{ created_booking.booking_reference or created_booking.id }}"}
                    ]
                },
                "transitions": [{"to_step": "omari_initiate_payment", "condition_config": {"type": "always_true"}}]
            },
            {
                "name": "omari_initiate_payment",
                "type": "action",
                "config": {
                    "actions_to_run": [
                        {
                            "action_type": "initiate_omari_payment",
                            "params_template": {
                                "booking_reference": "{{ payment_booking_reference }}",
                                "amount": "{{ amount_to_pay }}",
                                "currency": "USD",
                                "channel": "WEB",
                                "msisdn": "{{ payment_phone }}"
                            }
                        }
                    ]
                },
                "transitions": [
                    {"to_step": "omari_payment_initiated", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "omari_otp_reference"}},
                    {"to_step": "omari_payment_initiation_failed", "priority": 2, "condition_config": {"type": "always_true"}}
                ]
            },
            {
                "name": "omari_payment_initiated",
                "type": "question",
                "config": {
                    "message_config": {
                        "message_type": "text",
                        "text": {"body": "✅ Payment started! An OTP was sent to *{{ payment_phone }}*. Enter the OTP to confirm, or type *cancel* to abort."}
                    },
                    "reply_config": {"expected_type": "text", "save_to_variable": "otp_input"}
                },
                "transitions": [
                    {"to_step": "omari_cancel_payment", "priority": 0, "condition_config": {"type": "text_contains_any", "values": ["cancel", "stop", "quit", "abort"]}},
                    {"to_step": "omari_process_otp", "priority": 1, "condition_config": {"type": "always_true"}}
                ]
            },
            {
                "name": "omari_process_otp",
                "type": "action",
                "config": {"actions_to_run": [{"action_type": "process_otp", "otp": "{{ otp_input }}"}]},
                "transitions": [
                    {"to_step": "omari_finalize_booking", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "omari_payment_success"}},
                    {"to_step": "omari_payment_failed", "priority": 1, "condition_config": {"type": "always_true"}}
                ]
            },
            {
                "name": "omari_finalize_booking",
                "type": "action",
                "config": {
                    "actions_to_run": [
                        {
                            "action_type": "update_model_instance",
                            "app_label": "customer_data",
                            "model_name": "Booking",
                            "instance_id": "{{ created_booking.id }}",
                            "fields_to_update": {
                                "booking_reference": "",
                                "payment_status": "partially_paid",
                                "amount_paid": "{{ amount_to_pay }}"
                            },
                            "save_to_variable": "finalized_booking",
                            "comment": "Setting booking_reference to empty string triggers auto-generation in Booking.save() method"
                        }
                    ]
                },
                "transitions": [{"to_step": "omari_payment_success", "condition_config": {"type": "always_true"}}]
            },
            {
                "name": "omari_payment_success",
                "type": "end_flow",
                "config": {
                    "message_config": {"message_type": "text", "text": {"body": "🎉 Payment confirmed!\n\nAmount: *${{ '%.2f'|format(amount_to_pay|float) }}*\n✅ Booking Reference: *{{ finalized_booking.booking_reference }}*\nPayment Ref: *{{ omari_payment_reference }}*\n\nPlease save your booking reference for future use."}}
                }
            },
            {
                "name": "omari_payment_failed",
                "type": "question",
                "config": {
                    "message_config": {"message_type": "text", "text": {"body": "The OTP looks invalid or expired. Enter the OTP again or type *cancel* to abort."}},
                    "reply_config": {"expected_type": "text", "save_to_variable": "otp_input"}
                },
                "transitions": [
                    {"to_step": "omari_cancel_payment", "priority": 0, "condition_config": {"type": "text_contains_any", "values": ["cancel", "stop", "quit", "abort"]}},
                    {"to_step": "omari_process_otp", "priority": 1, "condition_config": {"type": "always_true"}}
                ]
            },
            {
                "name": "omari_cancel_payment",
                "type": "end_flow",
                "config": {"message_config": {"message_type": "text", "text": {"body": "Payment canceled. You can restart payment from the menu anytime."}}}
            },
            {
                "name": "omari_payment_initiation_failed",
                "type": "end_flow",
                "config": {"message_config": {"message_type": "text", "text": {"body": "We couldn't start the Omari payment. Please try again later or choose another payment method."}}}
            },
        # Paynow Payment Flow Steps
        {
            "name": "set_payment_amount_full_paynow",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "amount_to_pay", "value_template": "{{ total_cost }}"}]},
            "transitions": [{"to_step": "create_booking_for_paynow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "set_payment_amount_deposit_paynow",
            "type": "action",
            "config": {"actions_to_run": [{"action_type": "set_context_variable", "variable_name": "amount_to_pay", "value_template": "{{ total_cost|float * 0.5 }}"}]},
            "transitions": [{"to_step": "create_booking_for_paynow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "create_booking_for_paynow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "fields_template": {
                        "customer_id": "{{ contact.customer_profile.contact_id }}",
                        "tour_id": "{{ tour_id }}",
                        "tour_name": "{{ tour_name }}",
                        "start_date": "{{ selected_start_date }}",
                        "end_date": "{{ selected_end_date }}",
                        "number_of_adults": "{{ num_adults }}",
                        "number_of_children": "{{ num_children }}",
                        "total_amount": "{{ total_cost }}",
                        "payment_status": "pending",
                        "source": "whatsapp",
                        "notes": "Booking via WhatsApp. Paynow payment selected. Travelers: {{ num_adults }} adults, {{ num_children }} children."
                    },
                    "save_to_variable": "created_booking"
                }]
            },
            "transitions": [
                {"to_step": "save_travelers_for_paynow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "created_booking.id"}},
                {"to_step": "booking_creation_failed", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_travelers_for_paynow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_travelers_from_list",
                    "params_template": {
                        "booking_id": "{{ created_booking.id }}",
                        "travelers_list": "{{ travelers_details }}"
                    }
                }]
            },
            "transitions": [{"to_step": "query_payment_whatsapp_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "query_payment_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "payment_whatsapp_flow",
                    "filters_template": {
                        "name": "payment_whatsapp_flow",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["id", "flow_id", "name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "launch_payment_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "payment_whatsapp_flow.0.flow_id"}},
                {"to_step": "paynow_flow_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "launch_payment_whatsapp_flow",
            "type": "send_whatsapp_flow",
            "config": {
                "flow_id": "{{ payment_whatsapp_flow.0.flow_id }}",
                "flow_token": "PAYMENT_{{ created_booking.id }}_{{ now().timestamp() }}",
                "flow_action_type": "navigate",
                "screen_id": "PAYMENT",
                "data": {
                    "booking_reference": "{{ created_booking.booking_reference }}",
                    "amount": "{{ amount_to_pay }}",
                    "currency": "USD"
                },
                "save_response_to": "payment_flow_response"
            },
            "transitions": [
                {"to_step": "process_payment_flow_response", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "payment_flow_response"}},
                {"to_step": "payment_flow_failed", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "process_payment_flow_response",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "payment_method", "value_template": "{{ payment_flow_response.payment_method }}"},
                    {"action_type": "set_context_variable", "variable_name": "payment_phone", "value_template": "{{ payment_flow_response.phone_number }}"},
                    {"action_type": "set_context_variable", "variable_name": "payment_email", "value_template": "{{ payment_flow_response.email }}"}
                ]
            },
            "transitions": [
                {"to_step": "initiate_paynow_payment_api", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "payment_method"}},
                {"to_step": "payment_flow_data_missing", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "initiate_paynow_payment_api",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "initiate_paynow_payment",
                    "params_template": {
                        "booking_id": "{{ created_booking.id }}",
                        "amount": "{{ amount_to_pay }}",
                        "phone_number": "{{ payment_phone }}",
                        "email": "{{ payment_email }}",
                        "payment_method": "{{ payment_method }}"
                    },
                    "save_to_variable": "paynow_payment_result"
                }]
            },
            "transitions": [
                {"to_step": "paynow_payment_success", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "paynow_payment_result.success", "value": True}},
                {"to_step": "paynow_payment_failed_message", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "paynow_payment_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "🎉 Payment initiated successfully!\n\n*Booking Reference:* #{{ created_booking.booking_reference }}\n*Amount:* ${{ '%.2f'|format(amount_to_pay|float) }}\n*Payment Method:* {{ payment_method|title }}\n\n{{ paynow_payment_result.instructions }}\n\nYou will receive a confirmation message once payment is complete. Please save your booking reference for your records."}
                }
            }
        },
        {
            "name": "paynow_payment_failed_message",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "⚠️ Payment could not be initiated.\n\n*Booking Reference:* #{{ created_booking.booking_reference }}\n*Reason:* {{ paynow_payment_result.message }}\n\nYour booking has been saved. You can try again later or contact our support team for assistance."}
                }
            }
        },
        {
            "name": "paynow_flow_not_found",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "We're experiencing technical difficulties with the payment system. Your booking (Ref: #{{ created_booking.booking_reference }}) has been saved.\n\nOur team will contact you shortly to complete the payment. Thank you for your patience."}
                }
            }
        },
        {
            "name": "payment_flow_failed",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "The payment flow encountered an error. Your booking (Ref: #{{ created_booking.booking_reference }}) has been saved.\n\nPlease contact our support team to complete your payment."}
                }
            }
        },
        {
            "name": "payment_flow_data_missing",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Payment information was incomplete. Your booking (Ref: #{{ created_booking.booking_reference }}) has been saved.\n\nPlease try again or contact our support team for assistance."}
                }
            }
        },
        # End of Paynow Payment Flow Steps
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
                        "tour_id": "{{ tour_id }}",  # Sets the tour ForeignKey by ID (must be existing Tour PK)
                        "start_date": "{{ start_date | parse_date }}",
                        "end_date": "{{ end_date | parse_date }}",
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
            "transitions": [{"to_step": "save_travelers_to_booking", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "save_travelers_to_booking",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "save_travelers_to_booking",
                    "params_template": {
                        "booking_context_var": "created_booking",
                        "travelers_context_var": "travelers_details"
                    }
                }]
            },
            "transitions": [{"to_step": "show_booking_reference", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "show_booking_reference",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "✅ Your booking has been created!\n\n*Booking Reference:* #{{ created_booking.booking_reference }}\n\nPlease save this reference number for your records."}
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
                        "tour_id": "{{ tour_id }}",  # Sets the tour ForeignKey by ID (must be existing Tour PK)
                        "start_date": "{{ start_date | parse_date }}",
                        "end_date": "{{ end_date | parse_date }}",
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
                {"to_step": "save_travelers_to_manual_booking", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_travelers_to_manual_booking",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "save_travelers_to_booking",
                    "params_template": {
                        "booking_context_var": "created_booking",
                        "travelers_context_var": "travelers_details"
                    }
                }]
            },
            "transitions": [{"to_step": "send_manual_payment_instructions", "condition_config": {"type": "always_true"}}]
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
                            "channel": "WEB",
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
                            "destinations": "{{ tour_name }}",
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
                    "filename": "Kalai_Safaris_Quote_{{ created_inquiry.inquiry_reference }}.pdf",
                    "caption": "Thank you, {{ contact.name }}! Here is your quote for the *{{ tour_name }}* tour (Ref: #{{ created_inquiry.inquiry_reference }}).\n\nA travel specialist will contact you soon to discuss your itinerary."
                }
            },
            "transitions": [{"to_step": "ask_contact_preference", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_contact_preference",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Would you like us to contact you on this number or provide a different contact number?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "use_current", "title": "Use This Number"}},
                                {"type": "reply", "reply": {"id": "provide_another", "title": "Another Number"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "contact_choice"}
            },
            "transitions": [
                {"to_step": "end_booking_flow_final", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "use_current"}},
                {"to_step": "ask_alternate_contact", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "provide_another"}}
            ]
        },
        {
            "name": "ask_alternate_contact",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Please provide the phone number where you'd like to be contacted (with country code, e.g., +263771234567):"}
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "alternate_contact_number"},
                "fallback_config": {"re_prompt_message_text": "Please provide a valid phone number."}
            },
            "transitions": [{"to_step": "save_alternate_contact", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "save_alternate_contact",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "update_customer_profile",
                    "fields_to_update": {"notes": "Preferred contact: {{ alternate_contact_number }}"}
                }]
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
                    "text": {"body": "Thank you, {{ contact.name }}! Your inquiry for the *{{ tour_name }}* tour has been received (Ref: #{{ created_inquiry.inquiry_reference }}).\n\nWe had an issue generating the PDF, but a travel specialist will contact you shortly with a detailed quote.\n\nType *menu* to return to the main menu."}
                }
            }
        },
        {
            "name": "handle_missing_price_data",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "We apologize, but we're unable to retrieve pricing information for this tour at the moment.\n\nPlease contact our team at bookings@kalaisafaris.com or type 'menu' to return to the main menu. We'll be happy to provide you with a custom quote."}
                }
            }
        },
        {
            "name": "end_booking_flow_final",
            "type": "end_flow"
        }
    ]
}