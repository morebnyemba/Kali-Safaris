# whatsappcrm_backend/flows/actions.py

import logging
from decimal import Decimal
from django.utils import timezone
from django.utils.text import slugify

from customer_data.models import Booking, TourInquiry
from pdfs.services import generate_quote_pdf
from paynow_integration.services import PaynowService
from .utils import get_contact_from_context

logger = logging.getLogger(__name__)

class FlowActionRegistry:
    """
    A central registry for custom flow actions. This makes actions discoverable
    and prevents issues with circular imports or app loading order.
    """
    def __init__(self):
        self._actions = {}

    def register(self, name, func):
        self._actions[name] = func
        logger.info(f"Registered flow action: '{name}'")

    def get(self, name):
        return self._actions.get(name)

# Instantiate the registry
flow_action_registry = FlowActionRegistry()

def register_flow_action(name):
    """A decorator to register a flow action function."""
    def decorator(func):
        flow_action_registry.register(name, func)
        return func
    return decorator

@register_flow_action('create_booking_from_inquiry')
def create_booking_from_inquiry(contact, context: dict, params: dict) -> dict:
    """
    Creates a Booking from a completed TourInquiry. This is for custom tours
    where an agent will follow up with a quote.
    """
    contact = contact or get_contact_from_context(context)
    if not contact or not hasattr(contact, 'customer_profile') or not contact.customer_profile:
        logger.error("create_booking_from_inquiry: Could not find contact or customer profile in context.")
        return context

    inquiry_var = params.get('inquiry_context_var')
    inquiry_data = context.get(inquiry_var)
    if not inquiry_data or 'id' not in inquiry_data:
        logger.error(f"create_booking_from_inquiry: Inquiry object not found in context variable '{inquiry_var}'.")
        return context

    try:
        inquiry = TourInquiry.objects.get(id=inquiry_data['id'])
        timestamp = timezone.now().strftime('%Y%m%d%H%M')
        booking_ref = f"BK-INQ-{slugify(contact.name or 'user')[:5].upper()}-{timestamp}"

        booking = Booking.objects.create(
            customer=contact.customer_profile,
            booking_reference=booking_ref,
            tour_name=f"Custom Inquiry: {inquiry.destinations}",
            start_date=timezone.now().date(), # Placeholder, to be updated by agent
            end_date=timezone.now().date(),   # Placeholder
            number_of_adults=inquiry.number_of_travelers or 1,
            source=Booking.BookingSource.WHATSAPP,
            notes=f"Created from WhatsApp Inquiry ID: {inquiry.id}\n\n{inquiry.notes}",
            payment_status=Booking.PaymentStatus.PENDING,
        )
        
        inquiry.status = TourInquiry.InquiryStatus.CONVERTED
        inquiry.save(update_fields=['status'])

        save_to_var = params.get('save_booking_to', 'created_booking_from_inquiry')
        context[save_to_var] = {'booking_reference': booking.booking_reference}
        
        logger.info(f"Successfully created Booking {booking.booking_reference} from Inquiry {inquiry.id}.")
    except TourInquiry.DoesNotExist:
        logger.error(f"create_booking_from_inquiry: TourInquiry with ID {inquiry_data['id']} not found.")
    
    return context

@register_flow_action('initiate_tour_payment')
def initiate_tour_payment(contact, context: dict, params: dict) -> dict:
    """Initiates a Paynow payment for a tour booking."""
    contact = contact or get_contact_from_context(context)
    if not contact:
        logger.error("initiate_tour_payment: Could not find contact in context.")
        return context

    booking_var = params.get('booking_context_var')
    booking_data = context.get(booking_var)
    if not booking_data or 'id' not in booking_data:
        logger.error(f"initiate_tour_payment: Booking data not found in context variable '{booking_var}'.")
        return context

    amount_var = params.get('amount_to_pay_var')
    amount_to_pay = context.get(amount_var)
    if not isinstance(amount_to_pay, (int, float, str)):
        logger.error(f"initiate_tour_payment: Amount to pay not found or invalid in context variable '{amount_var}'.")
        return context

    try:
        booking = Booking.objects.get(pk=booking_data['id'])
        paynow_service = PaynowService(ipn_callback_url='/crm-api/paynow/ipn/')
        payment_result = paynow_service.initiate_payment(
            booking=booking, 
            amount=Decimal(amount_to_pay),
            phone_number=context.get('payment_phone', ''),
            email=contact.customer_profile.email if hasattr(contact, 'customer_profile') else '',
            payment_method=context.get('payment_method', 'ecocash'),
            description=f"Tour booking payment for {booking.tour_name}"
        )
        context[params.get('save_to_variable', 'payment_result')] = payment_result
        logger.info(f"Successfully initiated Paynow payment for Booking {booking.booking_reference}.")
    except Booking.DoesNotExist:
        logger.error(f"initiate_tour_payment: Booking with ID {booking_data['id']} not found.")
    except Exception as e:
        logger.error(f"Error initiating Paynow payment: {e}", exc_info=True)
        context[params.get('save_to_variable', 'payment_result')] = {'error': str(e)}

    return context

