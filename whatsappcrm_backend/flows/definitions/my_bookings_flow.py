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
            "type": "question",
            "config": {
                "message_config": {"message_type": "text", "text": {"body": "To find your bookings, please enter the phone number you used to book, starting with +263..."}},
                "reply_config": {"expected_type": "text", "save_to_variable": "booking_lookup_phone"}
            },
            "transitions": [
                {"to_step": "find_and_show_bookings", "priority": 1, "condition_config": {"type": "variable_exists", "variable_name": "booking_lookup_phone"}}
            ]
        },
        {
            "name": "find_and_show_bookings",
            "type": "action",
            "config": {
                "actions_to_run": [{
                    "action_type": "query_model",
                    "app_label": "customer_data",
                    "model_name": "Booking",
                    "variable_name": "found_bookings",
                    "filters_template": {
                        "customer__contact__whatsapp_id": "{{ booking_lookup_phone | regex_replace('[^0-9]', '') }}"
                    },
                    "fields_to_return": ["booking_reference", "tour_name", "start_date", "payment_status"],
                    "order_by": ["-start_date"]
                }]
            },
            "transitions": [
                {"to_step": "display_no_bookings_found", "priority": 1, "condition_config": {"type": "variable_equals", "variable_name": "found_bookings", "value": "[]"}},
                {"to_step": "display_bookings", "priority": 2, "condition_config": {"type": "always_true"}}
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

Type *menu* to return to the main menu."""
                }
            },
            "transitions": [
                {"to_step": "end_my_bookings", "condition_config": {"type": "always_true"}}
            ]
        },
        {
            "name": "display_no_bookings_found",
            "type": "send_message",
            "config": {
                "message_type": "text", "text": {"body": "I couldn't find any bookings associated with that phone number. Please make sure you entered it correctly.\n\nType *menu* to try again or return to the main menu."}
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