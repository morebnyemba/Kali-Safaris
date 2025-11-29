# whatsappcrm_backend/flows/definitions/admin_main_menu_flow.py

ADMIN_MAIN_MENU_FLOW = {
    "name": "admin_main_menu",
    "friendly_name": "Admin: Main Menu",
    "description": "A secure gateway menu for all administrative flows.",
    "trigger_keywords": ["admin", "management", "admin menu"],
    "is_active": True,
    "steps": [
        {
            "name": "start_admin_menu",
            "is_entry_point": True,
            "type": "action",
            "config": {"actions_to_run": []},
            "transitions": [
                {
                    "to_step": "display_admin_menu",
                    "priority": 0,
                    "condition_config": {"type": "contact_is_admin"}
                },
                {
                    "to_step": "handle_not_admin",
                    "priority": 1,
                    "condition_config": {"type": "always_true"}
                }
            ]
        },
        {
            "name": "display_admin_menu",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": "Admin Menu"},
                        "body": {"text": "Welcome, {{ contact.name }}. Please select an administrative task:"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "update_order", "title": "🔄 Update Order Status"}},
                                {"type": "reply", "reply": {"id": "update_assessment", "title": "📋 Update Assessment"}},
                                {"type": "reply", "reply": {"id": "update_warranty_claim", "title": "🛡️ Update Warranty Claim"}},
                                {"type": "reply", "reply": {"id": "exit", "title": "Exit"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "admin_choice"}
            },
            "transitions": [
                {"to_step": "switch_to_update_order", "condition_config": {"type": "interactive_reply_id_equals", "value": "update_order"}},
                {"to_step": "switch_to_update_assessment", "condition_config": {"type": "interactive_reply_id_equals", "value": "update_assessment"}},
                {"to_step": "switch_to_update_warranty_claim", "condition_config": {"type": "interactive_reply_id_equals", "value": "update_warranty_claim"}},
                {"to_step": "end_admin_menu", "condition_config": {"type": "interactive_reply_id_equals", "value": "exit"}},
            ]
        },
        {
            "name": "switch_to_update_order",
            "type": "switch_flow",
            "config": {"target_flow_name": "admin_update_order_status"}
        },
        {
            "name": "switch_to_update_assessment",
            "type": "switch_flow",
            "config": {"target_flow_name": "admin_update_assessment_status"}
        },
        {
            "name": "switch_to_update_warranty_claim",
            "type": "switch_flow",
            "config": {"target_flow_name": "admin_update_warranty_claim"}
        },
        {
            "name": "handle_not_admin",
            "type": "end_flow",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "Sorry, I didn't understand that. Type 'menu' to see available options."}
                }
            }
        },
        {
            "name": "end_admin_menu",
            "type": "end_flow",
            "config": {"message_config": {"message_type": "text", "text": {"body": "Exiting admin menu."}}}
        }
    ]
}