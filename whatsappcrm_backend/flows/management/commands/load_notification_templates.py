# whatsappcrm_backend/flows/management/commands/load_notification_templates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
NOTIFICATION_TEMPLATES = [
    {
        "name": "new_order_created",
        "description": "Sent to admins when a new order is created via a signal.",
        "template_type": "whatsapp",
        "body": """New Order Created! 📦

A new order has been created for customer *{{ order.customer.get_full_name or order.customer.contact.name }}*.

- Order Name: *{{ order.name }}*
- Order #: *{{ order.order_number }}*
- Amount: *${{ order.amount or '0.00' }}*

Please see the admin panel for full details."""
    },
    {
        "name": "new_online_order_placed",
        "description": "Sent to admins when a customer places a new order through the 'Purchase Product' flow.",
        "template_type": "whatsapp",
        "body": """New Online Order Placed! 🛍️

A new order has been placed via WhatsApp by *{{ contact.name or contact.whatsapp_id }}*.

*Order Details:*
- Order #: *{{ created_order_details.order_number }}*
- Total Amount: *${{ created_order_details.amount }}*
- Payment Status: Pending

*Customer & Delivery:*
- Name: {{ delivery_name }}
- Phone: {{ delivery_phone }}
- Address: {{ delivery_address }}

*Items Ordered:*
{% for item in cart_items %}- {{ item.quantity }} x {{ item.name }}
{% endfor %}

Please follow up with the customer to arrange payment."""
    },
    {
        "name": "order_payment_status_updated",
        "description": "Sent to a customer when an admin updates their order's payment status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The status for your order '{{ order_name }}' (#{{ order_number }}) has been updated to: *{{ new_status }}*.

Thank you for choosing us!"""
    },
    {
        "name": "assessment_status_updated",
        "description": "Sent to a customer when an admin updates their site assessment status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The status for your Site Assessment Request (#{{ assessment_id }}) has been updated to: *{{ new_status }}*.

Our team will be in touch with the next steps. Thank you!"""
    },
    {
        "name": "new_installation_request",
        "description": "Sent to admins when a customer submits a new solar installation request.",
        "template_type": "whatsapp",
        "body": """New Installation Request 🛠️

A new installation request has been submitted by *{{ contact.name or contact.whatsapp_id }}*.

*Request Details:*
- Type: {{ installation_type }}
- Order #: {{ order_number or 'N/A' }}
- Assessment #: {{ assessment_number or 'N/A' }}

*Installation Info:*
- Branch: {{ install_branch }}
- Sales Person: {{ install_sales_person }}
- Client Name: {{ install_full_name }}
- Client Phone: {{ install_phone }}{% if install_alt_name and install_alt_name|lower != 'n/a' %}
- Alt. Contact: {{ install_alt_name }} ({{ install_alt_phone }}){% endif %}
- Address: {{ install_address }}{% if install_location_pin and install_location_pin.latitude %}
- Location Pin: https://www.google.com/maps/search/?api=1&query={{ install_location_pin.latitude }},{{ install_location_pin.longitude }}{% endif %}
- Preferred Date: {{ install_datetime }} ({{ install_availability|title }})

Please review and schedule the installation."""
    },
    {
        "name": "new_starlink_installation_request",
        "description": "Sent to admins when a customer submits a new Starlink installation request.",
        "template_type": "whatsapp",
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
        "template_type": "whatsapp",
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
        "template_type": "whatsapp",
        "body": """Admin Action: New Order & Install Created 📝

Admin *{{ contact.name or contact.username }}* has created a new order and installation request.
*Customer:* {{ target_contact.0.name or customer_whatsapp_id }}
*Order #:* {{ order_number_ref }}/PO
*Order Name:* {{ order_description }}

Please see the admin panel for full details."""
    },
    {
        "name": "new_site_assessment_request",
        "description": "Sent to admins when a customer books a new site assessment.",
        "template_type": "whatsapp",
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
        "description": "Sent to admins when a job card is successfully created from an email attachment.",
        "template_type": "whatsapp",
        "body": """New Job Card Created ⚙️

A new job card has been automatically created from an email attachment.

*Job Card #*: {{ job_card.job_card_number }}
*Customer*: {{ customer.first_name }} {{ customer.last_name }}
*Product*: {{ job_card.product_description }}
*Serial #*: {{ job_card.product_serial_number }}
*Reported Fault*: {{ job_card.reported_fault }}

Please review the job card in the admin panel and assign it to a technician."""
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
        "name": "new_placeholder_order_created",
        "description": "Sent to admins when a placeholder order is created via the order receiver number.",
        "template_type": "whatsapp",
        "body": """New Placeholder Order Created 📦

A new placeholder order has been created by *{{ contact.name or contact.whatsapp_id }}*.

*Order #:* {{ normalized_order_number }}

Please update the order details in the admin panel as soon as possible."""
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
        "description": "Sent to admins when an invoice from an email has been successfully processed into an order.",
        "template_type": "whatsapp",
        "body": """Invoice Processed Successfully ✅

An invoice from *{{ attachment.sender }}* (Filename: *{{ attachment.filename }}*) has been processed.

*Order Details:*
- Order #: *{{ order.order_number }}*
- Total Amount: *${{ "%.2f"|format(order.amount) if order.amount is not none else '0.00' }}*
- Customer: *{{ customer.full_name or customer.contact_name }}*

The new order has been created in the system."""
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