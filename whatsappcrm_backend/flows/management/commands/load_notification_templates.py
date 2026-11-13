# whatsappcrm_backend/flows/management/commands/load_notification_templates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
# Staff alerts sent on WhatsApp. Names must match what the code queues; staff
# emails carry the same events with full detail (notifications/staff_alerts.py).
NOTIFICATION_TEMPLATES = [
    # --- Payments (notifications/staff_alerts.py) ---
    {
        "name": "staff_payment_received",
        "description": "Every successful payment, for finance to cross-reference. Full gateway details are in the staff email.",
        "template_type": "whatsapp",
        "body": """Payment received 💰

*{{ amount }}* via {{ method }}
Ref: {{ payment_reference }}

Booking *{{ booking_reference }}* · {{ customer }}
{{ tour_name }} · {{ start_date }}
Balance now: {{ balance }}

Full gateway details are in the staff email."""
    },
    {
        "name": "manual_payment_recorded_alert",
        "description": "A customer reported a bank transfer / manual payment that needs verifying.",
        "template_type": "whatsapp",
        "body": """Payment to verify 🧾

A customer reported *{{ amount }}* by {{ method }} for booking *{{ booking_reference }}*.

Check it reached the account, then approve or reject it under Payments → Awaiting verification."""
    },
    # --- Bookings ---
    {
        "name": "staff_booking_update",
        "description": "Booking events: new, confirmed, fully paid, awaiting details, on hold, rescheduled, cancelled, refunded.",
        "template_type": "whatsapp",
        "body": """{{ event }} 📋

Booking *{{ booking_reference }}* · {{ customer }}
{{ tour_name }} · {{ start_date }}
Status: {{ status }}

{{ details }}"""
    },
    {
        "name": "new_tour_inquiry_alert",
        "description": "A customer asked for a quote / custom tour on WhatsApp.",
        "template_type": "whatsapp",
        "body": """New tour inquiry ✈️

From: {{ contact }}
Tour: {{ tour_name or 'custom tour' }}
Dates: {{ start_date or 'not given' }}

Follow up from Tour inquiries in the dashboard."""
    },
    {
        "name": "invoice_processed_successfully",
        "description": "A partner's emailed booking document was read and turned into a booking.",
        "template_type": "whatsapp",
        "body": """Booking imported from email 📧

{{ attachment.filename }} from {{ attachment.sender }}
Booking *{{ booking.reference }}* · {{ booking.tour_name }} · {{ booking.start_date }}
Customer: {{ customer.full_name or customer.contact_name }}"""
    },
    # --- Conversations and system ---
    {
        "name": "human_handover_flow",
        "description": "A customer asked for (or was handed over to) a person in the WhatsApp inbox.",
        "template_type": "whatsapp",
        "body": """Customer needs a person ⚠️

*{{ related_contact_name or contact }}* is waiting in the inbox.
{{ last_bot_message or 'They asked to speak to someone.' }}

Reply to them from the dashboard Inbox."""
    },
    {
        "name": "message_send_failure",
        "description": "A WhatsApp message to a customer failed to send.",
        "template_type": "whatsapp",
        "body": """WhatsApp message failed ⚠️

To: *{{ contact_name }}* ({{ whatsapp_id }})
Type: {{ message_type }}
Reason: {{ error }}"""
    },
    {
        "name": "admin_24h_window_reminder",
        "description": "Sent to a staff user whose 24-hour WhatsApp window is about to close.",
        "template_type": "whatsapp",
        "body": """Hi {{ recipient.first_name or recipient.username }},

Your 24-hour window for receiving Kalai Safaris alerts on WhatsApp is closing. Reply to this message to keep receiving them."""
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
                    # NotificationTemplate has no `buttons` field; quick-reply
                    # buttons in the definitions are informational only.
                    **({'template_type': template_def['template_type']} if 'template_type' in template_def else {}),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created new template: '{template_name}'"))
            else:
                self.stdout.write(f"  Updated existing template: '{template_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully loaded all notification templates."))
