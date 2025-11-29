# whatsappcrm_backend/flows/definitions/solar_installation_flow.py

SOLAR_INSTALLATION_FLOW = {
    "name": "solar_installation_inquiry",
    "friendly_name": "Request Solar Installation",
    "description": "Initiates the WhatsApp interactive flow for solar installation or handles price quotes.",
    "trigger_keywords": [],
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
                {"to_step": "start_installation_request", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "start_installation_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Request Installation"},
                        "body": {"text": "{% if customer_profile.first_name %}Welcome back, {{ customer_profile.first_name }}!{% else %}Welcome!{% endif %}\n\nI can help you schedule your solar installation.\n\nHave you already paid for your system, or would you like to request a price quote first?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "paid", "title": "I've Already Paid"}},
                                {"type": "reply", "reply": {"id": "ask_for_price", "title": "Ask for Price"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "payment_status_choice"}
            },
            "transitions": [
                {"to_step": "query_whatsapp_flow", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "paid"}},
                {"to_step": "initialize_quote_context", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "ask_for_price"}}
            ]
        },
        {
            "name": "query_whatsapp_flow",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "flows",
                    "model_name": "WhatsAppFlow",
                    "variable_name": "solar_installation_whatsapp_flow",
                    "filters_template": {
                        "name": "solar_installation_whatsapp",
                        "sync_status": "published"
                    },
                    "fields_to_return": ["flow_id", "friendly_name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "send_whatsapp_flow", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "solar_installation_whatsapp_flow.0"}},
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
                    "header": {
                        "type": "text",
                        "text": "Solar Installation"
                    },
                    "body": {
                        "text": "Great! Please complete our solar installation form to schedule your installation."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": "{{ contact.id }}-solar-install-{{ 'now'|date:'U' }}",
                            "flow_id": "{{ solar_installation_whatsapp_flow.0.flow_id }}",
                            "flow_cta": "Start Request",
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": "WELCOME"
                            }
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "wait_for_whatsapp_response", "priority": 1, "condition_config": {"type": "always_true"}},
                {"to_step": "end_flow_success", "priority": 2, "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "wait_for_whatsapp_response",
            "type": "action",
            "config": {
                "actions_to_run": [],
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": "Please complete the WhatsApp form. We will continue once your submission is received."
                    }
                }
            },
            "transitions": [
                {"to_step": "map_whatsapp_response_to_context", "condition_config": {"type": "whatsapp_flow_response_received"}}
            ]
        },
        {
            "name": "map_whatsapp_response_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "install_branch", "value_template": "{{ whatsapp_flow_data.branch }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_sales_person", "value_template": "{{ whatsapp_flow_data.sales_person }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_full_name", "value_template": "{{ whatsapp_flow_data.full_name }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_phone", "value_template": "{{ whatsapp_flow_data.contact_phone }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_alt_name", "value_template": "{{ whatsapp_flow_data.alt_contact_name }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_alt_phone", "value_template": "{{ whatsapp_flow_data.alt_contact_phone }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_datetime", "value_template": "{{ whatsapp_flow_data.preferred_date }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_availability", "value_template": "{{ whatsapp_flow_data.availability }}"},
                    {"action_type": "set_context_variable", "variable_name": "install_address", "value_template": "{{ whatsapp_flow_data.address }}"}
                ]
            },
            "transitions": [
                {"to_step": "ask_location_pin", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "fallback_to_legacy",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "Sorry, the interactive form is currently unavailable. Let me collect the information the traditional way."}
            },
            "transitions": [{"to_step": "ask_installation_type", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_with_form_sent",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Thank you! Please complete the form to submit your solar installation request. Our team will contact you shortly to confirm the schedule."}}}
        },
        {
            "name": "ask_installation_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Installation Type"},
                        "body": {"text": "Great! Is this for a Residential or Commercial property?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "install_residential", "title": "Residential"}},
                                {"type": "reply", "reply": {"id": "install_commercial", "title": "Commercial"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "installation_type"}
            },
            "transitions": [
                {"to_step": "query_customer_paid_orders", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "install_residential"}},
                {"to_step": "ask_commercial_assessment_number", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "install_commercial"}}
            ]
        },
        {
            "name": "query_customer_paid_orders",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "customer_paid_orders",
                    "filters_template": {
                        "customer_id": "{{ customer_profile.id }}",
                        "payment_status": "paid",
                        "stage": "closed_won"
                    },
                    "fields_to_return": ["id", "order_number", "name", "amount"],
                    "order_by": ["-created_at"]
                }]
            },
            "transitions": [
                {"to_step": "display_paid_orders_for_selection", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "customer_paid_orders.0"}},
                {"to_step": "handle_no_paid_orders_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_paid_orders_for_selection",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Select Your Order"},
                        "body": {"text": "Great! We found the following paid orders under your profile. Please select the one you'd like to schedule for installation."},
                        "action": {
                            "button": "Choose Order",
                            "sections": [{
                                "title": "Your Paid Orders",
                                "rows": "{{ customer_paid_orders | to_interactive_rows(row_template={'id': '{{ item.id }}', 'title': '{{ item.order_number }}', 'description': '{{ item.name }}'}) }}"
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "selected_order_id"}
            },
            "transitions": [
                {"to_step": "verify_order_payment_from_selection", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "selected_order_id"}}
            ]
        },
        {
            "name": "handle_no_paid_orders_found",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "No Orders Found"},
                        "body": {"text": "We couldn't find any paid orders linked to your WhatsApp number.\n\nHow would you like to proceed?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "enter_order_manually", "title": "Enter Order Number"}},
                                {"type": "reply", "reply": {"id": "enter_assessment_manually", "title": "Enter Assessment No."}},
                                {"type": "reply", "reply": {"id": "request_agent_help", "title": "Speak to an Agent"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "no_order_choice"}
            },
            "transitions": [
                {"to_step": "ask_residential_order_number", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "enter_order_manually"}},
                {"to_step": "ask_commercial_assessment_number", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "enter_assessment_manually"}},
                {"to_step": "handle_payment_not_found", "priority": 3, "condition_config": {"type": "interactive_reply_id_equals", "value": "request_agent_help"}}
            ]
        },
        {
            "name": "ask_residential_order_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "No problem. To proceed with your residential installation, please provide your *Order Number* (e.g., 12345/PO, HAN-54321, or AV01/0034506).\n\nThis helps us verify your purchase and payment."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "order_number"}
            },
            "transitions": [
                {"to_step": "verify_order_payment", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "order_number"}}
            ]
        },
        {
            "name": "initialize_quote_context",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "set_context_variable", "variable_name": "selected_product_skus", "value_template": []}
                ]
            },
            "transitions": [{"to_step": "query_all_services_for_display", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "query_all_services_for_display",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "all_service_products",
                    "filters_template": {"is_active": True, "product_type": "service"},
                    "fields_to_return": ["sku", "name", "price"],
                    "order_by": ["name"]
                }]
            },
            "transitions": [{"to_step": "check_if_services_exist_for_display", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_if_services_exist_for_display",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "display_services_and_ask_sku", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "all_service_products.0"}},
                {"to_step": "handle_no_services_available", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_services_and_ask_sku",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "Here are our available installation services:\n\n"
                            "{% for product in all_service_products %}"
                            "- *{{ product.name }}*\n  SKU: `{{ product.sku }}` | Price: ${{ product.price }}\n"
                            "{% endfor %}\n"
                            "Please enter the SKU of the service you would like to add to your quote. Type 'done' when you are finished."
                        )
                    }
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "input_sku"}
            },
            "transitions": [
                {"to_step": "check_if_any_product_selected", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "verify_sku_and_add_to_context", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "verify_sku_and_add_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "found_product_for_quote",
                    "filters_template": {
                        "sku__iexact": "{{ input_sku }}",
                        "product_type": "service"
                    },
                    "fields_to_return": ["sku", "name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "add_sku_to_context", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_product_for_quote.0"}},
                {"to_step": "handle_invalid_sku", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "add_sku_to_context",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "selected_product_skus",
                    "value_template": "{{ selected_product_skus + [found_product_for_quote.0.sku] }}"
                }]
            },
            "transitions": [{"to_step": "query_selected_products", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "query_selected_products",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "selected_products_details",
                    "filters_template": {
                        "sku__in": "{{ selected_product_skus }}"
                    },
                    "fields_to_return": ["name", "price"]
                }]
            },
            "transitions": [{"to_step": "ask_for_next_sku", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "handle_invalid_sku",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "The SKU '{{ input_sku }}' is not valid. Please check the list and enter a valid SKU, or type 'done' to finish."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "input_sku"}
            },
            "transitions": [
                {"to_step": "check_if_any_product_selected", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "verify_sku_and_add_to_context", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_for_next_sku",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": (
                            "Added '{{ found_product_for_quote.0.name }}' to your quote.\n\n"
                            "Your current selections:\n"
                            "{% for product in selected_products_details %}- {{ product.name }} (${{ product.price }})\n{% endfor %}\n"
                            "Enter another SKU to add, or type 'done' to finalize your quote."
                        )
                    }
                },
                "reply_config": {"expected_type": "text", "save_to_variable": "input_sku"}
            },
            "transitions": [
                {"to_step": "check_if_any_product_selected", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "verify_sku_and_add_to_context", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_any_product_selected",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "generate_quote_order_number", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "selected_product_skus.0"}},
                {"to_step": "end_flow_cancelled", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "generate_quote_order_number",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "generate_unique_order_number",
                    "params_template": {
                        "save_to_variable": "generated_order_number_raw"
                    }
                }]
            },
            "transitions": [{"to_step": "prefix_order_number", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "prefix_order_number",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "generated_order_number",
                    "value_template": "HAN-{{ generated_order_number_raw }}"
                }]
            },
            "transitions": [{"to_step": "create_quote_order", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "verify_order_payment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "found_order",
                    "filters_template": {
                        "order_number__iexact": "{{ order_number }}"
                    },
                    "fields_to_return": ["id", "stage", "name", "payment_status"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_order_status", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_order.0"}},
                {"to_step": "handle_payment_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "verify_order_payment_from_selection",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "found_order",
                    "filters_template": {
                        "id": "{{ selected_order_id }}"
                    },
                    "fields_to_return": ["id", "order_number", "stage", "name", "payment_status"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_order_status", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_order.0"}},
                {"to_step": "handle_payment_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_order_status",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_branch", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "found_order.0.payment_status", "value": "paid"}},
                {"to_step": "handle_order_not_paid", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_commercial_assessment_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Understood. For commercial installations, please provide your *Site Assessment Number* (e.g., SA-67890)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "assessment_number"},
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid numeric assessment number."
                }
            },
            "transitions": [
                {"to_step": "verify_assessment", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "assessment_number"}}
            ]
        },
        {
            "name": "verify_assessment",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "SiteAssessmentRequest",
                    "variable_name": "found_assessment",
                    "filters_template": {
                        "assessment_id__iexact": "{{ assessment_number }}",
                        "status": "assessed"
                    },
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "ask_branch", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "found_assessment.0"}},
                {"to_step": "handle_assessment_not_found", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_branch",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {"type": "text", "text": "Select Branch"},
                        "body": {"text": "✅ Verification successful!\n\nLet's collect the details for your installation. Please select your branch."},
                        "action": {
                            "button": "Select Branch",
                            "sections": [{
                                "title": "Our Branches",
                                "rows": [
                                    {"id": "Harare", "title": "Harare"},
                                    {"id": "Bulawayo", "title": "Bulawayo"},
                                    {"id": "Mutare", "title": "Mutare"},
                                    {"id": "Other", "title": "Other"}
                                ]
                            }, {
                                "title": "Exit",
                                "rows": [
                                    {"id": "cancel_install", "title": "Cancel Request"}
                                ]
                            }]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_branch"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_install"}},
                {"to_step": "ask_sales_person", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_sales_person",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. Who was the *Sales Person* for this order? (e.g., John Doe)\n\n(Type 'back' to change the branch or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_sales_person",
                    "validation_regex": "^.{3,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid name (at least 3 characters)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_branch", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_client_name", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_sales_person"}}
            ]
        },
        {
            "name": "ask_client_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the *Client Name* as it appears on the invoice? (e.g., Jane Smith)\n\n(Type 'back' to change the sales person or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_full_name",
                    "validation_regex": "^.{3,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please enter a valid name (at least 3 characters)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_sales_person", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_client_phone", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_full_name"}}
            ]
        },
        {
            "name": "ask_client_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the *Client's contact number*? (e.g., +263771234567)\n\n(Type 'back' to change the client name or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_phone",
                    "validation_regex": "^\\+?[1-9]\\d{8,14}$"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "That doesn't look like a valid phone number. Please try again, including the country code (e.g., +263...)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_client_name", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_alt_contact_name", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_phone"}}
            ]
        },
        {
            "name": "ask_alt_contact_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the *Alternative Contact's Name*? (You can type 'N/A' if not applicable)\n\n(Type 'back' to change the client number or 'cancel' to exit)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_alt_name"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_client_phone", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_alt_contact_phone", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_alt_name"}}
            ]
        },
        {
            "name": "ask_alt_contact_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the *Alternative Contact's Number*? (e.g., +263719876543 or N/A)\n\n(Type 'back' to change the alt. name or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_alt_phone",
                    "validation_regex": "^(?i)(N/A|\\+?[1-9]\\d{8,14})$"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "That doesn't look like a valid phone number. Please enter a valid number (e.g., +263...) or 'N/A'."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_alt_contact_name", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_install_date", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_alt_phone"}}
            ]
        },
        {
            "name": "ask_install_date",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is your *preferred installation date*? (e.g., Tomorrow, 25 December, 2025-12-25)\n\n(Please note: We conduct installations within 48 hours of system delivery and this date is for confirmation purposes.)\n\n(Type 'back' to change the alt. number or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_datetime",
                    "validation_regex": "^.{4,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please provide a valid date (e.g., 'Tomorrow', '25 December')."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_alt_contact_phone", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_availability", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_datetime"}}
            ]
        },
        {
            "name": "ask_availability",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Thank you. What is your preferred availability on that day?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "morning", "title": "Morning"}},
                                {"type": "reply", "reply": {"id": "afternoon", "title": "Afternoon"}},
                                {"type": "reply", "reply": {"id": "go_back", "title": "Go Back"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_availability"}
            },
            "transitions": [
                {"to_step": "ask_install_date", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "go_back"}},
                {"to_step": "ask_install_address", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_availability"}}
            ]
        },
        {
            "name": "ask_install_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you. What is the *full installation address*? (e.g., 123 Solar Street, Avondale, Harare)\n\n(Type 'back' to change the availability or 'cancel' to exit)"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "install_address",
                    "validation_regex": "^.{10,}"
                },
                "fallback_config": {
                    "action": "re_prompt", "max_retries": 2,
                    "re_prompt_message_text": "Please provide a more detailed address (at least 10 characters)."
                }
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_availability", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "ask_location_pin", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_address"}}
            ]
        },
        {
            "name": "ask_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Almost done! Please share your location pin for accurate directions.\n\n(Type 'back' to change the address or 'cancel' to exit)"}},
                "reply_config": {"expected_type": "location", "save_to_variable": "install_location_pin"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "cancel"}},
                {"to_step": "ask_install_address", "priority": 2, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "back"}},
                {"to_step": "confirm_installation_request", "priority": 3, "condition_config": {"type": "variable_exists", "variable_name": "install_location_pin"}}
            ]
        },
        {
            "name": "confirm_installation_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": "Please review your details and confirm to submit your installation request.\n\n"
                            "Thank you. Please review your details and confirm to submit your installation request.\n\n"
                            "{% if order_number %}*Order #*: {{ order_number }} ({{ found_order.0.name }})\n\n{% endif %}"
                            "Branch: {{ install_branch }}\n"
                            "Sales Person: {{ install_sales_person }}\n"
                            "Client Name: {{ install_full_name }}\n"
                            "Client Contact: {{ install_phone }}\n"
                            "Alt. Contact: {{ install_alt_name }} ({{ install_alt_phone }})\n"
                            "Install Date: {{ install_datetime }} ({{ install_availability|title }})\n"
                            "Address: {{ install_address }}"
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "confirm_install", "title": "Confirm Request"}},
                                {"type": "reply", "reply": {"id": "cancel_install", "title": "Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_confirmation"}
            },
            "transitions": [
                {"to_step": "save_installation_request", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_install"}},
                {"to_step": "end_flow_cancelled", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_installation_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_contact_field",
                        "field_path": "name",
                        "value_template": "{{ install_full_name }}"
                    },
                    {
                        "action_type": "update_customer_profile",
                        "fields_to_update": {
                            "first_name": "{{ install_full_name.split(' ')[0] if ' ' in install_full_name else install_full_name }}",
                            "last_name": "{{ ' '.join(install_full_name.split(' ')[1:]) if ' ' in install_full_name else '' }}",
                            "address_line_1": "{{ install_address }}",
                            "notes": "Profile updated from Solar Installation Request flow."
                        }
                    },
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "InstallationRequest",
                        "fields_template": {
                            "customer_id": "{{ contact.id }}",
                            "associated_order_id": "{{ found_order.0.id }}",
                            "installation_type": "{{ installation_type }}",
                            "order_number": "{{ order_number }}",
                            "assessment_number": "{{ assessment_number }}",
                            "branch": "{{ install_branch }}",
                            "sales_person_name": "{{ install_sales_person }}",
                            "full_name": "{{ install_full_name }}",
                            "address": "{{ install_address }}",
                            "latitude": "{{ install_location_pin.latitude }}",
                            "longitude": "{{ install_location_pin.longitude }}",
                            "preferred_datetime": "{{ install_datetime }}",
                            "availability": "{{ install_availability }}",
                            "contact_phone": "{{ install_phone }}",
                            "alternative_contact_name": "{{ install_alt_name }}",
                            "alternative_contact_number": "{{ install_alt_phone }}"
                        },
                        "save_to_variable": "created_installation_request"
                    },
                    {
                        "action_type": "send_group_notification", # This is the new, preferred action
                        "params_template": {
                            "group_names": ["Pfungwa Staff", "System Admins"],
                            # This name must match a NotificationTemplate in the database
                            "template_name": "hanna_new_installation_request"
                        }
                    }
                ]
            },
            "transitions": [
                {"to_step": "end_flow_success", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "create_quote_order",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_order_with_items",
                    "params_template": {
                        "order_name_template": "Price Request from {{ contact.name or contact.whatsapp_id }}",
                        "stage": "prospecting",
                        "order_number_context_var": "generated_order_number",
                        "line_item_skus_context_var": "selected_product_skus",
                        "save_order_id_to": "created_order_id"
                    }
                }]
            },
            "transitions": [{"to_step": "query_new_order_details", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "query_new_order_details",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "newly_created_order",
                    "filters_template": {"id": "{{ created_order_id }}"},
                    "fields_to_return": ["amount", "currency"],
                    "limit": 1
                }]
            },
            "transitions": [{"to_step": "end_flow_quote_created", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_flow_quote_created",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {
                "body": "Thank you! We have created a price request for you with Order #{{ generated_order_number }}.\n\n*Total Amount: ${{ newly_created_order.0.amount }} {{ newly_created_order.0.currency }}*\n\nA sales agent will contact you shortly with payment options."
            }}},
            "transitions": []
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Thank you! Your installation request has been submitted. Our team will contact you shortly to confirm the schedule."}}
            },
            "transitions": []
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Your installation request has been cancelled. Type 'menu' to start over."}}
            },
            "transitions": []
        },
        {
            "name": "handle_no_services_available",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I'm sorry, it seems there are no installation services available for quoting at the moment. I'm connecting you with a support agent who can assist you further.",
                "notification_details": "Installation Flow: User asked for a price, but no 'service' type products were found in the database to offer."
            },
            "transitions": []
        },
        {
            "name": "handle_payment_not_found",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I couldn't verify the payment for order number '{{ order_number }}'. I'm connecting you with a support agent to assist you.",
                "notification_details": "Installation Flow: Could not verify payment for order #{{ order_number }}."
            },
            "transitions": []
        },
        {
            "name": "handle_order_not_paid",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I found your order '{{ order_number }}', but it looks like the payment is still pending or the order is not yet finalized. I'm connecting you with a support agent who can help you complete it.",
                "notification_details": "Installation Flow: Order #{{ order_number }} found, but payment_status is '{{ found_order.0.payment_status }}', not 'paid'."
            },
            "transitions": []
        },
        {
            "name": "handle_assessment_not_found",
            "type": "human_handover",
            "config": {
                "pre_handover_message_text": "I couldn't find a record for assessment number '{{ assessment_number }}'. I'm connecting you with a support agent to help.",
                "notification_details": "Installation Flow: Could not find assessment #{{ assessment_number }}."
            },
            "transitions": []
        }
    ]
}