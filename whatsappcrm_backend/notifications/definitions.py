# whatsappcrm_backend/notifications/definitions.py

"""
Central repository for all notification template definitions.
These definitions are used by the `load_notification_templates` management command.
"""

NOTIFICATION_TEMPLATES = [
    {
        "name": "new_booking_created",
        "description": "Sent to admins when a new booking is created via a signal.",
        "template_type": "whatsapp",
        "body": """New Booking Confirmed! 🦒

A new booking has been created for customer *{{ booking.customer.get_full_name or booking.customer.contact.name }}*.

- Tour: *{{ booking.tour_name }}*
- Booking Ref: *{{ booking.booking_reference }}*
- Amount: *${{ booking.total_amount or '0.00' }}*

Please see the admin panel for full details."""
    },
    {
        "name": "new_online_order_placed",
        "description": "Sent to admins when a customer places a new booking through a WhatsApp flow.",
        "template_type": "whatsapp",
        "body": """New Tour Booking via WhatsApp! 🐘

A new booking has been made via WhatsApp by *{{ contact.name or contact.whatsapp_id }}*.

*Booking Details:*
- Booking Ref: *{{ created_booking_details.reference }}*
- Total Amount: *${{ created_booking_details.amount }}*
- Payment Status: Pending

*Lead Guest:*
- Name: {{ lead_guest_name }}
- Phone: {{ lead_guest_phone }}

Please follow up with the customer to arrange payment."""
    },
    {
        "name": "order_payment_status_updated",
        "description": "Sent to a customer when an admin updates their order's payment status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The payment status for your booking '{{ booking_name }}' (Ref: {{ booking_reference }}) has been updated to: *{{ new_status }}*.

Thank you for choosing us!"""
    },
    {
        "name": "assessment_status_updated",
        "description": "Sent to a customer when an admin updates their itinerary request status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The status for your Itinerary Request (#{{ request_id }}) has been updated to: *{{ new_status }}*.

Our team will be in touch with the next steps. Thank you!"""
    },
    {
        "name": "admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new booking via an admin flow.",
        "template_type": "whatsapp",
        "body": """Admin Action: New Booking Created 📝

Admin *{{ contact.name or contact.username }}* has created a new booking.
*Customer:* {{ target_contact.0.name or customer_whatsapp_id }}
*Booking Ref:* {{ booking_ref }}
*Tour Name:* {{ tour_name }}

Please see the admin panel for full details."""
    },
    {
        "name": "booking_created_from_email",
        "description": "Sent to admins when a booking is successfully created from an email attachment.",
        "template_type": "whatsapp",
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
        "template_type": "whatsapp",
        "body": """Human Intervention Required ⚠️

Contact *{{ related_contact.name or related_contact.whatsapp_id }}* requires assistance.

*Reason:*
{{ template_context.last_bot_message or 'User requested help or an error occurred.' }}

Please respond to them in the main inbox."""
    },
    {
        "name": "message_send_failure",
        "description": "Sent to admins when a WhatsApp message fails to send.",
        "template_type": "whatsapp",
        "body": """Message Send Failure ⚠️

Failed to send a message to *{{ related_contact.name or related_contact.whatsapp_id }}*.

*Reason:* {{ template_context.message.error_details or 'Unknown error' }}

Please check the system logs for more details."""
    },
    {
        "name": "admin_24h_window_reminder",
        "description": "Sent to an admin user when their 24-hour interaction window is about to close.",
        "template_type": "whatsapp",
        "body": """Hi {{ recipient.first_name or recipient.username }},

This is an automated reminder. Your 24-hour interaction window for receiving system notifications on WhatsApp is closing soon.

Please reply with "status" or any other command to keep the window open."""
    },
    {
        "name": "invoice_processed_successfully",
        "description": "Sent to admins when a booking confirmation from an email has been successfully processed.",
        "template_type": "whatsapp",
        "body": """Booking Processed Successfully ✅

A booking confirmation from *{{ attachment.sender }}* (Filename: *{{ attachment.filename }}*) has been processed.

*Booking Details:*
- Booking Ref: *{{ booking.reference }}*
- Total Amount: *${{ "%.2f"|format(booking.amount) if booking.amount is not none else '0.00' }}*
- Customer: *{{ customer.full_name or customer.contact_name }}*

The new booking has been created in the system."""
    },
    {
        "name": "new_tour_inquiry_alert",
        "description": "Sent to admins when a new tour inquiry is submitted via the WhatsApp flow.",
        "template_type": "whatsapp",
        "body": """New Tour Inquiry! 🦁

A new tour inquiry has been submitted by *{{ contact.name or contact.whatsapp_id }}*.

*Inquiry Details:*
- Name: *{{ flow_context.inquiry_full_name }}*
- Destination: *{{ flow_context.inquiry_destination }}*
- Travelers: *{{ flow_context.inquiry_travelers }}*
- Dates: *{{ flow_context.inquiry_dates }}*
- Notes: {{ flow_context.inquiry_notes }}

Please follow up to create a custom itinerary. The inquiry has been saved to the CRM."""
    },
]
