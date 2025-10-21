# whatsappcrm_backend/flows/definitions/simple_add_order_flow.py

SIMPLE_ADD_ORDER_FLOW = {
    "name": "simple_add_order",
    "friendly_name": "Simple Add Order (Super Admin)",
    "description": "A restricted flow for a designated number to create a basic order shell by just sending the order number.",
    "trigger_keywords": [], # This flow is triggered by a special case in services.py, not by keywords.
    "is_active": True,
    "steps": [
        {
            "name": "start_simple_add_order",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "create_placeholder_order",
                    "params_template": {
                        "order_number": "{{ order_number_from_message }}"
                    }
                }]
            },
            "transitions": [
                {"to_step": "end_success", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_success",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "✅ Success! Order #{{ order_number_from_message }} has been created."}}}
        }
    ]
}