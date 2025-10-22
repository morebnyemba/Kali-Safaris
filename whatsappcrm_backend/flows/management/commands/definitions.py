# whatsappcrm_backend/notifications/definitions.py

"""
Central repository for all notification template definitions.
These definitions are used by:
1. `load_notification_templates` management command to populate the NotificationTemplate model.
2. `sync_meta_templates` management command to sync with the WhatsApp Business API.
"""

NOTIFICATION_TEMPLATES = [
    {
        "name": "new_order_created",
        "description": "Sent to admins when a new booking is created via a signal.",
        "body": """New Booking Confirmed! 🦒

A new booking has been created for customer *{{ booking.customer.get_full_name or booking.customer.contact.name }}*.

- Tour: *{{ booking.name }}*
- Booking Ref: *{{ booking.booking_reference }}*
- Amount: *${{ booking.total_amount or '0.00' }}*

Please see the admin panel for full details."""
    },
    {
        "name": "new_online_order_placed",
        "description": "Sent to admins when a customer places a new order through the 'Purchase Product' flow.",
        "body": """New Online Order Placed! 🛍️
New Tour Booking via WhatsApp! 🐘

A new booking has been made via WhatsApp by *{{ contact.name or contact.whatsapp_id }}*.

*Booking Details:*
- Booking Ref: *{{ created_booking_details.reference }}*
- Total Amount: *${{ created_booking_details.amount }}*
- Payment Status: Pending

*Lead Guest:*
- Name: {{ lead_guest_name }}
- Phone: {{ lead_guest_phone }}

*Items Ordered:*
{% for item in cart_items %}- {{ item.quantity }} x {{ item.name }}
{% endfor %}

Please follow up with the customer to arrange payment."""
    },
    {
        "name": "order_payment_status_updated",
        "description": "Sent to a customer when an admin updates their order's payment status.",
        "body": """Hello! 👋

The payment status for your booking '{{ booking_name }}' (Ref: {{ booking_reference }}) has been updated to: *{{ new_status }}*.

Thank you for choosing us!"""
    },
    {
        "name": "assessment_status_updated",
        "description": "Sent to a customer when an admin updates their site assessment status.",
        "body": """Hello! 👋
The status for your Itinerary Request (#{{ request_id }}) has been updated to: *{{ new_status }}*.

Our team will be in touch with the next steps. Thank you!"""
    },
    {
        "name": "new_installation_request",
        "description": "Sent to admins when a customer submits a new solar installation request.",
        "body": """New Installation Request 🛠️
New Tour Inquiry! 🦁

A new tour inquiry has been submitted by *{{ contact.name or contact.whatsapp_id }}*.

*Inquiry Details:*
- Tour Type: {{ tour_type }}
- Destination: {{ destination }}
- Number of Travelers: {{ number_of_travelers }}

*Contact Info:*
- Name: {{ full_name }}
- Phone: {{ phone }}
- Preferred Travel Dates: {{ travel_dates }}

Please follow up to create a custom itinerary."""
    },
    {
        "name": "new_starlink_installation_request",
        "description": "Sent to admins when a customer submits a new Starlink installation request.",
        "body": """New Starlink Installation Request 🛰️

A new Starlink installation request has been submitted by *{{ contact.name or contact.whatsapp_id }}*.

*Client & Location:*
- Name: {{ install_full_name }}
- Phone: {{ install_phone }}
- Address: {{ install_address }}
{% if install_location_pin and install_location_pin.latitude %}- Location Pin: https://www.google.com/maps/search/?api=1&query={{ install_location_pin.latitude }},{{ install_location_pin.longitude }}{% endif %}

*Scheduling:*
- Preferred Date: {{ install_datetime }} ({{ install_availability|title }})

*Job Details:*
- Kit Type: {{ install_kit_type|title }}
- Desired Mount: {{ install_mount_location }}

Please follow up to confirm the schedule."""
    },
    {
        "name": "new_solar_cleaning_request",
        "description": "Sent to admins when a customer submits a new solar panel cleaning request.",
        "body": """New Solar Cleaning Request 💧

A new cleaning request has been submitted by *{{ contact.name or contact.whatsapp_id }}*.

*Client Details:*
- Name: {{ cleaning_full_name }}
- Phone: {{ cleaning_phone }}

*Job Details:*
- Roof Type: {{ cleaning_roof_type|title }}
- Panels: {{ cleaning_panel_count }} x {{ cleaning_panel_type|title }}
- Preferred Date: {{ cleaning_date }} ({{ cleaning_availability|title }})
- Address: {{ cleaning_address }}{% if cleaning_location_pin and cleaning_location_pin.latitude %}
- Location Pin: https://www.google.com/maps/search/?api=1&query={{ cleaning_location_pin.latitude }},{{ cleaning_location_pin.longitude }}{% endif %}

Please follow up to provide a quote and schedule the service."""
    },
    {
        "name": "admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new order and installation request via the admin flow.",
        "body": """Admin Action: New Booking Created 📝

Admin *{{ contact.name or contact.username }}* has created a new booking.
*Customer:* {{ target_contact.0.name or customer_whatsapp_id }}
*Booking Ref:* {{ booking_ref }}
*Tour Name:* {{ tour_name }}
 
Please see the admin panel for full details."""
    },
    {
        "name": "new_site_assessment_request",
        "description": "Sent to admins when a customer books a new site assessment.",
        "body": """New Site Assessment Request 📋

A new site assessment has been requested by *{{ contact.name or contact.whatsapp_id }}*.

*Request Details:*
- Name: {{ assessment_full_name }}
- Company: {{ assessment_company_name }}
- Address: {{ assessment_address }}
- Contact: {{ assessment_contact_info }}
- Preferred Day: {{ assessment_preferred_day }}

Please follow up to schedule the assessment."""
    },
    {
        "name": "job_card_created_successfully",
        "description": "Sent to admins when a booking is successfully created from an email attachment.",
        "body": """New Booking Created from Email 🦁

A new booking has been automatically created from an email attachment.

*Booking Ref*: {{ booking.reference }}
*Customer*: {{ customer.first_name }} {{ customer.last_name }}
*Tour*: {{ booking.tour_name }}
*Start Date*: {{ booking.start_date }}

Please review the booking in the admin panel."""
    },
    {
        "name": "human_handover_flow",
        "description": "Sent to admins when a user is handed over to a human agent by the flow engine.",
        "body": """Human Intervention Required ⚠️

Contact *{{ related_contact.name or related_contact.whatsapp_id }}* requires assistance.

*Reason:*
{{ template_context.last_bot_message or 'User requested help or an error occurred.' }}

Please respond to them in the main inbox."""
    },
    {
        "name": "new_placeholder_order_created",
        "description": "Sent to admins when a placeholder order is created via the order receiver number.",
        "body": """New Placeholder Order Created 📦

A new placeholder order has been created by *{{ contact.name or contact.whatsapp_id }}*.

*Order #:* {{ normalized_order_number }}

Please update the order details in the admin panel as soon as possible."""
    },
    {
        "name": "message_send_failure",
        "description": "Sent to admins when a WhatsApp message fails to send.",
        "body": """Message Send Failure ⚠️

Failed to send a message to *{{ related_contact.name or related_contact.whatsapp_id }}*.

*Reason:* {{ template_context.message.error_details or 'Unknown error' }}

Please check the system logs for more details."""
    },
    {
        "name": "admin_24h_window_reminder",
        "description": "Sent to an admin user when their 24-hour interaction window is about to close.",
        "body": """Hi {{ recipient.first_name or recipient.username }},

This is an automated reminder. Your 24-hour interaction window for receiving system notifications on WhatsApp is closing soon.

Please reply with "status" or any other command to keep the window open."""
    },
    {
        "name": "invoice_processed_successfully",
        "description": "Sent to admins when a booking confirmation from an email has been successfully processed.",
        "body": """Booking Processed Successfully ✅

A booking confirmation from *{{ attachment.sender }}* (Filename: *{{ attachment.filename }}*) has been processed.

*Booking Details:*
- Booking Ref: *{{ booking.reference }}*
- Total Amount: *${{ "%.2f"|format(booking.amount) if booking.amount is not none else '0.00' }}*
- Customer: *{{ customer.full_name or customer.contact_name }}*

The new order has been created in the system."""
    },
]