# whatsappcrm_backend/flows/management/commands/load_notification_templates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
NOTIFICATION_TEMPLATES = [
    {
        "name": "hanna_new_tour_inquiry",
        "description": "Sent to admins when a new tour inquiry is created.",
        "template_type": "whatsapp",
        "body": """New Tour Inquiry! ✈️

A new tour inquiry has been submitted by *{{ customer.get_full_name or customer.contact.name }}*.

- Destinations: *{{ destinations }}*
- Preferred Dates: *{{ preferred_dates }}*
- Travelers: *{{ number_of_travelers }}*

Please see the admin panel for full details and follow up.""",
        "buttons": [
            {"type": "URL", "text": "View Inquiry", "url": "https://backend.kali-safaris.com/admin/customer_data/tourinquiry/{{ inquiry.id }}/change/"}
        ]
    },
    {
        "name": "hanna_new_booking_created",
        "description": "Sent to admins when a new booking is created.",
        "template_type": "whatsapp",
        "body": """New Booking Confirmed! 🎫

A new booking has been created for *{{ booking.customer.get_full_name or booking.customer.contact.name }}*.

- Booking Ref: *{{ booking.booking_reference }}*
- Tour: *{{ booking.tour_name }}*
- Dates: *{{ booking.start_date|strftime('%d %b %Y') }}* to *{{ booking.end_date|strftime('%d %b %Y') }}*
- Amount: *${{ booking.total_amount }}*

Please see the admin panel for full details.""",
        "buttons": [
            {"type": "URL", "text": "View Booking", "url": "https://backend.kali-safaris.com/admin/customer_data/booking/{{ booking.id }}/change/"}
        ]
    },
    {
        "name": "hanna_human_handover_flow",
        "description": "Sent to admins when a user is handed over to a human agent by the flow engine.",
        "template_type": "whatsapp",
        "body": """Human Intervention Required ⚠️

Contact *{{ related_contact_name }}* requires assistance.

*Reason:*
{{ last_bot_message }}

Please respond to them in the main inbox.""",
        "buttons": [
            {"type": "QUICK_REPLY", "text": "Acknowledge"},
            {"type": "URL", "text": "View Conversation", "url": "https://backend.kali-safaris.com/admin/conversations/contact/{{ related_contact.id }}/change/"}
        ]
    },
    {
        "name": "hanna_message_send_failure",
        "description": "Sent to admins when a WhatsApp message fails to send.",
        "template_type": "whatsapp",
        "body": """Message Send Failure ⚠️

Failed to send a message to *{{ related_contact_name }}*.

*Reason:* {{ error_details }}

Please check the system logs for more details."""
    },
    {
        "name": "hanna_admin_24h_window_reminder",
        "description": "Sent to an admin user when their 24-hour interaction window is about to close.",
        "template_type": "whatsapp",
        "body": """Hi {{ recipient.first_name or recipient.username }},

This is an automated reminder. Your 24-hour interaction window for receiving system notifications on WhatsApp is closing soon.

Please reply with "status" or any other command to keep the window open.""",
        "buttons": [
            {"type": "QUICK_REPLY", "text": "Reply Now"}
        ]
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
                    'buttons': template_def.get('buttons', []),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created new template: '{template_name}'"))
            else:
                self.stdout.write(f"  Updated existing template: '{template_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully loaded all notification templates."))
