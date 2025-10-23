# whatsappcrm_backend/flows/actions.py

import logging
from decimal import Decimal, InvalidOperation
from django.utils.text import slugify
from django.utils import timezone

from .utils import get_contact_from_context, render_string_with_context
from customer_data.models import CustomerProfile, Booking, TourInquiry
from products_and_services.models import Tour
from notifications.services import queue_notifications_to_users
from paynow_integration.services import PaynowService
from pdfs.services import generate_quote_pdf

logger = logging.getLogger(__name__)

# Action registry
flow_actions = {}

def register_flow_action(name):
    """
    A decorator to register a flow action function.
    """
    def decorator(func):
        flow_actions[name] = func
        logger.info(f"Registered flow action: '{name}'")
        return func
    return decorator

@register_flow_action('create_booking_from_inquiry')
def create_booking_from_inquiry(context: dict, params: dict) -> dict:
    """
    Creates a Booking from a completed TourInquiry.
    
    params_template:
      inquiry_context_var: "name_of_variable_holding_the_inquiry_object"
      save_booking_to: "variable_name_to_save_the_created_booking"
    """
    contact = get_contact_from_context(context)
    if not contact or not hasattr(contact, 'customer_profile') or not contact.customer_profile:
        logger.error("create_booking_from_inquiry: Could not find contact or customer profile in context.")
        return context

    inquiry_var = params.get('inquiry_context_var')
    inquiry = context.get(inquiry_var)
    if not inquiry or not isinstance(inquiry, TourInquiry):
        logger.error(f"create_booking_from_inquiry: Inquiry object not found in context variable '{inquiry_var}'.")
        return context

    # Generate a unique booking reference
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    booking_ref = f"BK-{slugify(contact.name or 'user')[:10].upper()}-{timestamp}"

    booking = Booking.objects.create(
        customer=contact.customer_profile,
        booking_reference=booking_ref,
        tour_name=f"Custom Inquiry: {inquiry.destination}",
        start_date=timezone.now().date(), # Placeholder, should be updated by an agent
        end_date=timezone.now().date(),   # Placeholder
        number_of_adults=inquiry.number_of_travelers or 1,
        source=Booking.BookingSource.WHATSAPP,
        notes=f"Created from WhatsApp Inquiry ID: {inquiry.id}\n\n{inquiry.notes}",
        payment_status=Booking.PaymentStatus.PENDING,
    )
    
    # Update the inquiry to show it has been converted
    inquiry.status = TourInquiry.InquiryStatus.CONVERTED
    inquiry.save(update_fields=['status'])

    # Save booking details to context
    save_to_var = params.get('save_booking_to', 'created_booking')
    context[save_to_var] = {
        'booking_reference': booking.booking_reference,
        'total_amount': float(booking.total_amount),
    }
    
    logger.info(f"Successfully created Booking {booking.booking_reference} from Inquiry {inquiry.id}.")
    return context

# This is a placeholder for the send_group_notification action.
# The actual implementation is handled by the flow service, but registering it here
# makes it discoverable.
@register_flow_action('send_group_notification')
def send_group_notification(context: dict, params: dict) -> dict:
    # The actual logic is in flows.services.py. This registration makes it discoverable.
    # We can, however, add a log here to confirm it's being triggered from a flow.
    logger.info(f"Flow action 'send_group_notification' triggered for contact {context.get('contact')} with params: {params}")
    return context

@register_flow_action('initiate_tour_payment')
def initiate_tour_payment(context: dict, params: dict) -> dict:
    """
    Initiates a Paynow payment for a tour booking.

    params_template:
      booking_context_var: "name_of_variable_holding_the_booking_object"
      amount_to_pay_var: "name_of_variable_holding_the_amount"
      save_to_variable: "variable_name_to_save_the_payment_result"
    """
    contact = get_contact_from_context(context)
    if not contact:
        logger.error("initiate_tour_payment: Could not find contact in context.")
        return context

    booking_var = params.get('booking_context_var')
    booking_data = context.get(booking_var)
    if not booking_data or not isinstance(booking_data, dict) or 'id' not in booking_data:
        logger.error(f"initiate_tour_payment: Booking data not found in context variable '{booking_var}'.")
        return context

    amount_var = params.get('amount_to_pay_var')
    amount_to_pay = context.get(amount_var)
    if not isinstance(amount_to_pay, (int, float)):
        logger.error(f"initiate_tour_payment: Amount to pay not found or invalid in context variable '{amount_var}'.")
        return context

    try:
        booking = Booking.objects.get(pk=booking_data['id'])
        paynow_service = PaynowService()
        
        # The service returns a dictionary with the poll_url and other details
        payment_result = paynow_service.initiate_payment(
            booking=booking,
            amount=Decimal(amount_to_pay),
            customer_email=contact.customer_profile.email if hasattr(contact, 'customer_profile') else '',
            return_url="https://kalaisafaris.com/payment-success", # Example URL
            result_url="https://backend.kalaisafaris.com/api/v1/paynow/webhook/" # Your webhook URL
        )
        
        context[params.get('save_to_variable', 'payment_result')] = payment_result
        logger.info(f"Successfully initiated Paynow payment for Booking {booking.booking_reference}. Result: {payment_result}")
    except Booking.DoesNotExist:
        logger.error(f"initiate_tour_payment: Booking with ID {booking_data['id']} not found.")
    except Exception as e:
        logger.error(f"Error initiating Paynow payment: {e}", exc_info=True)
        context[params.get('save_to_variable', 'payment_result')] = {'error': str(e)}

    return context

@register_flow_action('generate_and_save_quote_pdf')
def generate_and_save_quote_pdf(context: dict, params: dict) -> dict:
    """
    Generates a PDF quote based on the current flow context and saves its URL.

    params_template:
      save_to_variable: "variable_name_to_save_the_pdf_url"
    """
    save_to_var = params.get('save_to_variable', 'generated_pdf_url')
    
    # The entire flow context is passed to the PDF generation service
    pdf_url = generate_quote_pdf(context)
    
    if pdf_url:
        context[save_to_var] = pdf_url
    
    return context
