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
from customer_data.models import CustomerProfile, Booking, TourInquiry
from conversations.models import Contact
from products_and_services.models import Tour
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
            f"Kali Safaris"
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
                    <p>Thank you,<br><strong>Kali Safaris</strong></p>
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
def send_duplicate_invoice_email(self, attachment_id, booking_reference):
    """
    Sends an email to the original sender informing them that the document
    they sent is a duplicate of an existing booking.
    """
    log_prefix = f"[Duplicate Email Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Preparing to send duplicate booking notification for attachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if not attachment.sender:
            logger.warning(f"{log_prefix} Attachment {attachment_id} has no sender email. Cannot send notification.")
            return "Skipped: No sender email."

        subject = f"Duplicate Booking Document Detected: '{attachment.filename}'"
        message = (
            f"Dear Sender,\n\n"
            f"This is an automated message to inform you that the document '{attachment.filename}' you sent appears to be a duplicate.\n\n"
            f"A booking with the same reference number ({booking_reference}) already exists in our system.\n\n"
            f"No further action is needed. If you believe this is an error, please contact our support team.\n\n"
            f"Thank you,\n"
            f"Kali Safaris"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [attachment.sender]
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"{log_prefix} Successfully sent duplicate booking email to {attachment.sender}.")
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

        # --- UPDATED: Schema for Tour Booking Confirmation ---
        booking_schema_definition = """
        {
          "customer": {
            "name": "string | null",
            "phone": "string | null",
            "email": "string | null",
            "address": "string | null"
          },
          "booking_details": {
            "booking_reference": "string | null",
            "booking_date": "YYYY-MM-DD | null",
            "tour_name": "string | null",
            "tour_start_date": "YYYY-MM-DD | null",
            "number_of_adults": "number",
            "number_of_children": "number"
          },
          "payment_details": {
            "total_amount": "number | null",
            "amount_paid": "number | null",
            "payment_status": "string (e.g., 'Paid', 'Deposit Paid', 'Pending')"
          },
          "notes": "string | null"
        }
        """

        # --- NEW: Update the Prompt to Classify First, then Extract ---
        prompt = f"""
        Analyze the attached document and determine its type. The type should be 'booking_confirmation'.

        Based on the identified type, extract the key details into the corresponding JSON schema.

        If the document type is 'booking_confirmation', use this schema:
        {booking_schema_definition}

        Your final output must be a single JSON object with two keys: "document_type" and "data". The document_type should be 'booking_confirmation'.
        The "data" key should contain the extracted information. For dates, use YYYY-MM-DD format.

        Example for a booking confirmation:
        {{
            "document_type": "booking_confirmation",
            "data": {{ "customer": {{ "name": "John Doe" }}, "booking_details": {{ "booking_reference": "KS-123" }} }}
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
            raise ValueError("AI response missing 'document_type' or 'data' key. Raw: " + json.dumps(extracted_data))

        logger.info(f"{log_prefix} Gemini identified document as type: '{document_type}'")

        if document_type == 'booking_confirmation':
            _create_booking_from_data(attachment, data, log_prefix)
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
def _create_booking_from_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Creates or updates a Booking from extracted booking confirmation data."""
    from django.forms.models import model_to_dict
    logger.info(f"{log_prefix} Starting to create Booking from extracted data.")

    customer_profile = _get_or_create_customer_profile(data.get('customer', {}), log_prefix)
    booking_details = data.get('booking_details', {})
    payment_details = data.get('payment_details', {})

    booking_ref = booking_details.get('booking_reference')
    if not booking_ref:
        logger.warning(f"{log_prefix} No 'booking_reference' found in data. Cannot create booking.")
        return

    if Booking.objects.filter(booking_reference=booking_ref).exists():
        logger.warning(f"{log_prefix} Booking with reference '{booking_ref}' already exists. Skipping creation.")
        # Optionally send a duplicate notification email here.
        return

    start_date_obj = None
    if date_str := booking_details.get('tour_start_date'):
        try:
            start_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Could not parse start_date string '{date_str}' for Booking.")

    # Create the Booking
    booking = Booking.objects.create(
        booking_reference=booking_ref,
        customer=customer_profile,
        tour_name=booking_details.get('tour_name', 'Unknown Tour'),
        start_date=start_date_obj,
        end_date=start_date_obj,  # Placeholder, you might need to calculate this
        number_of_adults=booking_details.get('number_of_adults', 1),
        number_of_children=booking_details.get('number_of_children', 0),
        total_amount=payment_details.get('total_amount', 0),
        amount_paid=payment_details.get('amount_paid', 0),
        payment_status=payment_details.get('payment_status', 'pending').lower().replace(' ', '_'),
        source=Booking.BookingSource.EMAIL_IMPORT,
        booking_details_payload=data,
    )

    logger.info(f"{log_prefix} Created new Booking with reference '{booking_ref}'.")

    # Send notification
    if customer_profile:
        attachment_dict = model_to_dict(attachment, fields=['sender', 'filename'])
        booking_dict = {
            'reference': booking.booking_reference,
            'tour_name': booking.tour_name,
            'start_date': booking.start_date.strftime('%Y-%m-%d') if booking.start_date else 'N/A',
        }
        customer_dict = {'full_name': customer_profile.get_full_name(), 'contact_name': getattr(customer_profile.contact, 'name', None)}

        queue_notifications_to_users(
            template_name='booking_created_from_email',
            group_names=settings.INVOICE_PROCESSED_NOTIFICATION_GROUPS,
            related_contact=customer_profile.contact,
            template_context={
                'attachment': attachment_dict, 'booking': booking_dict, 'customer': customer_dict
            }
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