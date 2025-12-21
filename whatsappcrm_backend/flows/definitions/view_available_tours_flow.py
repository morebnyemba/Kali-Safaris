# whatsappcrm_backend/flows/definitions/view_available_tours_flow.py

VIEW_AVAILABLE_TOURS_FLOW = {
    "name": "view_available_tours_flow",
    "friendly_name": "View Available Tours",
    "description": "Displays a list of available tours to the user.",
    "trigger_keywords": ["view tours", "show tours", "safaris"],
    "is_active": True,
    "steps": [
        {
                # Placeholder for missing step: switch_to_main_menu (if not already present)
                # (No action needed if already present)
            "name": "query_tours",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "query_model",
                        "app_label": "products_and_services",
                        "model_name": "Tour",
                        "variable_name": "available_tours",
                        "filters_template": {"is_active": True},
                        "fields_to_return": [
                            "id",
                            "name",
                            "base_price",
                            "duration_value",
                            "duration_unit",
                            "duration_days",
                            "description"
                        ],
                        "order_by": ["name"]
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "tour_index",
                        "value_template": 0
                    }
                ]
            },
            "transitions": [
                {"to_step": "resolve_tour_price", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "available_tours.0"}},
                {"to_step": "no_tours_available", "priority": 2, "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "resolve_tour_price",
            "type": "action",
            "config": {
                "actions_to_run": [
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "today_date",
                        "value_template": "{{ now().strftime('%Y-%m-%d') }}"
                    },
                    {
                        "action_type": "query_model",
                        "app_label": "products_and_services",
                        "model_name": "SeasonalTourPrice",
                        "variable_name": "current_seasonal_price",
                        "filters_template": {
                            "tour_id": "{{ available_tours[tour_index|int].id }}",
                            "start_date__lte": "{{ today_date }}",
                            "end_date__gte": "{{ today_date }}",
                            "is_active": True
                        },
                        "fields_to_return": ["price_per_adult", "price_per_child"],
                        "limit": 1
                    },
                    {
                        "action_type": "set_context_variable",
                        "variable_name": "display_price_per_adult",
                        "value_template": "{{ (current_seasonal_price.0.price_per_adult if current_seasonal_price and current_seasonal_price.0.price_per_adult is not none else available_tours[tour_index|int].base_price) }}"
                    }
                ]
            },
            "transitions": [
                {"to_step": "display_single_tour", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_single_tour",
            "type": "question",
            "config": {
                "message_config": {
                    "message_type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {
                            "type": "text",
                            "text": "Tour {{ tour_index|int + 1 }} of {{ available_tours | length }}"
                        },
                        "body": {
                            "text": """*{{ available_tours[tour_index|int].name }}*\n\n{{ available_tours[tour_index|int].description | striptags | replace('\r\n', '\n') | replace('\r', '\n') | trim }}\n\nDuration: {{ available_tours[tour_index|int].duration_value }} {{ available_tours[tour_index|int].duration_unit }}{% if available_tours[tour_index|int].duration_value|int > 1 %}s{% endif %}.\nPrice from: *${{ '%.2f'|format(display_price_per_adult|float) }}*."""
                        },
                        "footer": {
                            "text": "Select an option below"
                        },
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "book_this_tour", "title": "Book This Tour"}},
                                {"type": "reply", "reply": {"id": "view_next_tour", "title": "{% if tour_index|int + 1 < available_tours|length %}Next Tour ➡️{% else %}Back to Start 🔄{% endif %}"}},
                                {"type": "reply", "reply": {"id": "back_to_menu", "title": "Main Menu"}}
                            ]
                        }
                    }
                },
                "reply_config": {"expected_type": "interactive_id", "save_to_variable": "tour_choice"}
            },
            "transitions": [
                {"to_step": "start_booking_inquiry", "priority": 0, "condition_config": {"type": "interactive_reply_id_equals", "value": "book_this_tour"}},
                {"to_step": "increment_tour_index", "priority": 1, "condition_config": {"type": "interactive_reply_id_equals", "value": "view_next_tour"}},
                {"to_step": "switch_to_main_menu", "priority": 2, "condition_config": {"type": "interactive_reply_id_equals", "value": "back_to_menu"}},
                {"to_step": "tour_fallback_support", "priority": 3, "condition_config": {"type": "invalid_or_no_selection"}}
            ]
        },
        # Fallback/support step if user input is invalid
        {
            "name": "tour_fallback_support",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "If you need help or want to see the tours again, type 'menu' or contact bookings@kalaisafaris.com."}
            },
            "transitions": [
                {"to_step": "switch_to_main_menu", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "increment_tour_index",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "set_context_variable",
                    "variable_name": "tour_index",
                    "value_template": "{{ (tour_index|int + 1) % (available_tours | length) }}"
                }]
            },
            "transitions": [
                {"to_step": "resolve_tour_price", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "start_booking_inquiry",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "booking_flow",
                "initial_context_template": {
                    "tour_name": "{{ available_tours[tour_index|int].name }}",
                    "tour_id": "{{ available_tours[tour_index|int].id }}",
                    "tour_base_price": "{{ available_tours[tour_index|int].base_price }}",
                    "tour_duration_value": "{{ available_tours[tour_index|int].duration_value }}",
                    "tour_duration_unit": "{{ available_tours[tour_index|int].duration_unit }}"
                }
            }
        },
        {
            "name": "switch_to_main_menu",
            "type": "switch_flow",
            "config": {
                "target_flow_name": "main_menu"
            }
        },
        {
            "name": "no_tours_available",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "We are currently updating our tour packages. Please check back soon or type 'menu' to contact an agent for a custom tour." }
            },
            "transitions": [{"to_step": "end_view_tours", "condition_config": {"type": "always_true"}}]
        },
        {
            "name": "end_view_tours",
            "type": "end_flow"
        }
    ]
}