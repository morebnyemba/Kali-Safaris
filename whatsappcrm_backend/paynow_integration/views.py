# views.py
import logging
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import PaynowConfig
from .paynow_wrapper import PaynowSDK # Import the SDK wrapper
from .services import PaynowService
from customer_data.models import Payment, Booking
from conversations.models import Contact # Assuming you need to find the contact by whatsapp_id

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST", "GET"])
def paynow_return_view(request: HttpRequest) -> HttpResponse:
    """
    Handles the return URL from Paynow after a user completes (or cancels) a payment.
    This is usually a browser redirect.
    """
    status = request.GET.get('status', 'unknown')
    reference = request.GET.get('reference')
    paynow_reference = request.GET.get('paynowreference')
    
    logger.info(
        f"Paynow Return URL hit for transaction reference: {reference}. "
        f"Status: '{status}', PaynowRef: '{paynow_reference}'"
    )
    
    # You might want to redirect the user to a specific page in your app
    # based on the status (e.g., success page, pending page, failed page).
    # For now, a simple message.
    if status == 'Paid':
        # Payment was successful, but the IPN (resulturl) is the definitive source.
        # Here, you might show a "Payment successful, awaiting confirmation" message.
        return HttpResponse(f"Payment for {reference} was successful. Thank you! We are confirming your transaction.")
    elif status == 'Cancelled':
        return HttpResponse(f"Payment for {reference} was cancelled. Please try again.")
    else:
        return HttpResponse(f"Payment status for {reference}: {status}. Please check your transaction history.")


@csrf_exempt
@require_http_methods(["POST"])
def paynow_ipn_view(request: HttpRequest) -> HttpResponse:
    """
    Handles IPN (Instant Payment Notification) callbacks from Paynow.
    This is the server-to-server notification that confirms payment status.
    """
    try:
        # Extract IPN data from POST request
        ipn_data = {
            'reference': request.POST.get('reference', ''),
            'paynowreference': request.POST.get('paynowreference', ''),
            'amount': request.POST.get('amount', ''),
            'status': request.POST.get('status', ''),
            'pollurl': request.POST.get('pollurl', ''),
            'hash': request.POST.get('hash', ''),
        }
        
        logger.info(f"Paynow IPN received: {ipn_data}")
        
        # Verify the IPN hash
        paynow_service = PaynowService(ipn_callback_url='/crm-api/paynow/ipn/')
        if not paynow_service.verify_ipn_hash(ipn_data):
            logger.error(f"IPN hash verification failed for reference {ipn_data['reference']}")
            return HttpResponse("Invalid IPN signature", status=400)
        
        # Extract reference (format: BOOKING_REF-PAY-PAYMENT_ID)
        reference = ipn_data['reference']
        paynow_reference = ipn_data['paynowreference']
        amount = ipn_data['amount']
        status = ipn_data['status']
        
        # Try to find the payment record
        try:
            # The reference format is: BOOKING_REF-PAY-PAYMENT_ID
            if '-PAY-' in reference:
                payment_id = reference.split('-PAY-')[-1]
                payment = Payment.objects.get(id=payment_id)
            else:
                # Fallback: try to find by transaction reference
                payment = Payment.objects.get(transaction_reference=paynow_reference)
            
            # Update payment status based on Paynow status
            if status.lower() in ['paid', 'delivered']:
                payment.status = Payment.PaymentStatus.SUCCESSFUL
                payment.notes = f"{payment.notes}\nPayment confirmed via IPN. Paynow ref: {paynow_reference}"
                logger.info(f"Payment {payment.id} marked as successful")
                
                # Optionally send notification to customer via WhatsApp
                # TODO: Add WhatsApp notification
                
            elif status.lower() in ['cancelled', 'failed']:
                payment.status = Payment.PaymentStatus.FAILED
                payment.notes = f"{payment.notes}\nPayment failed. Status: {status}"
                logger.warning(f"Payment {payment.id} marked as failed")
            else:
                # Other statuses (e.g., 'awaiting delivery')
                logger.info(f"Payment {payment.id} has status: {status}")
            
            payment.save()
            
            return HttpResponse("OK", status=200)
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for reference {reference}")
            return HttpResponse("Payment not found", status=404)
        except Exception as e:
            logger.error(f"Error processing payment IPN: {e}", exc_info=True)
            return HttpResponse("Error processing IPN", status=500)
            
    except Exception as e:
        logger.error(f"Error in IPN handler: {e}", exc_info=True)
        return HttpResponse("Error processing IPN", status=500)
