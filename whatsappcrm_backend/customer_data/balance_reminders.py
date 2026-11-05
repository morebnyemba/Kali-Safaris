"""
Balance reminders and the unpaid-balance rule for deposit / instalment bookings.

Runs daily (Celery beat). For a booking with money paid and a balance left:

1. 'upcoming' — 7 days before the balance is due (BALANCE_DUE_DAYS_BEFORE
   days before the trip).
2. 'final' — on (or after) the due date, once: pay within HOLD_GRACE_DAYS or
   the booking is moved off this cruise.
3. 'moved' — still unpaid HOLD_GRACE_DAYS after the final notice: the booking
   becomes ON_HOLD. Its seats are released (ON_HOLD doesn't hold seats), the
   money paid stays on the booking as credit, and the customer picks a new date
   on their secure link (manage_links.reschedule). Staff are told.
4. Staff are alerted when a booking has sat ON_HOLD for HOLD_CREDIT_DAYS.

Customers hear by email (when we have an address) and WhatsApp (delivered only
inside WhatsApp's 24-hour window; otherwise Meta rejects it and email carries
it). A booking is moved only after a final notice actually reached them.
`balance_reminder_sent_on` keeps reminders to one per booking per day.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .booking_emails import CONTACT, customer_email
from .manage_links import balance_due, manage_url, needs_id
from .models import Booking
from .payment_plan import BALANCE_DUE_DAYS_BEFORE, HOLD_CREDIT_DAYS, HOLD_GRACE_DAYS, INSTALMENT_MIN_DAYS_AHEAD, balance_due_date

logger = logging.getLogger(__name__)

UPCOMING_DAYS_BEFORE_DUE = 7
OWING_STATUSES = (Booking.PaymentStatus.DEPOSIT_PAID, Booking.PaymentStatus.AWAITING_DETAILS)


def hold_date(booking):
    """Day the booking is moved if still unpaid (needs the final notice to have gone out)."""
    return booking.final_notice_sent_on + timedelta(days=HOLD_GRACE_DAYS) if booking.final_notice_sent_on else None


def reminder_kind(booking, today):
    """'upcoming' | 'final' | None for this booking today."""
    due_by = balance_due_date(booking)
    if due_by is None or balance_due(booking) <= 0:
        return None
    to_due = (due_by - today).days
    if to_due == UPCOMING_DAYS_BEFORE_DUE:
        return 'upcoming'
    if to_due <= 0 and booking.final_notice_sent_on is None:
        return 'final'
    return None


def owing(today):
    return (
        Booking.objects.select_related('customer')
        .prefetch_related('travelers')
        .filter(start_date__gte=today, amount_paid__gt=0, amount_paid__lt=F('total_amount'), payment_status__in=OWING_STATUSES)
    )


def _notify_customer(booking, kind, url, today):
    """Email + WhatsApp. Returns True if at least one channel accepted it."""
    from .manage_links import send_manage_link

    due = balance_due(booking)
    move_on = hold_date(booking) or (today + timedelta(days=HOLD_GRACE_DAYS))
    context = {
        'booking': booking, 'kind': kind, 'balance': due, 'due_by': balance_due_date(booking), 'move_on': move_on,
        'manage_url': url, 'contact': CONTACT, 'departure': booking.departure_display,
        'first_name': (booking.customer.get_full_name() if booking.customer_id else '').split(' ')[0],
        'missing_ids': [t.name for t in booking.travelers.all() if needs_id(t)],
        'held_from_date': booking.held_from_date, 'min_days_ahead': INSTALMENT_MIN_DAYS_AHEAD,
        'due_days_before': BALANCE_DUE_DAYS_BEFORE,
    }
    trip = booking.held_from_date or booking.start_date
    subject = {
        'upcoming': f"Balance of ${due:.2f} due soon — {booking.tour_name}, {trip:%d %b}",
        'final': f"Action needed: pay ${due:.2f} by {move_on:%d %b} to keep your {trip:%d %b} cruise",
        'moved': f"Your {trip:%d %b} cruise is on hold — choose a new date",
    }[kind]
    reached = False
    try:
        from notifications.emailing import send_branded_email
        reached = bool(send_branded_email(
            template='balance_reminder', to=customer_email(booking), booking=booking, subject=subject,
            key=f'balance-{kind}:{booking.pk}:{today.isoformat()}',
            preheader={
                'upcoming': f"${due:.2f} left to pay — all at once or in instalments.",
                'final': 'Pay the balance to keep your seats. Your payment is never lost.',
                'moved': 'Your payment is kept as credit. Choose a new date in a couple of taps.',
            }[kind],
            context={**context, 'kind_is_moved': kind == 'moved'},
        ))
    except Exception:
        logger.exception("Balance %s email failed for %s", kind, booking.booking_reference)
    try:
        text = {
            'upcoming': f"⏰ Your balance of *${due:.2f}* for {booking.tour_name} on {trip:%d %b} is due by {context['due_by']:%d %b}.",
            'final': (f"⚠️ Your balance of *${due:.2f}* for {booking.tour_name} on {trip:%d %b} is now due. "
                      f"If it isn't paid by *{move_on:%d %b}*, your booking will be moved off this cruise and your "
                      f"payment kept as credit for a new date."),
            'moved': (f"📅 Your balance wasn't paid in time, so your {booking.tour_name} booking for {trip:%d %b} is *on hold* "
                      f"and those seats were released. The ${booking.amount_paid:.2f} you paid is kept as credit: "
                      f"choose a new date (more than {INSTALMENT_MIN_DAYS_AHEAD} days away) on your booking page."),
        }[kind]
        sent, _ = send_manage_link(booking, url, intro=text)
        reached = reached or sent
    except Exception:
        logger.exception("Balance %s WhatsApp failed for %s", kind, booking.booking_reference)
    return reached


def _notify_staff(template_name, booking, **extra):
    def _send():
        try:
            from notifications.services import queue_notifications_to_users
            contact = getattr(booking.customer, 'contact', None) if booking.customer_id else None
            queue_notifications_to_users(
                template_name=template_name, group_names=["System Admins", "Sales Team"], related_contact=contact,
                template_context={
                    'booking_reference': booking.booking_reference, 'tour_name': booking.tour_name,
                    'start_date': (booking.held_from_date or booking.start_date).isoformat(),
                    'amount_paid': f"{booking.amount_paid:.2f}", 'balance': f"{balance_due(booking):.2f}", **extra,
                },
            )
        except Exception:
            logger.exception("Staff alert %s failed for %s", template_name, booking.booking_reference)
    transaction.on_commit(_send)


def send_balance_reminders(today=None):
    """'upcoming' and 'final' notices. Returns the references reminded."""
    today = today or timezone.localdate()
    sent = []
    for booking in owing(today).exclude(balance_reminder_sent_on=today):
        kind = reminder_kind(booking, today)
        if kind is None:
            continue
        # Claim first, so an overlapping run can't double-send.
        if not Booking.objects.filter(pk=booking.pk).exclude(balance_reminder_sent_on=today).update(balance_reminder_sent_on=today):
            continue
        if kind == 'final':
            booking.final_notice_sent_on = today  # the template quotes hold_date()
        if _notify_customer(booking, kind, manage_url(booking), today):
            sent.append(booking.booking_reference)
            if kind == 'final':
                Booking.objects.filter(pk=booking.pk).update(final_notice_sent_on=today)
        else:
            # Nothing reached the customer: try again tomorrow; never move a booking unwarned.
            Booking.objects.filter(pk=booking.pk, balance_reminder_sent_on=today).update(balance_reminder_sent_on=None)
            logger.warning("Balance %s notice for %s reached no channel", kind, booking.booking_reference)
    logger.info("Balance reminders sent: %s", sent)
    return sent


def move_unpaid_to_hold(today=None):
    """Bookings still owing HOLD_GRACE_DAYS after their final notice go ON_HOLD. Returns references moved."""
    today = today or timezone.localdate()
    moved = []
    due_ids = owing(today).filter(final_notice_sent_on__lte=today - timedelta(days=HOLD_GRACE_DAYS)).values_list('pk', flat=True)
    for pk in due_ids:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().select_related('customer').filter(pk=pk).first()
            # Re-check under the lock: a payment may have just landed.
            if (booking is None or booking.payment_status not in OWING_STATUSES
                    or balance_due(booking) <= 0 or booking.start_date < today):
                continue
            booking.held_from_date, booking.held_from_time = booking.start_date, booking.start_time
            booking.held_at = timezone.now()
            booking.payment_status = Booking.PaymentStatus.ON_HOLD
            booking.held_payment_status = ''
            booking.save(update_fields=['held_from_date', 'held_from_time', 'held_at', 'payment_status',
                                        'held_payment_status', 'updated_at'])
            _notify_staff('booking_moved_to_hold', booking)
        url = manage_url(booking)
        if not _notify_customer(booking, 'moved', url, today):
            logger.warning("Booking %s moved to hold but the customer couldn't be told", booking.booking_reference)
        moved.append(booking.booking_reference)
    logger.info("Unpaid bookings moved to hold: %s", moved)
    return moved


def alert_stale_holds(today=None):
    """Tell staff about bookings that have sat on hold for HOLD_CREDIT_DAYS (once, on that day)."""
    today = today or timezone.localdate()
    stale = Booking.objects.select_related('customer').filter(
        payment_status=Booking.PaymentStatus.ON_HOLD, held_at__date=today - timedelta(days=HOLD_CREDIT_DAYS),
    )
    refs = []
    for booking in stale:
        _notify_staff('booking_hold_expired', booking, days=HOLD_CREDIT_DAYS)
        refs.append(booking.booking_reference)
    return refs


def run_daily(today=None):
    """Order matters: move bookings whose grace ran out before sending today's notices."""
    return {
        'moved': move_unpaid_to_hold(today),
        'reminded': send_balance_reminders(today),
        'stale_holds': alert_stale_holds(today),
    }
