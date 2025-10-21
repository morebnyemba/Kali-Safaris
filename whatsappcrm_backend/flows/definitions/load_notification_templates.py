# whatsappcrm_backend/notifications/management/commands/load_notification_templates.py
# (This file has been moved from the 'flows' app to the 'notifications' app for better project structure)

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate

# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
NOTIFICATION_TEMPLATES = [
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
        "name": "admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new order and installation request via the admin flow.",
        "template_type": "whatsapp",
        "body": """Admin Action: New Order & Install Created 📝

Admin *{{ contact.name or contact.username }}* has created a new order and installation request.

*Customer:* {{ target_contact.0.name or customer_whatsapp_id }}
*Order #:* PO-{{ order_number_ref }}
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

*Order #:* {{ order_number_from_message }}

Please update the order details in the admin panel as soon as possible."""
    },
    {
        "name": "new_loan_application",
        "description": "Sent to the finance team when a customer submits a new loan application.",
        "template_type": "whatsapp",
        "body": """New Loan Application Received 💰

A new loan application has been submitted by *{{ contact.name or contact.whatsapp_id }}*.

*Application Details:*
- Application ID: *#{{ created_loan_application.id }}*
- Name: *{{ loan_applicant_name }}*
- National ID: {{ loan_national_id }}
- Loan Type: {{ loan_type|replace('_', ' ')|title }}
- Employment: {{ loan_employment_status|replace('_', ' ')|title }}
- Monthly Income: ${{ loan_monthly_income }}
{% if loan_request_amount %}- Amount Requested: *${{ loan_request_amount }}*{% endif %}
{% if loan_product_interest %}- Product of Interest: *{{ loan_product_interest }}*{% endif %}

Please review the application in the admin panel and follow up with the customer."""
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