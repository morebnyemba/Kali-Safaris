"""
Customer emails about bookings and payments (all branded, all via
notifications.emailing.send_branded_email, so every send is logged and deduped).

    booking_confirmation  — booking_emails.send_booking_confirmation (first confirmed payment)
    payment_receipt       — every later successful payment (instalments, balance)
    balance_reminder      — balance_reminders (upcoming / final / moved to hold)
    booking_rescheduled   — customer picked a new date for an on-hold booking
    payment_rejected      — staff couldn't verify a reported (manual) payment
"""
import logging

from notifications.emailing import send_branded_email

from .booking_emails import customer_email
from .models import Booking, Payment

logger = logging.getLogger(__name__)


def booking_context(booking, **extra):
    from .manage_links import balance_due, manage_url, needs_id
    from .payment_plan import balance_due_date

    name = (booking.customer.get_full_name() if booking.customer_id else '') or ''
    return {
        'booking': booking,
        'first_name': name.split(' ')[0] if name else '',
        'departure': booking.departure_display,
        'balance': balance_due(booking),
        'due_by': balance_due_date(booking),
        'manage_url': manage_url(booking),
        'missing_ids': [t.name for t in booking.travelers.all() if needs_id(t)],
        'travelers': list(booking.travelers.order_by('traveler_type', 'name')),
        **extra,
    }


def receipt_wanted(payment) -> bool:
    """
    A receipt for each successful payment *after* the booking was confirmed by
    email — the first payment is covered by the booking confirmation itself.
    """
    booking = payment.booking
    return (
        payment.status == Payment.PaymentStatus.SUCCESSFUL
        and booking is not None
        and booking.confirmation_email_sent_at is not None
        and booking.confirmation_email_sent_at <= payment.created_at
    )


def send_payment_receipt(payment_id):
    payment = Payment.objects.select_related('booking__customer').filter(pk=payment_id).first()
    if payment is None or not receipt_wanted(payment):
        return None
    booking = payment.booking
    return send_branded_email(
        template='payment_receipt', to=customer_email(booking), booking=booking,
        key=f'payment-receipt:{payment.pk}',
        subject=f"Payment received: ${payment.amount:.2f} for {booking.tour_name} — {booking.booking_reference}",
        preheader='Thank you! Here is your receipt and what is left to pay.',
        context=booking_context(booking, payment=payment),
    )


def send_booking_rescheduled(booking_id, held_from_date=None):
    booking = Booking.objects.select_related('customer').filter(pk=booking_id).first()
    if booking is None:
        return None
    return send_branded_email(
        template='booking_rescheduled', to=customer_email(booking), booking=booking,
        key=f'booking-rescheduled:{booking.pk}:{booking.start_date.isoformat()}',
        subject=f"New date confirmed: {booking.tour_name} on {booking.start_date:%d %b %Y} — {booking.booking_reference}",
        preheader='Your booking has moved to its new date and your payment carried over.',
        context=booking_context(booking, held_from_date=held_from_date),
    )


def send_payment_rejected(payment_id, reason=''):
    payment = Payment.objects.select_related('booking__customer').filter(pk=payment_id).first()
    if payment is None or payment.booking is None:
        return None
    booking = payment.booking
    return send_branded_email(
        template='payment_rejected', to=customer_email(booking), booking=booking,
        key=f'payment-rejected:{payment.pk}',
        subject=f"We couldn't verify your payment for {booking.booking_reference}",
        preheader='Nothing has changed on your booking — here is how to sort it out.',
        context=booking_context(booking, payment=payment, reason=reason),
    )


# --- Booking statements: one receipt per booking listing every payment ---

STATEMENT_STATUSES = (
    Booking.PaymentStatus.DEPOSIT_PAID, Booking.PaymentStatus.PAID,
    Booking.PaymentStatus.AWAITING_DETAILS, Booking.PaymentStatus.ON_HOLD,
)
_INFORMING_TEMPLATES = ('booking_confirmation', 'payment_receipt', 'booking_rescheduled', 'booking_statement')


def statement_candidates(include_past=False):
    """Bookings with money received that may still need a receipt (eligibility is re-checked per booking)."""
    from django.db.models import Q
    from django.utils import timezone

    qs = Booking.objects.filter(payment_status__in=STATEMENT_STATUSES, amount_paid__gt=0).select_related('customer')
    if not include_past:
        qs = qs.filter(Q(start_date__gte=timezone.localdate()) | Q(payment_status=Booking.PaymentStatus.ON_HOLD))
    return qs.order_by('start_date', 'pk')


def statement_skip_reason(booking):
    """Why this booking doesn't get a statement, or '' if it should."""
    from notifications.models import EmailLog

    if not customer_email(booking):
        return 'no email address'
    payments = booking.payments.filter(status=Payment.PaymentStatus.SUCCESSFUL)
    last = payments.order_by('-created_at').values_list('created_at', flat=True).first()
    if last is None:
        return 'no successful payments'
    if EmailLog.objects.filter(key=f'booking-statement:{booking.pk}', status=EmailLog.Status.SENT).exists():
        return 'statement already sent'
    informed = EmailLog.objects.filter(booking=booking, status=EmailLog.Status.SENT,
                                       template__in=_INFORMING_TEMPLATES, sent_at__gte=last).exists()
    if informed or (booking.confirmation_email_sent_at and booking.confirmation_email_sent_at >= last):
        return 'already emailed after the last payment'
    return ''


def send_booking_statement(booking_id):
    booking = Booking.objects.select_related('customer').filter(pk=booking_id).first()
    if booking is None or statement_skip_reason(booking):
        return None
    payments = list(booking.payments.filter(status=Payment.PaymentStatus.SUCCESSFUL).order_by('created_at'))
    return send_branded_email(
        template='booking_statement', to=customer_email(booking), booking=booking,
        key=f'booking-statement:{booking.pk}',
        subject=f"Your booking & payment receipt — {booking.tour_name}, {booking.start_date:%d %b %Y} ({booking.booking_reference})",
        preheader='Every payment we have received for your booking, and what is left to do.',
        context=booking_context(booking, payments=payments),
    )
