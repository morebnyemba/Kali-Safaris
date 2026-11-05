"""
Automatic balance reminders for bookings paid by deposit / instalments.

Daily (Celery beat). A booking with a payment but an outstanding balance gets
a reminder a week before the balance is due, on the due date, and a final one
3 days before the trip if it's still unpaid. Each reminder goes by email (when
we have an address) and WhatsApp (delivered only inside WhatsApp's 24-hour
window; otherwise Meta rejects it and email carries it). Both carry the
customer's secure link, which also lists any missing IDs.
`Booking.balance_reminder_sent_on` keeps it to one per booking per day.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone

from .booking_emails import CONTACT, customer_email
from .manage_links import balance_due, link_message, manage_url, needs_id, send_manage_link
from .models import Booking
from .payment_plan import balance_due_date

logger = logging.getLogger(__name__)

DAYS_BEFORE_DUE = (7, 0)
FINAL_NOTICE_DAYS_BEFORE_TRIP = 3


def reminder_kind(booking, today):
    """'upcoming' | 'due' | 'final' | None for this booking today."""
    due_by = balance_due_date(booking)
    if due_by is None or balance_due(booking) <= 0:
        return None
    to_due = (due_by - today).days
    if to_due == DAYS_BEFORE_DUE[0]:
        return 'upcoming'
    if to_due == DAYS_BEFORE_DUE[1]:
        return 'due'
    if (booking.start_date - today).days == FINAL_NOTICE_DAYS_BEFORE_TRIP:
        return 'final'
    return None


def candidates(today):
    return (
        Booking.objects.select_related('customer')
        .prefetch_related('travelers')
        .filter(
            start_date__gt=today,
            amount_paid__gt=0,
            amount_paid__lt=F('total_amount'),
            payment_status__in=[Booking.PaymentStatus.DEPOSIT_PAID, Booking.PaymentStatus.AWAITING_DETAILS],
        )
        .exclude(balance_reminder_sent_on=today)
    )


def _email(booking, kind, url):
    to = customer_email(booking)
    if not to:
        return False
    due = balance_due(booking)
    context = {
        'booking': booking, 'kind': kind, 'balance': due, 'due_by': balance_due_date(booking),
        'manage_url': url, 'contact': CONTACT, 'departure': booking.departure_display,
        'first_name': (booking.customer.get_full_name() if booking.customer_id else '').split(' ')[0],
        'missing_ids': [t.name for t in booking.travelers.all() if needs_id(t)],
    }
    subject = {
        'upcoming': f"Balance of ${due:.2f} due soon — {booking.tour_name}, {booking.start_date:%d %b}",
        'due': f"Your balance of ${due:.2f} is due today — {booking.booking_reference}",
        'final': f"Final reminder: ${due:.2f} to pay before your cruise on {booking.start_date:%d %b}",
    }[kind]
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string('customer_data/emails/balance_reminder.txt', context),
        from_email=settings.DEFAULT_FROM_EMAIL, to=[to], reply_to=[CONTACT['email']],
    )
    message.attach_alternative(render_to_string('customer_data/emails/balance_reminder.html', context), 'text/html')
    message.send()
    return True


def send_balance_reminders(today=None):
    """Returns the references reminded. One failing booking never stops the rest."""
    today = today or timezone.localdate()
    sent = []
    for booking in candidates(today):
        kind = reminder_kind(booking, today)
        if kind is None:
            continue
        # Claim first, so an overlapping run can't double-send.
        claimed = Booking.objects.filter(pk=booking.pk).exclude(balance_reminder_sent_on=today).update(balance_reminder_sent_on=today)
        if not claimed:
            continue
        url = manage_url(booking)
        emailed = whatsapped = False
        try:
            emailed = _email(booking, kind, url)
        except Exception:
            logger.exception("Balance reminder email failed for %s", booking.booking_reference)
        try:
            whatsapped, _ = send_manage_link(booking, url)
        except Exception:
            logger.exception("Balance reminder WhatsApp failed for %s", booking.booking_reference)
        if emailed or whatsapped:
            sent.append(booking.booking_reference)
        else:
            # Nothing reached the customer: let tomorrow's run (or staff) try again.
            Booking.objects.filter(pk=booking.pk, balance_reminder_sent_on=today).update(balance_reminder_sent_on=None)
            logger.warning("Balance reminder for %s reached no channel", booking.booking_reference)
    logger.info("Balance reminders sent: %s", sent)
    return sent
