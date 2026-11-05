"""
Staff verification of manually reported payments (bank transfer / proof of payment).

Shared by the Django admin actions and the dashboard's Payments page, so both
paths lock the same rows, move the booking the same way and message the
customer the same way. WhatsApp messages go out after commit: a slow or failed
send never holds row locks or rolls back an approval.
"""
import logging

from django.db import transaction
from django.utils import timezone

from .models import Booking, Payment

logger = logging.getLogger(__name__)


class PaymentReviewError(Exception):
    """The payment can't be reviewed (already decided, or gone)."""


def _stamp(payment, verb, user, reason=''):
    who = getattr(user, 'username', None) or 'staff'
    line = f"[{verb} by {who} on {timezone.now().strftime('%Y-%m-%d %H:%M')}]"
    if reason:
        line += f" {reason}"
    payment.notes = f"{payment.notes}\n{line}" if payment.notes else line


def _send_whatsapp(booking, body):
    try:
        contact = booking.customer.contact if booking.customer_id else None
    except Exception:
        contact = None
    if not contact:
        return
    from meta_integration.utils import send_whatsapp_message

    try:
        send_whatsapp_message(contact.whatsapp_id, 'text', {'body': body}, contact.associated_app_config)
    except Exception:
        logger.exception("Payment review: WhatsApp notice failed for booking %s", booking.booking_reference)


def _lock_pending(payment_id):
    payment = Payment.objects.select_for_update().filter(pk=payment_id).first()
    if payment is None:
        raise PaymentReviewError("Payment not found.")
    if payment.status != Payment.PaymentStatus.PENDING:
        raise PaymentReviewError(f"This payment is already {payment.get_status_display().lower()}.")
    return payment


def approve_payment(payment_id, user):
    """PENDING -> SUCCESSFUL; recalculates the booking and confirms it if covered."""
    with transaction.atomic():
        payment = _lock_pending(payment_id)
        booking = Booking.objects.select_for_update().get(pk=payment.booking_id) if payment.booking_id else None

        payment.status = Payment.PaymentStatus.SUCCESSFUL
        _stamp(payment, 'Approved', user)
        payment.save()

        if booking is not None:
            booking.update_amount_paid(commit=False)
            fields = ['amount_paid', 'payment_status', 'updated_at']
            if booking.payment_status not in (Booking.PaymentStatus.CANCELLED, Booking.PaymentStatus.REFUNDED):
                if booking.total_amount and booking.amount_paid >= booking.total_amount:
                    booking.payment_status = Booking.PaymentStatus.PAID
                elif booking.amount_paid > 0:
                    booking.payment_status = Booking.PaymentStatus.DEPOSIT_PAID
            was_updated, _ = booking.update_to_shared_reference(commit=False)
            if was_updated:
                fields.append('booking_reference')
            booking.save(update_fields=fields)  # holds as AWAITING_DETAILS if passengers are incomplete

    if booking is not None:
        body = (
            f"✅ *Payment Approved!*\n\n"
            f"Your payment of ${payment.amount:.2f} for booking *{booking.booking_reference}* has been approved.\n\n"
            f"Tour: {booking.tour_name}\n"
            f"Date: {booking.start_date.strftime('%B %d, %Y')}"
            f"{' · ' + booking.departure_display if booking.start_time else ''}\n"
            f"Amount Paid: ${booking.amount_paid:.2f}\n"
            f"Total: ${booking.total_amount:.2f}\n"
        )
        if booking.amount_paid >= booking.total_amount:
            body += "\n✅ Your booking is now fully paid!\n"
        else:
            body += f"\nBalance Due: ${booking.total_amount - booking.amount_paid:.2f}\n"
        if booking.payment_status == Booking.PaymentStatus.AWAITING_DETAILS:
            body += (
                "\n📋 *Next Step:* We still need complete details (name, age, nationality, "
                "gender and ID/passport number) for every passenger before your booking "
                "is confirmed. Please send them to us here."
            )
        transaction.on_commit(lambda: _send_whatsapp(booking, body))
    return payment


def reject_payment(payment_id, user, reason=''):
    """PENDING -> FAILED; the booking's totals are unchanged."""
    reason = (reason or '').strip()
    with transaction.atomic():
        payment = _lock_pending(payment_id)
        payment.status = Payment.PaymentStatus.FAILED
        _stamp(payment, 'Rejected', user, reason)
        payment.save()
        booking = payment.booking

    if booking is not None:
        body = (
            f"❌ *Payment Not Approved*\n\n"
            f"Unfortunately, we couldn't verify your payment of ${payment.amount:.2f} for booking *{booking.booking_reference}*.\n\n"
            + (f"Reason: {reason}\n\n" if reason else "")
            + "Please contact our finance team or try submitting the payment again with a clear proof of payment.\n\n"
            "You can record a new payment by typing *manual payment*."
        )
        transaction.on_commit(lambda: _send_whatsapp(booking, body))
    return payment