@register_flow_action('initiate_paynow_payment')
def initiate_paynow_payment(contact, context: dict, params: dict) -> dict:
    """
    Initiates a Paynow payment with detailed parameters.
    Expected params:
        - booking_id: The booking ID from context
        - amount: The amount to pay
        - phone_number: Customer phone number  
        - email: Customer email
        - payment_method: One of 'ecocash', 'onemoney', 'innbucks'
        - save_to_variable: Variable name to save result (default: 'paynow_payment_result')
    """
    contact = contact or get_contact_from_context(context)
    if not contact:
        logger.error("initiate_paynow_payment: Could not find contact in context.")
        return context

    # Extract parameters from params_template
    booking_id = params.get('booking_id')
    amount = params.get('amount')
    phone_number = params.get('phone_number')
    email = params.get('email')
    payment_method = params.get('payment_method')
    
    # Validate required parameters
    if not all([booking_id, amount, phone_number, email, payment_method]):
        logger.error(f"initiate_paynow_payment: Missing required parameters. Got: {params}")
        context[params.get('save_to_variable', 'paynow_payment_result')] = {
            'success': False, 
            'message': 'Missing required payment parameters'
        }
        return context

    try:
        # Get the booking
        booking = Booking.objects.get(pk=booking_id)
        
        # Initialize Paynow service
        paynow_service = PaynowService(ipn_callback_url='/crm-api/paynow/ipn/')
        
        # Initiate payment
        payment_result = paynow_service.initiate_payment(
            booking=booking,
            amount=Decimal(str(amount)),
            phone_number=phone_number,
            email=email,
            payment_method=payment_method,
            description=f"Tour booking payment for {booking.tour_name}"
        )
        
        # Save result to context
        context[params.get('save_to_variable', 'paynow_payment_result')] = payment_result
        
        if payment_result.get('success'):
            logger.info(f"Successfully initiated Paynow {payment_method} payment for Booking {booking.booking_reference}")
        else:
            logger.warning(f"Paynow payment initiation failed for Booking {booking.booking_reference}: {payment_result.get('message')}")
            
    except Booking.DoesNotExist:
        logger.error(f"initiate_paynow_payment: Booking with ID {booking_id} not found.")
        context[params.get('save_to_variable', 'paynow_payment_result')] = {
            'success': False,
            'message': 'Booking not found'
        }
    except Exception as e:
        logger.error(f"Error initiating Paynow payment: {e}", exc_info=True)
        context[params.get('save_to_variable', 'paynow_payment_result')] = {
            'success': False,
            'message': f'Error processing payment: {str(e)}'
        }

    return context

@register_flow_action('generate_and_save_quote_pdf')
def generate_and_save_quote_pdf_action(contact, context: dict, params: dict) -> dict:
    """Generates a PDF quote and saves its URL to the context."""
    save_to_var = params.get('save_to_variable', 'generated_pdf_url')
    pdf_url = generate_quote_pdf(context)
    if pdf_url:
        context[save_to_var] = pdf_url
    return context

@register_flow_action('create_placeholder_order')
def create_placeholder_order(contact, context: dict, params: dict) -> dict:
    """
    Creates a placeholder Booking record from a simple order number message.
    This is used by the `simple_add_order_flow`.
    """
    contact = contact or get_contact_from_context(context)
    if not contact or not hasattr(contact, 'customer_profile') or not contact.customer_profile:
        logger.error("create_placeholder_order: Could not find contact or customer profile in context.")
        return context

    order_number = params.get('order_number')
    if not order_number:
        logger.error("create_placeholder_order: 'order_number' not found in params.")
        return context

    try:
        Booking.objects.create(
            customer=contact.customer_profile,
            booking_reference=order_number,
            tour_name=f"Placeholder for Order: {order_number}",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            payment_status=Booking.PaymentStatus.PENDING,
            source=Booking.BookingSource.MANUAL_ENTRY,
            notes=f"Placeholder booking created by {contact.name or contact.whatsapp_id} via simple order flow."
        )
        logger.info(f"Successfully created placeholder booking {order_number} for contact {contact.id}.")
    except Exception as e:
        logger.error(f"Error creating placeholder booking {order_number}: {e}", exc_info=True)

    return context

