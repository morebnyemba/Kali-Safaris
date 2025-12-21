"""
WhatsApp payment flow handler for Omari integration.

This service manages the payment flow through WhatsApp:
1. Initiates Omari payment
2. Sends OTP reference to customer
3. Collects OTP from customer
4. Completes payment
5. Updates booking status
"""
import logging
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any

from django.utils import timezone
from django.db import transaction as db_transaction

from conversations.models import Contact, Message
from customer_data.models import Booking
from .models import OmariTransaction, OmariUser
from .services import OmariClient, OmariConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class WhatsAppPaymentHandler:
    """Handles Omari payment flow through WhatsApp conversations."""
    
    PAYMENT_STATE_KEY = '_omari_payment_state'
    
    def __init__(self):
        """Initialize Omari client from settings."""
        self.client = OmariClient(OmariConfig(
            base_url=getattr(settings, 'OMARI_API_BASE_URL', 
                           'https://omari.v.co.zw/uat/vsuite/omari/api/merchant/api/payment'),
            merchant_key=getattr(settings, 'OMARI_MERCHANT_KEY', ''),
        ))
    
    def initiate_payment(
        self, 
        contact: Contact, 
        booking: Booking,
        amount: Decimal,
        currency: str = 'USD',
        channel: str = 'WEB'
    ) -> Dict[str, Any]:
        """
        Initiate Omari payment for a booking.
        
        Args:
            contact: WhatsApp contact
            booking: Booking to pay for
            amount: Amount to charge
            currency: 'USD' or 'ZWG'
            channel: 'WEB' or 'POS'
            
        Returns:
            dict with 'success', 'otp_reference', 'reference', 'message'
        """
        # Extract msisdn from contact whatsapp_id
        msisdn = self._format_msisdn(contact.whatsapp_id)
        
        # Generate reference
        reference = str(uuid.uuid4())
        
        try:
            # Call Omari auth endpoint
            result = self.client.auth(
                msisdn=msisdn,
                reference=reference,
                amount=float(amount),
                currency=currency,
                channel=channel
            )
            
            if result.get('error'):
                logger.error(f"Omari auth failed for contact {contact.id}: {result}")
                return {
                    'success': False,
                    'message': result.get('message', 'Payment initiation failed'),
                    'reference': reference,
                }
            
            # Create transaction record
            txn = OmariTransaction.objects.create(
                reference=reference,
                msisdn=msisdn,
                amount=amount,
                currency=currency,
                channel=channel,
                otp_reference=result.get('otpReference'),
                status='OTP_SENT',
                response_code=result.get('responseCode'),
                response_message=result.get('message'),
                booking=booking,
            )
            
            # Store payment state in contact conversation context
            self._set_payment_state(contact, {
                'reference': reference,
                'otp_reference': result.get('otpReference'),
                'booking_id': booking.id,
                'amount': str(amount),
                'currency': currency,
                'awaiting_otp': True,
                'initiated_at': timezone.now().isoformat(),
            })
            
            logger.info(f"Initiated Omari payment {reference} for booking {booking.booking_reference}")
            
            return {
                'success': True,
                'otp_reference': result.get('otpReference'),
                'reference': reference,
                'message': result.get('message', 'OTP sent successfully'),
                'transaction': txn,
            }
            
        except Exception as e:
            logger.exception(f"Failed to initiate Omari payment for contact {contact.id}")
            return {
                'success': False,
                'message': f'Payment initiation error: {str(e)}',
                'reference': reference,
            }
    
    def process_otp_input(self, contact: Contact, otp: str) -> Dict[str, Any]:
        """
        Process OTP input from customer and complete payment.
        
        Args:
            contact: WhatsApp contact
            otp: OTP code entered by customer
            
        Returns:
            dict with 'success', 'message', 'payment_reference', 'booking'
        """
        payment_state = self._get_payment_state(contact)
        
        if not payment_state or not payment_state.get('awaiting_otp'):
            return {
                'success': False,
                'message': 'No pending payment found. Please initiate a payment first.',
            }
        
        reference = payment_state.get('reference')
        msisdn = self._format_msisdn(contact.whatsapp_id)
        
        try:
            # Complete payment with OTP
            result = self.client.request(
                msisdn=msisdn,
                reference=reference,
                otp=otp
            )
            
            # Update transaction
            txn = OmariTransaction.objects.filter(reference=reference).first()
            if txn:
                txn.payment_reference = result.get('paymentReference')
                txn.debit_reference = result.get('debitReference')
                txn.response_code = result.get('responseCode')
                txn.response_message = result.get('message')
                
                if not result.get('error') and result.get('responseCode') == '000':
                    txn.status = 'SUCCESS'
                    txn.completed_at = timezone.now()
                    # Auto-enroll Omari user upon successful payment
                    try:
                        OmariUser.objects.update_or_create(
                            msisdn=msisdn,
                            defaults={
                                'is_active': True,
                                'verified_at': timezone.now()
                            }
                        )
                    except Exception:
                        logger.warning("Failed to auto-enroll Omari user %s", msisdn)
                    
                    # Update booking
                    if txn.booking:
                        with db_transaction.atomic():
                            booking = Booking.objects.select_for_update().get(id=txn.booking.id)
                            booking.amount_paid += txn.amount
                            
                            # Update payment status based on amount
                            if booking.amount_paid >= booking.total_amount:
                                booking.payment_status = Booking.PaymentStatus.PAID
                            elif booking.amount_paid > 0:
                                booking.payment_status = Booking.PaymentStatus.DEPOSIT_PAID
                            
                            booking.save(update_fields=['amount_paid', 'payment_status', 'updated_at'])
                            
                            logger.info(f"Updated booking {booking.booking_reference} payment status to {booking.payment_status}")
                else:
                    txn.status = 'FAILED'
                
                txn.save()
            
            # Clear payment state
            self._clear_payment_state(contact)
            
            if not result.get('error') and result.get('responseCode') == '000':
                return {
                    'success': True,
                    'message': 'Payment completed successfully!',
                    'payment_reference': result.get('paymentReference'),
                    'booking': txn.booking if txn else None,
                    'transaction': txn,
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Payment failed'),
                    'response_code': result.get('responseCode'),
                }
                
        except Exception as e:
            logger.exception(f"Failed to process OTP for contact {contact.id}")
            return {
                'success': False,
                'message': f'Payment processing error: {str(e)}',
            }
    
    def check_payment_status(self, reference: str) -> Dict[str, Any]:
        """
        Check status of a payment transaction.
        
        Args:
            reference: UUID reference of the transaction
            
        Returns:
            dict with transaction status details
        """
        try:
            result = self.client.query(reference)
            return {
                'success': not result.get('error'),
                'status': result.get('status'),
                'data': result,
            }
        except Exception as e:
            logger.exception(f"Failed to query payment status for {reference}")
            return {
                'success': False,
                'message': str(e),
            }
    
    def is_awaiting_otp(self, contact: Contact) -> bool:
        """Check if contact is awaiting OTP input for a payment."""
        payment_state = self._get_payment_state(contact)
        return payment_state.get('awaiting_otp', False) if payment_state else False
    
    def get_pending_payment(self, contact: Contact) -> Optional[Dict[str, Any]]:
        """Get details of pending payment for contact."""
        return self._get_payment_state(contact)
    
    def cancel_payment(self, contact: Contact) -> bool:
        """Cancel pending payment for contact."""
        payment_state = self._get_payment_state(contact)
        if payment_state and payment_state.get('reference'):
            # Mark transaction as failed
            OmariTransaction.objects.filter(
                reference=payment_state['reference']
            ).update(
                status='FAILED',
                response_message='Cancelled by user'
            )
        self._clear_payment_state(contact)
        return True
    
    # Private helper methods
    
    def _format_msisdn(self, whatsapp_id: str) -> str:
        """Format WhatsApp ID to Omari msisdn format (2637XXXXXXXX)."""
        # Remove any non-digit characters
        digits = ''.join(c for c in whatsapp_id if c.isdigit())
        
        # Ensure it starts with 263
        if not digits.startswith('263'):
            if digits.startswith('0'):
                digits = '263' + digits[1:]
            elif len(digits) == 9:  # Local format
                digits = '263' + digits
        
        return digits

    def is_omari_user(self, contact: Contact) -> str:
        """Return 'true' if verified, else 'unknown' to allow API to enforce."""
        try:
            msisdn = self._format_msisdn(contact.whatsapp_id)
            if OmariUser.objects.filter(msisdn=msisdn, is_active=True).exists():
                return 'true'
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _get_payment_state(self, contact: Contact) -> Optional[Dict[str, Any]]:
        """Get payment state from contact conversation context."""
        return contact.conversation_context.get(self.PAYMENT_STATE_KEY)
    
    def _set_payment_state(self, contact: Contact, state: Dict[str, Any]) -> None:
        """Store payment state in contact conversation context."""
        if not isinstance(contact.conversation_context, dict):
            contact.conversation_context = {}
        contact.conversation_context[self.PAYMENT_STATE_KEY] = state
        contact.save(update_fields=['conversation_context'])
    
    def _clear_payment_state(self, contact: Contact) -> None:
        """Clear payment state from contact conversation context."""
        if isinstance(contact.conversation_context, dict) and self.PAYMENT_STATE_KEY in contact.conversation_context:
            del contact.conversation_context[self.PAYMENT_STATE_KEY]
            contact.save(update_fields=['conversation_context'])


# Singleton instance
_payment_handler = None

def get_payment_handler() -> WhatsAppPaymentHandler:
    """Get singleton payment handler instance."""
    global _payment_handler
    if _payment_handler is None:
        _payment_handler = WhatsAppPaymentHandler()
    return _payment_handler
