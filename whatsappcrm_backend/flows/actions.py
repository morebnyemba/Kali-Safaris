# whatsappcrm_backend/flows/actions.py

import logging
from decimal import Decimal, InvalidOperation
from django.utils.text import slugify
from django.utils import timezone

from .utils import get_contact_from_context, render_string_with_context
from customer_data.models import CustomerProfile, Booking, TourInquiry
from products_and_services.models import Tour
from notifications.services import queue_notifications_to_users

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
    params_template:
      inquiry_context_var: "name_of_variable_holding_the_inquiry_object"
      save_booking_to: "variable_name_to_save_the_created_booking"
    """
    contact = get_contact_from_context(context)
    if not contact or not hasattr(contact, 'customer_profile'):
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
    # This action is handled by the core flow service, which calls queue_notifications_to_users.
    # No implementation is needed here, but it must be registered to be recognized in flow definitions.
    logger.debug(f"Flow action 'send_group_notification' triggered with params: {params}")
    return context
