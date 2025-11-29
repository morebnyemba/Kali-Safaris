# whatsappcrm_backend/flows/definitions/admin_update_order_status_flow.py

ADMIN_UPDATE_ORDER_STATUS_FLOW = {
    "name": "admin_update_order_status",
    "friendly_name": "Admin: Update Order Payment Status",
    "description": "An internal flow for admins to change the payment status of an existing order.",
    "trigger_keywords": ["update order", "payment status", "update payment"],
    "is_active": True,
    "steps": [
        {
            "name": "start_update_order",
            "is_entry_point": True,
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "Let's update an order's payment status. Please enter the Order Number (e.g., 12345/PO)."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "target_order_number"}
            },
            "transitions": [{"to_step": "normalize_the_order_number", "condition_config": {"type": "variable_exists", "variable_name": "target_order_number"}}]
        },
        {
            "name": "normalize_the_order_number",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "normalize_order_number",
                    "params_template": {
                        "input_variable": "target_order_number",
                        "output_variable": "target_order_number",
                        "default_suffix": "PO"
                    }
                }]
            },
            "transitions": [
                {"to_step": "find_order", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "find_order",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Order",
                    "variable_name": "found_order",
                    "filters_template": {"order_number__iexact": "{{ target_order_number }}"},
                    "fields_to_return": ["id", "name", "amount", "payment_status", "customer_id"],
                    "limit": 1
                }]
            },
            "transitions": [{"to_step": "check_if_order_exists", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "check_if_order_exists",
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {"to_step": "get_customer_contact", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "found_order.0"}},
                {"to_step": "handle_order_not_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "get_customer_contact",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "conversations",
                    "model_name": "Contact",
                    "variable_name": "order_contact",
                    "filters_template": {"id": "{{ found_order.0.customer_id }}"},
                    "fields_to_return": ["id", "whatsapp_id"],
                    "limit": 1
                }]
            },
            "transitions": [{"to_step": "ask_for_new_status", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "ask_for_new_status",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Update Payment Status"},
                        "body": {"text": "Found Order: *{{ found_order.0.name }}*\nAmount: *${{ found_order.0.amount }}*\nCurrent Status: *{{ found_order.0.payment_status|title }}*\n\nPlease select the new payment status:"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "paid", "title": "✅ Mark as Paid"}},
                                {"type": "reply", "reply": {"id": "pending", "title": "⏳ Mark as Pending"}},
                                {"type": "reply", "reply": {"id": "partially_paid", "title": "Partial Payment"}},
                                {"type": "reply", "reply": {"id": "cancel_update", "title": "Cancel"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "new_payment_status"}
            },
            "transitions": [
                {"to_step": "end_flow_cancelled", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "cancel_update"}},
                {"to_step": "update_order_status", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "update_order_status",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "update_model_instance",
                        "app_label": "customer_data",
                        "model_name": "Order",
                        "instance_id_template": "{{ found_order.0.id }}",
                        "fields_to_update_template": {"payment_status": "{{ new_payment_status }}"}
                    },
                    {
                        "action_type": "send_group_notification",
                        "params_template": {
                            "template_name": "hanna_order_payment_status_updated",
                            "contact_ids": ["{{ order_contact.0.id }}"],
                            "template_context": {
                                "order_name": "{{ found_order.0.name }}",
                                "new_status": "{{ new_payment_status|title }}",
                                "order_number": "{{ found_order.0.order_number }}"
                            }
                        }
                    }
                ]
            },
            "transitions": [{"to_step": "end_flow_success", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "handle_order_not_found",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Sorry, I couldn't find an order with the number '{{ target_order_number }}'. Please check the number and try again."}}}
        },
        {
            "name": "end_flow_cancelled",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Order update cancelled."}}}
        },
        {
            "name": "end_flow_success",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Success! The payment status for order '{{ found_order.0.name }}' has been updated to *{{ new_payment_status|title }}*.\n\nThe customer has been notified."}
                }
            }
        }
    ]
}