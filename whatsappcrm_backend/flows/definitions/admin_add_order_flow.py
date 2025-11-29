# whatsappcrm_backend/flows/definitions/admin_add_order_flow.py

ADMIN_ADD_ORDER_FLOW = {
    "name": "admin_add_order",
    "friendly_name": "Admin: Add New Order & Installation",
    "description": "An internal flow for admins to create a new order, add items, and book the installation for a customer.",
    "trigger_keywords": ["add order", "new order", "create order"],
    "is_active": True,
    "steps": [
        {
            "name": "start_add_order",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Let's add a new order. What is the customer's WhatsApp number? (e.g., 263...)"}},
                "reply_config": {
                    "expected_type": "text", "save_to_variable": "customer_whatsapp_id"
                }
            },
            "transitions": [
                {"to_step": "find_contact", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "customer_whatsapp_id"}}
            ]
        },
        {
            "name": "find_contact",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "conversations",
                    "model_name": "Contact",
                    "variable_name": "target_contact",
                    "filters_template": {"whatsapp_id": "{{ customer_whatsapp_id }}"},
                    "fields_to_return": ["id", "name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_if_contact_exists", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_contact_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "get_customer_profile", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "target_contact.0"}},
                {"to_step": "ask_new_contact_name", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_new_contact_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "This is a new customer. What is their full name?"}},
                "reply_config": {
                    "expected_type": "text",
                    "save_to_variable": "new_customer_full_name",
                    "validation_regex": "^.{3,}"
                },
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid name."}
            },
            "transitions": [
                {"to_step": "create_contact_and_profile", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "new_customer_full_name"}}
            ]
        },
        {
            "name": "create_contact_and_profile",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "conversations",
                        "model_name": "Contact",
                        "fields_template": {
                            "whatsapp_id": "{{ customer_whatsapp_id }}",
                            "name": "{{ new_customer_full_name }}"
                        },
                        "save_to_variable": "created_contact_instance"
                    },
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "CustomerProfile",
                        "fields_template": {
                            "contact_id": "{{ created_contact_instance.id }}",
                            "first_name": "{{ new_customer_full_name.split(' ')[0] if ' ' in new_customer_full_name else new_customer_full_name }}",
                            "last_name": "{{ ' '.join(new_customer_full_name.split(' ')[1:]) if ' ' in new_customer_full_name else '' }}"
                        },
                        "save_to_variable": "created_profile_instance"
                    }
                ]
            },
            "transitions": [
                {"to_step": "ask_order_number", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "get_customer_profile",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "query_model",
                        "app_label": "customer_data",
                        "model_name": "CustomerProfile",
                        "variable_name": "target_customer_profile",
                        "filters_template": {"contact_id": "{{ target_contact.0.id }}"},
                        "fields_to_return": ["contact"],
                        "limit": 1
                    }
                ]
            },
            "transitions": [
                {"to_step": "check_if_profile_exists", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_profile_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_order_number", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "target_customer_profile.0"}},
                {"to_step": "create_customer_profile", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "create_customer_profile",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "create_model_instance",
                        "app_label": "customer_data",
                        "model_name": "CustomerProfile",
                        "fields_template": {"contact_id": "{{ target_contact.0.id }}"},
                        "save_to_variable": "created_profile_instance"
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "target_customer_profile",
                        "value_template": "[{{ created_profile_instance }}]"
                    }
                ]
            },
            "transitions": [
                {"to_step": "ask_order_number", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_order_number",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Customer profile is ready. What is the Order Number for this transaction?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "order_number_ref"},
            },
            "transitions": [
                {"to_step": "ask_order_description", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "order_number_ref"}}
            ]
        },
        {
            "name": "ask_order_description",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Please provide a short description for this order (e.g., '5kVA Solar Kit for Mr. Smith'). This will be the order name."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "order_description"},
            },
            "transitions": [
                {"to_step": "create_initial_order", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "order_description"}}
            ]
        },
        {
            "name": "create_initial_order",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "fields_template": {
                        "customer_id": "{{ target_customer_profile.0.contact_id if target_customer_profile else created_profile_instance.contact }}",
                        "order_number": "{{ order_number_ref }}/PO",
                        "name": "{{ order_description }}",
                        "stage": "closed_won",
                        "payment_status": "paid",
                        "amount": "0.00",
                        "notes": "Order created by admin {{ contact.name or contact.username }}. Items added via flow."
                    },
                    "save_to_variable": "created_order"
                }]
            },
            "transitions": [
                {"to_step": "ask_product_sku_loop", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "created_order.id"}}
            ]
        },
        {
            "name": "ask_product_sku_loop",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Order '{{ order_description }}' created. Let's add products.\n\nEnter the SKU for the first product, or type 'done' to finish."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "product_sku"},
            },
            "transitions": [
                {"to_step": "calculate_and_update_order_total", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "query_product_loop", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "query_product_loop",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Product",
                    "variable_name": "found_product",
                    "filters_template": {"sku__iexact": "{{ product_sku }}"},
                    "fields_to_return": ["id", "price", "name"],
                    "limit": 1
                }]
            },
            "transitions": [
                {"to_step": "check_if_product_exists_loop", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "check_if_product_exists_loop",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "ask_quantity_loop", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_product.0"}},
                {"to_step": "handle_no_product_found_loop", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "handle_no_product_found_loop",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Product with SKU '{{ product_sku }}' not found. Please enter another SKU, or type 'done' to finish."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "product_sku"},
            },
            "transitions": [
                {"to_step": "calculate_and_update_order_total", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "query_product_loop", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_quantity_loop",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Product '{{ found_product.0.name }}' found. How many units?"}},
                "reply_config": {"expected_type": "number", "save_to_variable": "product_quantity"},
            },
            "transitions": [
                {"to_step": "create_order_item_loop", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "product_quantity"}}
            ]
        },
        {
            "name": "create_order_item_loop",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_model_instance",
                    "app_label": "customer_data",
                    "model_name": "OrderItem",
                    "fields_template": {
                        "order_id": "{{ created_order.id }}",
                        "product_id": "{{ found_product.0.id }}",
                        "quantity": "{{ product_quantity }}",
                        "unit_price": "{{ found_product.0.price }}"
                    }
                }]
            },
            "transitions": [
                {"to_step": "ask_next_sku_loop", "priority": 0, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_next_sku_loop",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Added {{ product_quantity }} x {{ found_product.0.name }}. Enter the next product SKU, or type 'done' to finish."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "product_sku"},
            },
            "transitions": [
                {"to_step": "calculate_and_update_order_total", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "done"}},
                {"to_step": "query_product_loop", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "calculate_and_update_order_total",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "calculate_order_total", "params_template": {"order_id_context_var": "created_order.id", "save_to_variable": "final_order_amount"}},
                    {"action_type": "update_order_fields", "params_template": {"order_id_context_var": "created_order.id", "fields_to_update_template": {"amount": "{{ final_order_amount }}"}}}
                ]
            }, # Removed to step transition and moved to save instllation request
            "transitions": [{"to_step": "ask_installation_type", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_installation_type",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {"type": "button", "header": {"type": "text", "text": "Installation Details"}, "body": {"text": "Order details complete. Now, let's book the installation. Is this for a Residential or Commercial property?"}, "action": {"buttons": [{"type": "reply", "reply": {"id": "install_residential", "title": "Residential"}}, {"type": "reply", "reply": {"id": "install_commercial", "title": "Commercial"}}]}}
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "installation_type"}
            },
            "transitions": [{"to_step": "ask_branch", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_branch",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {"type": "list", "header": {"type": "text", "text": "Select Branch"}, "body": {"text": "Please select the branch handling this installation."}, "action": {"button": "Select Branch", "sections": [{"title": "Our Branches", "rows": [{"id": "Harare", "title": "Harare"}, {"id": "Bulawayo", "title": "Bulawayo"}, {"id": "Mutare", "title": "Mutare"}, {"id": "Other", "title": "Other"}]}, {"title": "Exit", "rows": [{"id": "cancel_install", "title": "Cancel Request"}]}]}}
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_branch"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_install"}},
                {"to_step": "ask_sales_person", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "ask_sales_person",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Who is the TV Sales Sales Person for this order?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_sales_person"}
            },
            "transitions": [{"to_step": "ask_client_name", "condition_config": {"type": "variable_exists", "variable_name": "install_sales_person"}}]
        },
        {
            "name": "ask_client_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Client Name as it appears on the invoice?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_full_name"}
            },
            "transitions": [{"to_step": "ask_client_phone", "condition_config": {"type": "variable_exists", "variable_name": "install_full_name"}}]
        },
        {
            "name": "ask_client_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Client's contact number?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_phone", "validation_regex": "^\\+?[1-9]\\d{8,14}$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid phone number (e.g., +263...)"}
            },
            "transitions": [{"to_step": "ask_alt_contact_name", "condition_config": {"type": "variable_exists", "variable_name": "install_phone"}}]
        },
        {
            "name": "ask_alt_contact_name",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Alternative Contact's Name? (Type 'N/A' if not applicable)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_alt_name"}
            },
            "transitions": [{"to_step": "ask_alt_contact_phone", "condition_config": {"type": "variable_exists", "variable_name": "install_alt_name"}}]
        },
        {
            "name": "ask_alt_contact_phone",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the Alternative Contact's Number? (Type 'N/A' if not applicable)"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_alt_phone", "validation_regex": "^(?i)(N/A|\\+?[1-9]\\d{8,14})$"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please enter a valid phone number or 'N/A'."}
            },
            "transitions": [{"to_step": "ask_install_date", "condition_config": {"type": "variable_exists", "variable_name": "install_alt_phone"}}]
        },
        {
            "name": "ask_install_date",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the customer's preferred installation date?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_datetime"}
            },
            "transitions": [{"to_step": "ask_availability", "condition_config": {"type": "variable_exists", "variable_name": "install_datetime"}}]
        },
        {
            "name": "ask_availability",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {"type": "button", "body": {"text": "What is the customer's preferred availability on that day?"}, "action": {"buttons": [{"type": "reply", "reply": {"id": "morning", "title": "Morning"}}, {"type": "reply", "reply": {"id": "afternoon", "title": "Afternoon"}}]}}
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_availability"}
            },
            "transitions": [{"to_step": "ask_install_address", "condition_config": {"type": "variable_exists", "variable_name": "install_availability"}}]
        },
        {
            "name": "ask_install_address",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "What is the full installation address?"}},
                "reply_config": {"expected_type": "text", "save_to_variable": "install_address", "validation_regex": "^.{10,}"},
                "fallback_config": {"action": "re_prompt", "max_retries": 2, "re_prompt_message_text": "Please provide a more detailed address."}
            },
            "transitions": [{"to_step": "ask_location_pin", "condition_config": {"type": "variable_exists", "variable_name": "install_address"}}]
        },
        {
            "name": "ask_location_pin",
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Please provide the customer's location pin for accurate directions.\n(You can type 'skip' to skip this step.)"}},
                "reply_config": {"expected_type": "location", "save_to_variable": "install_location_pin"}
            },
            "transitions": [
                {"to_step": "set_skipped_location", "priority": 0, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "skip"}},                {"to_step": "set_skipped_location", "priority": 1, "condition_config": {"type": "user_reply_matches_keyword", "keyword": "n/a"}},
                {"to_step": "confirm_installation_request", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "install_location_pin"}}
            ]
        },
        {
            "name": "set_skipped_location",
            "type": "action",
            "config": {
                "actions_to_run": [{"action_type": "set_context_variable", "variable_name": "install_location_pin", "value_template": {"latitude": None, "longitude": None}}]
            },
            "transitions": [{"to_step": "confirm_installation_request", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "confirm_installation_request",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": (
                            "Please review the details for this order and installation before submitting:\n\n"
                            "*Order #*: {{ order_number_ref }}/PO\n"
                            "*Order Name*: {{ order_description }}\n"
                            "*Branch*: {{ install_branch }}\n"
                            "*Sales Person*: {{ install_sales_person }}\n"
                            "*Client Name*: {{ install_full_name }}\n"
                            "*Client Contact*: {{ install_phone }}\n"
                            "*Alt. Contact*: {{ install_alt_name }} ({{ install_alt_phone }})\n"
                            "*Install Date*: {{ install_datetime }} ({{ install_availability|title }})\n"
                            "*Address*: {{ install_address }}"
                        )},
                        "action": {"buttons": [{"type": "reply", "reply": {"id": "confirm_install", "title": "Confirm & Submit"}}, {"type": "reply", "reply": {"id": "cancel_install", "title": "Cancel"}}]}
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "install_confirmation"}
            },
            "transitions": [
                {"to_step": "save_installation_request", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "confirm_install"}},
                {"to_step": "end_flow_cancelled", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "save_installation_request",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {"action_type": "create_model_instance", "app_label": "customer_data", "model_name": "InstallationRequest", "fields_template": {"customer_id": "{{ target_customer_profile.0.contact_id if target_customer_profile else created_profile_instance.contact }}", "associated_order_id": "{{ created_order.id }}", "installation_type": "{{ installation_type }}", "order_number": "{{ order_number_ref }}", "branch": "{{ install_branch }}", "sales_person_name": "{{ install_sales_person }}", "full_name": "{{ install_full_name }}", "address": "{{ install_address }}", "latitude": "{{ install_location_pin.latitude }}", "longitude": "{{ install_location_pin.longitude }}", "preferred_datetime": "{{ install_datetime }}", "availability": "{{ install_availability }}", "contact_phone": "{{ install_phone }}", "alternative_contact_name": "{{ install_alt_name }}", "alternative_contact_number": "{{ install_alt_phone }}"}, "save_to_variable": "created_installation_request"},
                    {"action_type": "send_group_notification", "params_template": {"group_names": ["Pfungwa Staff", "System Admins"], "template_name": "hanna_admin_order_and_install_created"}}
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
                    "text": {"body": "Success! Order '{{ order_description }}' and its installation request have been created for customer {{ customer_whatsapp_id }}. You can view the details in the admin panel."}
                }
            }
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Request cancelled."}}}
        }
    ]
}