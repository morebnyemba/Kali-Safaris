import os
import logging
import re
from google.api_core import exceptions as core_exceptions
import smtplib
import json
from datetime import datetime
from celery import shared_task, chain

from celery import shared_task
from google import genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors
from .models import EmailAttachment, ParsedInvoice
from decimal import Decimal, InvalidOperation
# --- ADD JobCard to imports ---
from customer_data.models import CustomerProfile, Order, OrderItem, JobCard
from conversations.models import Contact
from products_and_services.models import Product
from notifications.services import queue_notifications_to_users
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q

# Import the new model to fetch credentials
from ai_integration.models import AIProvider
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="email_integration.send_receipt_confirmation_email",
    # Automatically retry for connection errors, which are common for email servers.
    autoretry_for=(ConnectionRefusedError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3}
)
def send_receipt_confirmation_email(self, attachment_id):
    """
    Sends an email to the original sender confirming receipt of their attachment.
    Retries on common SMTP connection errors.
    """
    log_prefix = f"[Email Confirmation Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Preparing to send receipt confirmation for attachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)

        if not attachment.sender:
            logger.warning(f"{log_prefix} Attachment {attachment_id} has no sender email. Cannot send confirmation.")
            return "Skipped: No sender email."

        subject = f"Confirmation: We've received your document '{attachment.filename}'"

        # Plain text version for email clients that don't support HTML
        text_message = (
            f"Dear Sender,\n\n"
            f"This is an automated message to confirm that we have successfully received your attachment named '{attachment.filename}'.\n\n"
            f"Our system is now processing it. You will be notified if any further action is required.\n\n"
            f"Thank you,\n"
            f"Hanna Installations"
        )

        # HTML version for a richer user experience
        html_message = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; margin: auto; }}
                    .header {{ font-size: 1.2em; font-weight: bold; color: #28a745; }}
                    strong {{ color: #000; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <p class="header">Document Receipt Confirmation</p>
                    <p>Dear Sender,</p>
                    <p>This is an automated message to confirm that we have successfully received your attachment named <strong>'{attachment.filename}'</strong>.</p>
                    <p>Our system is now processing it. You will be notified if any further action is required.</p>
                    <p>Thank you,<br><strong>Hanna Installations</strong></p>
                </div>
            </body>
        </html>
        """

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [attachment.sender]

        send_mail(subject, text_message, from_email, recipient_list, html_message=html_message)

        logger.info(f"{log_prefix} Successfully sent confirmation email to {attachment.sender} for attachment {attachment_id}.")
        return f"Confirmation sent to {attachment.sender}."
    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id} to send confirmation.")
        # No retry needed, this is a permanent failure for this task instance.
    except Exception as e:
        # The `autoretry_for` decorator handles SMTP exceptions. We just need to log other errors.
        logger.error(f"{log_prefix} An unexpected error occurred while sending confirmation for attachment {attachment_id}: {e}", exc_info=True)
        raise  # Re-raise to let Celery mark the task as failed for non-retriable errors.

@shared_task(
    bind=True,
    name="email_integration.send_duplicate_invoice_email",
    autoretry_for=(ConnectionRefusedError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3}
)
def send_duplicate_invoice_email(self, attachment_id, order_number):
    """
    Sends an email to the original sender informing them that the invoice
    they sent is a duplicate of an existing order.
    """
    log_prefix = f"[Duplicate Email Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Preparing to send duplicate invoice notification for attachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if not attachment.sender:
            logger.warning(f"{log_prefix} Attachment {attachment_id} has no sender email. Cannot send notification.")
            return "Skipped: No sender email."

        subject = f"Duplicate Invoice Detected: '{attachment.filename}'"
        message = (
            f"Dear Sender,\n\n"
            f"This is an automated message to inform you that the invoice '{attachment.filename}' you sent appears to be a duplicate.\n\n"
            f"An order with the same invoice number ({order_number}) already exists in our system.\n\n"
            f"No further action is needed. If you believe this is an error, please contact our support team.\n\n"
            f"Thank you,\n"
            f"Hanna Installations"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [attachment.sender]
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"{log_prefix} Successfully sent duplicate invoice email to {attachment.sender}.")
        return f"Duplicate notification sent to {attachment.sender}."
    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id} to send duplicate notification.")
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred while sending duplicate notification for attachment {attachment_id}: {e}", exc_info=True)
        raise

@shared_task(
    bind=True,
    name="email_integration.process_attachment_with_gemini",
    # Automatically retry on transient API errors like rate limits or server overload.
    autoretry_for=(core_exceptions.ResourceExhausted, genai_errors.ServerError),
    retry_backoff=True, retry_kwargs={'max_retries': 5}
)
def process_attachment_with_gemini(self, attachment_id):
    """
    Fetches an attachment, asks Gemini to classify it (invoice or job_card),
    extracts structured data based on the type, and saves it to the correct model.
    """
    log_prefix = f"[Gemini File API Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Starting Gemini processing for attachment ID: {attachment_id}")

    attachment = None
    uploaded_file = None

    try:
        # 1. Fetch the attachment record and check processing status
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if attachment.processed:
            logger.warning(f"{log_prefix} Attachment ID {attachment_id} already processed. Skipping.")
            return f"Skipped: Attachment {attachment_id} already processed."

        # --- Configure Gemini ---
        try:
            active_provider = AIProvider.objects.get(provider='google_gemini', is_active=True)
            client = genai.Client(api_key=active_provider.api_key)
        except (AIProvider.DoesNotExist, AIProvider.MultipleObjectsReturned) as e:
            error_message = f"Gemini API key configuration error: {e}"
            logger.error(f"{log_prefix} {error_message}")
            attachment.processed = True
            attachment.extracted_data = {"error": error_message, "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
            return f"Failed: {error_message}"

        # 2. Upload the local file to the Gemini API
        file_path = attachment.file.path
        logger.info(f"{log_prefix} Uploading file to Gemini: {file_path}")
        uploaded_file = client.files.upload(file=file_path)
        logger.info(f"{log_prefix} File uploaded successfully. URI: {uploaded_file.uri}")

        # --- UPDATED: More detailed invoice schema ---
        invoice_schema_definition = """
        {
          "issuer": {
            "tin": "string | null",
            "name": "string | null",
            "email": "string | null",
            "phone": "string | null",
            "vat_no": "string | null",
            "address": "string | null"
          },
          "recipient": {
            "name": "string | null",
            "phone": "string | null",
            "address": "string | null"
          },
          "line_items": [
            {
              "product_code": "string | null",
              "description": "string",
              "quantity": "number",
              "unit_price": "number",
              "vat_amount": "number | null",
              "total_amount": "number"
            }
          ],
          "invoice_number": "string | null",
          "customer_reference_no": "string | null",
          "invoice_date": "YYYY-MM-DD | null",
          "total_amount": "number | null",
          "total_vat_amount": "number | null",
          "notes_and_terms": "string | null"
        }
        """

        job_card_schema_definition = """
        {
          "job_card_number": "string", "creation_date": "YYYY-MM-DD",
          "customer": { "name": "string", "phone": "string", "address": "string" },
          "product": { "description": "string", "serial_number": "string" },
          "reported_fault": "string", "is_under_warranty": "boolean", "status": "string"
        }
        """

        # --- NEW: Update the Prompt to Classify First, then Extract ---
        prompt = f"""
        Analyze the attached document and determine its type. The type can be 'invoice' or 'job_card'.

        Based on the identified type, extract the key details into the corresponding JSON schema.

        If the document type is 'invoice', use this schema:
        {invoice_schema_definition}

        If the document type is 'job_card', use this schema:
        {job_card_schema_definition}

        Your final output must be a single JSON object with two keys: "document_type" and "data".
        The "data" key should contain the extracted information. For dates, use YYYY-MM-DD format.
        For boolean values, use true or false.

        Example for a job card:
        {{
            "document_type": "job_card",
            "data": {{ "job_card_number": "31,699", "creation_date": "2025-09-18", ... }}
        }}
        """

        # 4. Call the Gemini API to process the document
        logger.info(f"{log_prefix} Sending request to Gemini model for analysis.")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, uploaded_file],
        )

        # 5. Parse the extracted JSON data
        try:
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            if not cleaned_text:
                raise json.JSONDecodeError("Empty response from Gemini", "", 0)
            extracted_data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"{log_prefix} Failed to decode JSON from Gemini response for attachment {attachment_id}. Error: {e}. Raw response text: '{response.text}'")
            attachment.processed = True
            attachment.extracted_data = {"error": "Invalid JSON response from Gemini", "status": "failed", "raw_response": response.text}
            attachment.save(update_fields=['processed', 'extracted_data'])
            return f"Failed: Gemini returned non-JSON response for attachment {attachment_id}."

        # --- NEW: Conditional Logic Based on Document Type ---
        document_type = extracted_data.get("document_type")
        data = extracted_data.get("data")

        if not document_type or not data:
            raise ValueError("AI response missing 'document_type' or 'data' key.")

        logger.info(f"{log_prefix} Gemini identified document as type: '{document_type}'")

        if document_type == 'invoice':
            _create_order_from_invoice_data(attachment, data, log_prefix)
        elif document_type == 'job_card':
            _create_job_card_from_data(attachment, data, log_prefix)
        else:
            logger.warning(f"{log_prefix} Unknown document type '{document_type}' received. Skipping database save.")

        # 8. Update the EmailAttachment status
        attachment.processed = True
        attachment.extracted_data = extracted_data
        attachment.save(update_fields=['processed', 'extracted_data', 'updated_at'])

        logger.info(f"{log_prefix} Successfully processed attachment {attachment_id}.")
        send_receipt_confirmation_email.delay(attachment_id)
        return f"Successfully processed attachment {attachment_id} with Gemini."

    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Attachment with ID {attachment_id} not found.")
    except (core_exceptions.ResourceExhausted, core_exceptions.DeadlineExceeded, genai_errors.ServerError) as e:
        logger.warning(f"{log_prefix} Gemini API rate limit or timeout error for attachment {attachment_id}: {e}. Task will be retried by Celery.")
        raise
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during Gemini processing for attachment {attachment_id}: {e}", exc_info=True)
        if attachment:
            attachment.processed = True
            attachment.extracted_data = {"error": str(e), "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
    finally:
        # 9. Clean up: Delete the file from the Gemini service
        if uploaded_file:
            try:
                logger.info(f"{log_prefix} Deleting temporary file from Gemini service: {uploaded_file.name}")
                client.files.delete(name=uploaded_file.name)
            except Exception as e:
                logger.error(f"{log_prefix} Failed to delete uploaded Gemini file {uploaded_file.name}: {e}")


def _get_or_create_customer_profile(customer_data: dict, log_prefix: str) -> CustomerProfile | None:
    """Finds or creates a customer profile based on data from a document."""
    customer_name = customer_data.get('name')
    customer_phone = customer_data.get('phone')

    if not customer_phone and customer_name:
        match = re.search(r'(07[1-9][0-9]{7})', customer_name)
        if match:
            customer_phone = match.group(0)
            customer_name = customer_name.replace(customer_phone, '').strip(' _-').strip()
            logger.info(f"{log_prefix} Extracted fallback phone '{customer_phone}' from name.")

    if not customer_phone:
        logger.warning(f"{log_prefix} No phone number found for customer '{customer_name}'. Cannot create profile.")
        return None

    normalized_phone = re.sub(r'\D', '', customer_phone)
    contact, _ = Contact.objects.get_or_create(
        whatsapp_id=normalized_phone,
        defaults={'name': customer_name or f"Customer {normalized_phone}"}
    )

    profile, created = CustomerProfile.objects.get_or_create(
        contact=contact,
        defaults={
            'first_name': customer_name.split(' ')[0] if customer_name else '',
            'last_name': ' '.join(customer_name.split(' ')[1:]) if customer_name and ' ' in customer_name else '',
            'address_line_1': customer_data.get('address', '')
        }
    )

    if created:
        logger.info(f"{log_prefix} Created new CustomerProfile for '{customer_name}'.")
    else:
        logger.info(f"{log_prefix} Found existing CustomerProfile for '{customer_name}'.")

    return profile


@transaction.atomic
def _create_order_from_invoice_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Creates or updates an Order and its items from extracted invoice data."""
    from django.forms.models import model_to_dict
    logger.info(f"{log_prefix} Starting to create Order from extracted data.")
    
    customer_profile = _get_or_create_customer_profile(data.get('recipient', {}), log_prefix)
    
    # --- FIX: More robust fallback logic for order number ---
    invoice_num_raw = data.get('invoice_number')
    cust_ref_raw = data.get('customer_reference_no')
    invoice_number = None

    # Prioritize invoice_number only if it's a meaningful, non-zero value
    if invoice_num_raw and str(invoice_num_raw).strip() and str(invoice_num_raw).strip() != '0':
        invoice_number = str(invoice_num_raw).strip()
    # Fallback to customer_reference_no if it exists and invoice_number was not valid
    elif cust_ref_raw and str(cust_ref_raw).strip():
        invoice_number = str(cust_ref_raw).strip()

    if not invoice_number:
        logger.warning(f"{log_prefix} No valid 'invoice_number' or 'customer_reference_no' found in data. Cannot create order.")
        return

    # --- NEW: Check for existing order BEFORE creating ---
    if Order.objects.filter(order_number=invoice_number).exists():
        logger.warning(f"{log_prefix} Order with number '{invoice_number}' already exists. Skipping creation and sending duplicate notification.")
        send_duplicate_invoice_email.delay(attachment.id, invoice_number)
        return # Stop processing

    invoice_date_obj = None
    if date_str := data.get('invoice_date'):
        try:
            invoice_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Could not parse date string '{date_str}' for Order.")

    # Since we checked for existence, we can now safely create it.
    order = Order.objects.create(
        order_number=invoice_number,
        customer=customer_profile,
        name=f"Invoice {invoice_number}",
        stage=Order.Stage.CLOSED_WON,
        payment_status=Order.PaymentStatus.PAID,
        source=Order.Source.EMAIL_IMPORT,
        invoice_details=data,
        expected_close_date=invoice_date_obj,
    )

    logger.info(f"{log_prefix} Created new Order with order_number '{invoice_number}'.")

    line_items = data.get('line_items', [])
    if isinstance(line_items, list):
        for item_data in line_items:
            product_code = item_data.get('product_code')
            product_description = item_data.get('description', 'Unknown Product')
            
            # More robust product lookup: Try SKU first, then name.
            product = None
            if product_code:
                product = Product.objects.filter(sku=product_code).first()
            if not product and product_description:
                product = Product.objects.filter(name=product_description).first()

            if not product:
                product = Product.objects.create(
                    sku=product_code,
                    name=product_description,
                    price=item_data.get('unit_price', 0),
                    product_type=Product.ProductType.HARDWARE # Default type
                )
            OrderItem.objects.create(
                order=order, 
                product=product, 
                quantity=item_data.get('quantity', 1), 
                unit_price=item_data.get('unit_price', 0),
                total_amount=item_data.get('total_amount', 0) # Save the line item total
            )
        logger.info(f"{log_prefix} Created {len(line_items)} OrderItem(s) for Order '{invoice_number}'.")

        # --- NEW: Send the specific, more descriptive notification for email imports ---
        if customer_profile:
            from django.forms.models import model_to_dict
            attachment_dict = model_to_dict(attachment, fields=['sender', 'filename'])
            # --- FIX: Explicitly convert Decimal to float for JSON serialization ---
            order_dict = {
                'order_number': order.order_number, 'amount': float(order.amount) if order.amount is not None else 0.0
            }
            customer_dict = {'full_name': customer_profile.get_full_name(), 'contact_name': getattr(customer_profile.contact, 'name', None)}

            queue_notifications_to_users(
                template_name='invoice_processed_successfully',
                group_names=settings.INVOICE_PROCESSED_NOTIFICATION_GROUPS,
                related_contact=customer_profile.contact,
                template_context={
                    'attachment': attachment_dict, 'order': order_dict, 'customer': customer_dict
                }
            )

@transaction.atomic
def _create_job_card_from_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Creates or updates a JobCard from extracted data."""
    logger.info(f"{log_prefix} Starting to create JobCard from extracted data.")

    customer_profile = _get_or_create_customer_profile(data.get('customer', {}), log_prefix)

    job_card_number = data.get('job_card_number')
    if not job_card_number:
        logger.warning(f"{log_prefix} No 'job_card_number' found in data. Cannot create job card.")
        return

    creation_date_obj = None
    if date_str := data.get('creation_date'):
        try:
            creation_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Could not parse date string '{date_str}' for JobCard.")

    product_info = data.get('product', {})

    job_card, created = JobCard.objects.update_or_create(
        job_card_number=job_card_number,
        defaults={
            'customer': customer_profile,
            'product_description': product_info.get('description'),
            'product_serial_number': product_info.get('serial_number'),
            'reported_fault': data.get('reported_fault'),
            'is_under_warranty': data.get('is_under_warranty', False),
            'creation_date': creation_date_obj,
            'status': data.get('status', 'open').lower(),
            'job_card_details': data,
        }
    )

    if created:
        logger.info(f"{log_prefix} Created new JobCard with number '{job_card_number}'.")
    else:
        logger.info(f"{log_prefix} Updated existing JobCard with number '{job_card_number}'.")

    # --- NEW: Send notification if a new job card was created ---
    if created:
        from django.forms.models import model_to_dict
        job_card_dict = model_to_dict(job_card, fields=[
            'job_card_number', 'product_description', 'product_serial_number', 'reported_fault'
        ])
        customer_dict = {}
        if customer_profile:
            customer_dict = {
                'first_name': customer_profile.first_name,
                'last_name': customer_profile.last_name
            }

        queue_notifications_to_users(
            template_name='job_card_created_successfully',
            # You might want to create a specific group setting for this
            group_names=settings.INVOICE_PROCESSED_NOTIFICATION_GROUPS,
            related_contact=customer_profile.contact if customer_profile else None,
            template_context={'job_card': job_card_dict, 'customer': customer_dict}
        )

@shared_task(name="email_integration.fetch_email_attachments_task")
def fetch_email_attachments_task():
    """
    Celery task to run the fetch_mailu_attachments management command.
    """
    log_prefix = "[Fetch Email Task]"
    logger.info(f"{log_prefix} Starting scheduled task to fetch email attachments.")
    try:
        call_command('fetch_mailu_attachments')
        logger.info(f"{log_prefix} Successfully finished fetch_mail_attachments command.")
    except Exception as e:
        logger.error(f"{log_prefix} The 'fetch_mail_attachments' command failed: {e}", exc_info=True)
        raise