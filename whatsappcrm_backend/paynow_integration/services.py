# services.py
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from django.conf import settings

from .paynow_wrapper import PaynowSDK # Import our wrapper
from .models import PaynowConfig
from customer_data.models import Payment, Booking

logger = logging.getLogger(__name__)

class PaynowService:
    """
    Service class to interact with the Paynow API.
    """
    def __init__(self, ipn_callback_url: str):
        self.config: Optional[PaynowConfig] = None
        self.paynow_sdk: Optional[PaynowSDK] = None
        try:
            self.config = PaynowConfig.objects.first()
            if not self.config:
                logger.error("PaynowConfig not found in database. Please configure Paynow settings.")
            else:
                # The full URL is constructed from the base URL and the path passed from the calling service.
                # This is more robust than having the service guess the URL via reverse().
                base_url = getattr(settings, 'SITE_URL', 'https://your-domain.com') # Ensure SITE_URL is configured
                result_url = f"{base_url.rstrip('/')}{ipn_callback_url}"
                
                # For server-to-server API calls like this, the return_url is not used by the user's browser.
                # It's safe to set it to the same as the result_url (IPN handler).
                return_url = result_url

                self.paynow_sdk = PaynowSDK(
                    integration_id=self.config.integration_id,
                    integration_key=self.config.integration_key,
                    result_url=result_url,
                    return_url=return_url
                )
                logger.debug(f"PaynowSDK wrapper successfully initialized for Integration ID: {self.config.integration_id}.")
        except Exception as e: # Catch any exception during initialization
            logger.error(f"Error initializing PaynowService: {type(e).__name__}: {e}", exc_info=True)
            self.paynow_sdk = None # Ensure SDK is None if init fails
    
    def initiate_express_checkout_payment(
        self,
        amount: Decimal, reference: str, phone_number: str, email: str,
        paynow_method_type: str, description: str = "Wallet Deposit"
    ) -> Dict[str, Any]:
        """
        Initiates an Express Checkout payment via Paynow using the SDK.
        """
        if not self.paynow_sdk:
            logger.error("Paynow SDK not initialized when initiate_express_checkout_payment was called. Configuration likely missing or failed to load.")
            return {"success": False, "message": "Paynow service not configured or failed to initialize."}
        
        logger.debug(f"Attempting to initiate Paynow Express Checkout for reference: {reference}, amount: {amount}, phone: {phone_number}, method: {paynow_method_type}.")
        try:
            result = self.paynow_sdk.initiate_express_checkout(
                amount=amount,
                reference=reference,
                phone_number=phone_number,
                email=email,
                paynow_method_type=paynow_method_type,
                description=description
            )
            if result['success']:
                logger.info(f"Paynow Express Checkout initiated successfully for reference: {reference}. PaynowRef: {result.get('paynow_reference')}.")
            else:
                logger.warning(f"Paynow Express Checkout initiation failed for reference: {reference}. Reason: {result.get('message')}.")
            return result
        except Exception as e: # Catch any unexpected exceptions from the SDK call
            logger.error(f"Error during Paynow SDK initiate_express_checkout for reference {reference}: {type(e).__name__}: {e}", exc_info=True)
            return {"success": False, "message": f"Paynow initiation failed: {type(e).__name__} - {str(e)}"}
    
    def check_transaction_status(self, poll_url: str) -> Dict[str, Any]:
        """
        Delegates transaction status check to the PaynowSDK wrapper.
        """
        if not self.paynow_sdk:
            return {"success": False, "message": "Paynow SDK not initialized. Configuration missing."}
        
        logger.debug(f"Attempting to check Paynow transaction status using poll URL: {poll_url}.")
        try:
            result = self.paynow_sdk.check_transaction_status(poll_url)
            if result['success']:
                logger.info(f"Paynow status check successful for {poll_url}. Status: {result.get('status')}, Paid: {result.get('paid')}.")
            else:
                logger.warning(f"Paynow status check failed for {poll_url}. Reason: {result.get('message')}.")
            return result
        except Exception as e:
            logger.error(f"Error during Paynow SDK check_transaction_status for {poll_url}: {type(e).__name__}: {e}", exc_info=True)
            return {"success": False, "message": f"Error checking status: {type(e).__name__} - {str(e)}"}

    def verify_ipn_hash(self, ipn_data: Dict[str, Any]) -> bool:
        """
        Verifies the hash of an incoming IPN message to ensure it's authentic.
        Delegates the actual hash generation and comparison to the PaynowSDK.
        """
        if not self.paynow_sdk:
            logger.error("Paynow SDK not initialized when verify_ipn_hash was called.")
            return False
        
        logger.debug(f"Verifying IPN hash for reference: {ipn_data.get('reference')}")
        try:
            return self.paynow_sdk.verify_ipn_hash(ipn_data)
        except Exception as e:
            logger.error(f"Error during Paynow SDK verify_ipn_hash: {e}", exc_info=True)
            return False

    def initiate_payment(
        self,
        booking: Booking,
        amount: Decimal,
        phone_number: str,
        email: str,
        payment_method: str,
        description: str = "Tour Booking Payment"
    ) -> Dict[str, Any]:
        """
        Initiates a Paynow payment for a booking.
        Creates a Payment record and calls the Paynow API.
        
        Args:
            booking: The Booking instance
            amount: Payment amount
            phone_number: Customer phone number for mobile money
            email: Customer email
            payment_method: One of 'ecocash', 'onemoney', 'innbucks'
            description: Payment description
        
        Returns:
            Dict with payment result including success status, poll_url, etc.
        """
        if not self.paynow_sdk:
            logger.error("Paynow SDK not initialized when initiate_payment was called.")
            return {"success": False, "message": "Paynow service not configured."}
        
        # Map payment method to Paynow method type and Payment model choice
        payment_method_map = {
            'ecocash': ('ecocash', Payment.PaymentMethod.PAYNOW_ECOCASH),
            'onemoney': ('onemoney', Payment.PaymentMethod.PAYNOW_ONEMONEY),
            'innbucks': ('innbucks', Payment.PaymentMethod.PAYNOW_INNBUCKS)
        }
        
        if payment_method not in payment_method_map:
            logger.error(f"Invalid payment method: {payment_method}")
            return {"success": False, "message": f"Invalid payment method: {payment_method}"}
        
        paynow_method_type, payment_model_choice = payment_method_map[payment_method]
        
        # Create a Payment record
        try:
            payment = Payment.objects.create(
                booking=booking,
                amount=amount,
                currency='USD',
                status=Payment.PaymentStatus.PENDING,
                payment_method=payment_model_choice,
                notes=f"Paynow {payment_method} payment initiated"
            )
            
            # Generate a unique reference for this payment
            payment_reference = f"{booking.booking_reference}-PAY-{payment.id}"
            
            # Initiate the Paynow payment
            result = self.initiate_express_checkout_payment(
                amount=amount,
                reference=payment_reference,
                phone_number=phone_number,
                email=email,
                paynow_method_type=paynow_method_type,
                description=description
            )
            
            # Update payment record with transaction reference
            if result.get('success'):
                payment.transaction_reference = result.get('paynow_reference', '')
                payment.notes = f"{payment.notes}. Paynow reference: {result.get('paynow_reference')}"
                payment.save()
                
                # Add payment ID to result for tracking
                result['payment_id'] = str(payment.id)
                logger.info(f"Payment record created with ID {payment.id} for booking {booking.booking_reference}")
            else:
                # Mark payment as failed
                payment.status = Payment.PaymentStatus.FAILED
                payment.notes = f"{payment.notes}. Failed: {result.get('message', 'Unknown error')}"
                payment.save()
                logger.warning(f"Payment initiation failed for booking {booking.booking_reference}: {result.get('message')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating payment record or initiating payment: {e}", exc_info=True)
            return {"success": False, "message": f"Error processing payment: {str(e)}"}
