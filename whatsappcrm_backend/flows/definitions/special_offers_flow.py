# whatsappcrm_backend/flows/definitions/special_offers_flow.py

SPECIAL_OFFERS_FLOW = {
    "name": "special_offers_flow",
    "friendly_name": "Special Offers",
    "description": "Displays current special offers to the user.",
    "trigger_keywords": ["offers", "deals", "specials"],
    "is_active": True,
    "steps": [
        {
            "name": "query_offers",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "products_and_services",
                    "model_name": "SpecialOffer",
                    "variable_name": "active_offers",
                    "filters_template": {
                        "is_active": True,
                        "valid_until__gte": "{{ now() | strftime('%Y-%m-%d') }}"
                    },
                    "fields_to_return": ["title", "description", "valid_until"],
                    "order_by": ["-valid_until"]
                }]
            },
            "transitions": [
                {"to_step": "display_offers", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "active_offers.0"}},
                {"to_step": "no_offers_available", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_offers",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {
                        "body": """We have the following special offers available:

{% for offer in active_offers %}
*{{ offer.title }}*
{{ offer.description }}
_Valid until: {{ offer.valid_until | strftime('%B %d, %Y') }}_
---
{% endfor %}

Type *menu* to return to the main menu."""
                    }
                }
            },
            "transitions": [{"to_step": "end_offers_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "no_offers_available",
            "type": "send_message",
            "config": {
                "message_config": {
                    "message_type": "text",
                    "text": {"body": "There are no special offers available at the moment. Please check back later!\n\nType *menu* to return to the main menu."}
                }
            },
            "transitions": [{"to_step": "end_offers_flow", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_offers_flow",
            "type": "end_flow"
        }
    ]
}