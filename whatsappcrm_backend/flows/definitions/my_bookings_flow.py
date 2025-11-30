# whatsappcrm_backend/flows/definitions/my_bookings_flow.py

MY_BOOKINGS_FLOW = {
    "name": "my_bookings_flow",
    "friendly_name": "My Bookings",
    "description": "Allows a user to check the status and details of their bookings.",
    "trigger_keywords": ["my bookings", "check booking"],
    "is_active": True,
    "steps": [
        {
            "name": "start_my_bookings",
            "is_entry_point": True,
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "variable_name": "found_bookings",
                    "filters_template": {
                        "customer_id": "{{ customer_profile.id }}"
                    },
                    "fields_to_return": ["booking_reference", "tour_name", "start_date", "payment_status"],
                    "order_by": ["-start_date"]
                }]
            },
            "transitions": [
                {"to_step": "display_no_bookings_found", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "found_bookings", "value": "[]"}},
                {"to_step": "display_bookings", "priority": 2, "condition_config": {"type": "variable_exists", "variable_name": "found_bookings.0"}}
            ]
        },
        {
            "name": "display_bookings",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {
                    "body": """Here are your upcoming bookings:

{% for booking in found_bookings %}
*Tour:* {{ booking.tour_name }}
*Reference:* {{ booking.booking_reference }}
*Start Date:* {{ booking.start_date | strftime('%A, %d %B %Y') }}
*Payment:* {{ booking.payment_status | title }}
---
{% endfor %}

Type *menu* to return to the main menu or contact bookings@kalaisafaris.com for help."""
                }
            },
            "transitions": [
                {"to_step": "end_my_bookings", "priority": 1, "condition_config": {"type": "always_true"}},
                {"to_step": "bookings_support", "priority": 2, "condition_config": {"type": "invalid_or_no_selection"}}
            ]
        },
        # Fallback/support step if user input is invalid
        {
            "name": "bookings_support",
            "type": "send_message",
            "config": {
                "message_type": "text",
                "text": {"body": "If you need help or want to see your bookings again, type 'menu' or contact bookings@kalaisafaris.com."}
            },
            "transitions": [
                {"to_step": "end_my_bookings", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_no_bookings_found",
            "type": "send_message",
            "config": {
                "message_type": "text", "text": {"body": "I couldn't find any bookings associated with your account.\n\nIf you booked using a different number, please contact an agent. Type *menu* to return to the main menu."}
            },
            "transitions": [
                {"to_step": "end_my_bookings", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "end_my_bookings",
            "type": "end_flow"
        }
    ]
}