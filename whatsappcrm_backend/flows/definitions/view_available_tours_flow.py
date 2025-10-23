# whatsappcrm_backend/flows/definitions/view_available_tours_flow.py

VIEW_AVAILABLE_TOURS_FLOW = {
    "name": "view_available_tours_flow",
    "friendly_name": "View Available Tours",
    "description": "Displays a list of available tours to the user.",
    "trigger_keywords": ["view tours", "show tours", "safaris"],
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
                    "fields_to_return": ["id", "name", "base_price", "duration_days"],
                    "order_by": ["name"]
                }]
            },
            "transitions": [
                {"to_step": "display_tours", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "available_tours.0"}},
                {"to_step": "no_tours_available", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_tours",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": """Here are our available safari packages:

{% for tour in available_tours %}
*{{ tour.name }}*
Duration: {{ tour.duration_days }} days
Price: ${{ "%.2f"|format(tour.base_price) }}
---
{% endfor %}

To book or ask for a custom trip, please type *menu* and choose 'Plan a Custom Tour'."""
                }
            },
            "transitions": [{"to_step": "end_view_tours", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "no_tours_available",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "We are currently updating our tour packages. Please check back soon or type 'menu' to contact an agent for a custom tour."}
            },
            "transitions": [{"to_step": "end_view_tours", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_view_tours",
            "type": "end_flow"
        }
    ]
}