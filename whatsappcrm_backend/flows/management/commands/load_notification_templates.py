# whatsappcrm_backend/flows/management/commands/load_notification_templates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
NOTIFICATION_TEMPLATES = [
    {
        "name": "new_order_created",
        "description": "Sent to admins when a new booking is created via a signal.",
        "template_type": "whatsapp",
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
        "body": """Admin Action: New Order & Install Created 📝

Admin *{{ contact.name or contact.username }}* has created a new booking.
*Customer:* {{ target_contact.0.name or customer_whatsapp_id }}
*Booking Ref:* {{ booking_ref }}
*Tour Name:* {{ tour_name }}

Please see the admin panel for full details."""
    },
    {
        "name": "job_card_created_successfully",
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
        "body": """Invoice Processed Successfully ✅

A booking confirmation from *{{ attachment.sender }}* (Filename: *{{ attachment.filename }}*) has been processed.

*Order Details:*
- Booking Ref: *{{ booking.reference }}*
- Total Amount: *${{ "%.2f"|format(booking.amount) if booking.amount is not none else '0.00' }}*
- Customer: *{{ customer.full_name or customer.contact_name }}*

The new order has been created in the system."""
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


class Command(BaseCommand):
    help = 'Loads or updates predefined notification templates from a definition list.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load notification templates...")
        
        for template_def in NOTIFICATION_TEMPLATES:
            template_name = template_def['name']
            
            template, created = NotificationTemplate.objects.update_or_create(
                name=template_name,
                defaults={
                    'description': template_def.get('description', ''),
                    'message_body': template_def.get('body', ''),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created new template: '{template_name}'"))
            else:
                self.stdout.write(f"  Updated existing template: '{template_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully loaded all notification templates."))