@register_flow_action('save_travelers_to_booking')
def save_travelers_to_booking(contact, context: dict, params: dict) -> dict:
    """
    Saves traveler details from the context to Traveler model instances
    associated with a booking.
    """
    from customer_data.models import Traveler
    
    booking_var = params.get('booking_context_var', 'created_booking')
    travelers_var = params.get('travelers_context_var', 'travelers_details')
    
    booking_data = context.get(booking_var)
    travelers_details = context.get(travelers_var, [])
    
    if not booking_data or 'id' not in booking_data:
        logger.error(f"save_travelers_to_booking: Booking data not found in context variable '{booking_var}'.")
        return context
    
    if not isinstance(travelers_details, list) or not travelers_details:
        logger.warning(f"save_travelers_to_booking: No traveler details found in context variable '{travelers_var}'.")
        return context
    
    try:
        booking = Booking.objects.get(pk=booking_data['id'])
        
        # Create Traveler instances for each traveler in the list
        travelers_created = 0
        for traveler_data in travelers_details:
            if not isinstance(traveler_data, dict):
                continue
                
            # Extract traveler information
            name = traveler_data.get('name', '')
            age = traveler_data.get('age', 0)
            nationality = traveler_data.get('nationality', '')
            gender = traveler_data.get('gender', '')
            id_number = traveler_data.get('id_number', '')
            medical = traveler_data.get('medical', '')
            traveler_type = traveler_data.get('type', 'adult')
            id_document_media_id = traveler_data.get('id_document', '')
            
            # Skip if essential fields are missing
            if not name or age is None or age == '':
                logger.warning(f"Skipping traveler with incomplete data: {traveler_data}")
                continue
            
            # Validate and convert age to integer
            try:
                age_int = int(age)
                if age_int < 0 or age_int > 150:
                    logger.warning(f"Skipping traveler {name} with invalid age: {age}")
                    continue
            except (ValueError, TypeError):
                logger.warning(f"Skipping traveler {name} with non-numeric age: {age}")
                continue
            
            # Process medical requirements
            medical_requirements = ''
            if medical and isinstance(medical, str):
                medical_lower = medical.lower()
                if medical_lower not in ['none', 'no', 'n/a', '']:
                    medical_requirements = medical
            
            # Create Traveler instance
            traveler = Traveler.objects.create(
                booking=booking,
                name=name,
                age=age_int,
                nationality=nationality,
                gender=gender,
                id_number=id_number,
                medical_dietary_requirements=medical_requirements,
                traveler_type=traveler_type
            )
            
            # Handle ID document if provided
            if id_document_media_id:
                try:
                    from meta_integration.utils import download_whatsapp_media
                    from django.core.files.base import ContentFile
                    import mimetypes
                    
                    # Download the media from WhatsApp
                    download_result = download_whatsapp_media(
                        id_document_media_id,
                        contact.associated_app_config
                    )
                    
                    if download_result:
                        media_content, media_mime_type = download_result
                        
                        # Determine file extension from mime type
                        file_extension = mimetypes.guess_extension(media_mime_type) or '.jpg'
                        
                        # Save the document to the traveler
                        file_name = f"id_document_{traveler.id}{file_extension}"
                        traveler.id_document.save(file_name, ContentFile(media_content), save=True)
                        logger.info(f"Successfully saved ID document for traveler {name} (mime: {media_mime_type})")
                except Exception as e:
                    logger.error(f"Error saving ID document for traveler {name}: {e}", exc_info=True)
            
            travelers_created += 1
        
        logger.info(f"Successfully created {travelers_created} traveler records for Booking {booking.booking_reference}.")
        context['travelers_saved_count'] = travelers_created
        
    except Booking.DoesNotExist:
        logger.error(f"save_travelers_to_booking: Booking with ID {booking_data['id']} not found.")
    except Exception as e:
        logger.error(f"Error saving travelers to booking: {e}", exc_info=True)
    
    return context
