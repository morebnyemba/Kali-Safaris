# whatsappcrm_backend/flows/definitions/view_available_tours_flow.py

VIEW_AVAILABLE_TOURS_FLOW = {
    "name": "view_available_tours_flow",
    "friendly_name": "View Available Tours",
    "description": "Displays a list of available tours to the user.",
    "trigger_keywords": ["tours", "view tours", "available tours"],
    "is_active": True,
    "steps": [
        {
            "name": "query_tours",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "Tour",
                    "variable_name": "available_tours",
                    "filters_template": {"is_active": True},
                    "fields_to_return": ["id", "name", "description", "duration_days", "location", "image"],
                    "order_by": ["name"]
                }]
            },
            "transitions": [
                {"to_step": "display_tours", "priority": 0, "condition_config": {"type": "variable_exists", "variable_name": "available_tours.0"}},
                {"to_step": "no_tours_found", "priority": 1, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_tours",
            "type": "send_message",
            "config": {
                "message_type": "interactive",
                "interactive": {
                    "type": "carousel",
                    "action": {
                        "name": "tour_carousel",
                        "parameters": {
                            "cards": [
                                {
                                    "card_index": "{{ loop.index0 }}",
                                    "components": [
                                        {
                                            "type": "header",
                                            "parameters": [{"type": "image", "image": {"link": "{{ item.image }}"}}]
                                        },
                                        {
                                            "type": "body",
                                            "parameters": [
                                                {"type": "text", "text": "{{ item.name | truncatewords(10) }}"},
                                                {"type": "text", "text": "{{ item.description | truncatewords(15) }}"}
                                            ]
                                        }
                                    ]
                                } for item in available_tours
                            ]
                        }
                    }
                }
            },
            "transitions": [
                {"to_step": "end_flow", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "no_tours_found",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "We don't have any tours listed at the moment, but our travel experts are always creating new experiences! Please check back soon or contact an agent for a custom tour.\n\nType 'menu' to return."}
            },
            "transitions": [
                {"to_step": "end_flow", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_flow",
            "type": "end_flow",
            "config": {}
        }
    ]
}