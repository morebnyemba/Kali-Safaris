"""
WhatsApp payment flow handler for CBZ/iVeri EcoCash integration.

This service manages the EcoCash payment flow through WhatsApp:
1. Collects mobile number (or uses WhatsApp number)
2. Sends iVeri Debit request (triggers STK Push to customer's phone)
3. Waits for customer to enter EcoCash PIN
4. Processes the response and updates booking

Unlike Omari, there is NO OTP step — iVeri uses EcoCash's native STK Push.
Card payments are handled on the website only, not through WhatsApp.
"""
import logging
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any

from django.utils import timezone
from django.db import transaction as db_transaction

from conversations.models import Contact
from customer_data.models import Booking, Payment
from .models import CBZTransaction
from .services import IVeriClient, IVeriConfig
from .constants import RESULT_CODE_SUCCESS, STATUS_APPROVED
from django.conf import settings


logger = logging.getLogger(__name__)


def _mask_msisdn(msisdn: str) -> str:
    """Return a lightly masked MSISDN for logging."""
    if not msisdn:
        return ""
    tail = msisdn[-4:] if len(msisdn) >= 4 else msisdn
    return f"***{tail}"


class WhatsAppCBZPaymentHandler:
    """Handles CBZ/iVeri EcoCash payment flow through WhatsApp conversations."""

    PAYMENT_STATE_KEY = '_cbz_payment_state'

    def __init__(self):
        """Initialize iVeri client preferring DB config with settings fallback."""
        try:
            self.client = IVeriClient()
            logger.info("iVeri client configured from DB active config")
        except ValueError:
            # Fallback to environment-based settings
            self.client = IVeriClient(IVeriConfig(
                portal_url=getattr(settings, 'CBZ_PORTAL_URL', 'https://portal.host.iveri.com'),
                certificate_id=getattr(settings, 'CBZ_CERTIFICATE_ID', ''),
                application_id=getattr(settings, 'CBZ_APPLICATION_ID', ''),
                mode=getattr(settings, 'CBZ_MODE', 'Test'),
            ))
            logger.warning("iVeri client configured from settings (no active DB config found)")

    def initiate_ecocash_payment(
        self,
        contact: Contact,
        booking: Booking,
        amount: Decimal,
        currency: str = 'USD',
        msisdn: str = None,
    ) -> Dict[str, Any]:
        """
        Initiate EcoCash payment via iVeri STK Push.

        The customer receives a prompt on their phone to enter their EcoCash PIN.
        No OTP step is needed — this is simpler than the Omari flow.

        Args:
            contact: WhatsApp contact
            booking: Booking to pay for
            amount: Amount to charge
            currency: 'USD' or 'ZWG'
            msisdn: Optional payment phone number (overrides contact.whatsapp_id)

        Returns:
            dict with 'success', 'message', 'reference', 'transaction'
        """
        # Use provided msisdn or extract from contact whatsapp_id
        if not msisdn:
            msisdn = self._format_msisdn(contact.whatsapp_id)
        else:
            msisdn = self._format_msisdn(msisdn)

        # Generate unique merchant reference
        merchant_ref = f"KS-{uuid.uuid4().hex[:12].upper()}"

        logger.info(
            "CBZ EcoCash payment start | contact=%s booking=%s amount=%s %s msisdn=%s ref=%s",
            contact.id,
            getattr(booking, 'booking_reference', None),
            amount, currency,
            _mask_msisdn(msisdn),
            merchant_ref,
        )

        # Create transaction record before API call
        txn = CBZTransaction.objects.create(
            merchant_reference=merchant_ref,
            payment_type=CBZTransaction.PaymentType.ECOCASH,
            msisdn=msisdn,
            amount=amount,
            currency=currency,
            command='Debit',
            status=CBZTransaction.TransactionStatus.INITIATED,
            booking=booking,
        )

        try:
            # Call iVeri EcoCash debit endpoint (triggers STK Push)
            response = self.client.debit_ecocash(
                mobile=msisdn,
                amount=amount,
                currency=currency,
                merchant_reference=merchant_ref,
            )

            result = IVeriClient.get_result(response)
            is_approved = IVeriClient.is_approved(response)

            # Update transaction with response
            txn.result_code = result.get('result_code')
            txn.result_description = result.get('result_description')
            txn.transaction_index = result.get('transaction_index')
            txn.authorisation_code = result.get('authorisation_code')
            txn.request_id = result.get('request_id')

            if is_approved:
                txn.status = CBZTransaction.TransactionStatus.APPROVED
                txn.completed_at = timezone.now()
                txn.save()

                # Create Payment record and update booking
                self._record_successful_payment(txn, booking)

                # Store success state for flow
                self._set_payment_state(contact, {
                    'reference': merchant_ref,
                    'status': 'approved',
                    'completed': True,
                })

                logger.info(
                    "CBZ EcoCash payment APPROVED | contact=%s booking=%s ref=%s txn_index=%s",
                    contact.id,
                    booking.booking_reference,
                    merchant_ref,
                    result.get('transaction_index'),
                )

                return {
                    'success': True,
                    'message': 'Payment approved successfully!',
                    'reference': merchant_ref,
                    'transaction': txn,
                    'authorisation_code': result.get('authorisation_code'),
                }
            else:
                # Payment was not approved
                txn.status = CBZTransaction.TransactionStatus.DECLINED
                txn.save()

                error_desc = result.get('result_description', 'Payment was not approved')
                logger.warning(
                    "CBZ EcoCash payment DECLINED | contact=%s booking=%s ref=%s code=%s desc=%s",
                    contact.id,
                    booking.booking_reference,
                    merchant_ref,
                    result.get('result_code'),
                    error_desc,
                )

                return {
                    'success': False,
                    'message': error_desc,
                    'reference': merchant_ref,
                    'result_code': result.get('result_code'),
                }

        except Exception as e:
            txn.status = CBZTransaction.TransactionStatus.FAILED
            txn.result_description = str(e)[:500]
            txn.save()

            logger.exception(
                "CBZ EcoCash payment EXCEPTION | contact=%s booking=%s ref=%s msisdn=%s",
                contact.id,
                getattr(booking, 'booking_reference', None),
                merchant_ref,
                _mask_msisdn(msisdn),
            )

            return {
                'success': False,
                'message': f'Payment service error: {str(e)}',
                'reference': merchant_ref,
            }

    def check_payment_status(self, merchant_reference: str) -> Dict[str, Any]:
        """
        Check status of a payment transaction.

        Args:
            merchant_reference: Merchant reference for the transaction

        Returns:
            dict with transaction status details
        """
        try:
            response = self.client.query_transaction(merchant_reference)
            result = IVeriClient.get_result(response)
            is_approved = IVeriClient.is_approved(response)

            # Update local transaction record if found
            txn = CBZTransaction.objects.filter(merchant_reference=merchant_reference).first()
            if txn:
                txn.result_code = result.get('result_code')
                txn.result_description = result.get('result_description')
                txn.transaction_index = result.get('transaction_index')
                if is_approved and txn.status != CBZTransaction.TransactionStatus.APPROVED:
                    txn.status = CBZTransaction.TransactionStatus.APPROVED
                    txn.completed_at = timezone.now()
                    # Record payment if not already done
                    if txn.booking:
                        self._record_successful_payment(txn, txn.booking)
                txn.save()

            return {
                'success': True,
                'is_approved': is_approved,
                'status': result.get('status'),
                'data': result,
            }
        except Exception as e:
            logger.exception(f"Failed to query CBZ payment status for {merchant_reference}")
            return {
                'success': False,
                'message': str(e),
            }

    def cancel_payment(self, contact: Contact) -> bool:
        """Cancel pending payment for contact."""
        payment_state = self._get_payment_state(contact)
        if payment_state and payment_state.get('reference'):
            CBZTransaction.objects.filter(
                merchant_reference=payment_state['reference']
            ).update(
                status=CBZTransaction.TransactionStatus.FAILED,
                result_description='Cancelled by user',
            )
        self._clear_payment_state(contact)
        return True

    # ─── Private Helper Methods ──────────────────────────────────────

    def _format_msisdn(self, whatsapp_id: str) -> str:
        """Format WhatsApp ID to msisdn format (2637XXXXXXXX)."""
        digits = ''.join(c for c in whatsapp_id if c.isdigit())

        if not digits.startswith('263'):
            if digits.startswith('0'):
                digits = '263' + digits[1:]
            elif len(digits) == 9:
                digits = '263' + digits

        return digits

    def _record_successful_payment(self, txn: CBZTransaction, booking: Booking):
        """
        Create a Payment record and update the booking after successful payment.
        """
        try:
            with db_transaction.atomic():
                # Create Payment record
                Payment.objects.create(
                    booking=booking,
                    amount=txn.amount,
                    currency=txn.currency,
                    status=Payment.PaymentStatus.SUCCESSFUL,
                    payment_method=(
                        Payment.PaymentMethod.CBZ_ECOCASH
                        if txn.payment_type == CBZTransaction.PaymentType.ECOCASH
                        else Payment.PaymentMethod.CBZ_CARD
                    ),
                    transaction_reference=txn.merchant_reference,
                    notes=f"CBZ/iVeri {txn.payment_type} payment. Auth: {txn.authorisation_code or 'N/A'}",
                )

                # Refresh and update booking totals
                booking = Booking.objects.select_for_update().get(id=booking.id)
                booking.update_amount_paid(commit=False)

                if booking.amount_paid >= booking.total_amount:
                    booking.payment_status = Booking.PaymentStatus.PAID
                elif booking.amount_paid > 0:
                    booking.payment_status = Booking.PaymentStatus.DEPOSIT_PAID

                booking.save(update_fields=['amount_paid', 'payment_status', 'updated_at'])

                logger.info(
                    "CBZ payment recorded | booking=%s amount=%s %s status=%s total_paid=%s",
                    booking.booking_reference,
                    txn.amount, txn.currency,
                    booking.payment_status,
                    booking.amount_paid,
                )
        except Exception as e:
            logger.error(
                "Failed to record CBZ payment | txn=%s booking=%s error=%s",
                txn.merchant_reference,
                booking.booking_reference,
                str(e),
                exc_info=True,
            )

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
_cbz_payment_handler = None


def get_cbz_payment_handler() -> WhatsAppCBZPaymentHandler:
    """Get singleton payment handler instance."""
    global _cbz_payment_handler
    if _cbz_payment_handler is None:
        _cbz_payment_handler = WhatsAppCBZPaymentHandler()
    return _cbz_payment_handler
