"""
Booking confirmation email to the customer.

Sent once, when a booking first reaches a confirmed payment status (paid or
deposit paid) — whichever payment path got it there: website card, ZimSwitch,
EcoCash, Omari, or a staff approval. `Booking.confirmation_email_sent_at`
makes it idempotent; the admin action "Resend confirmation email" clears it.

Uses Django's configured SMTP settings (EMAIL_HOST etc.). If mail isn't set up
yet the send fails, the booking stays unmarked and the task retries.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Booking

logger = logging.getLogger(__name__)

CONTACT = {
    'phone': '+263 712 629 336',
    'whatsapp': 'https://wa.me/263712629336',
    'email': 'reservation@kalaisafaris.com',
    'address': 'Riverside jetty next to Palm Lodge, Victoria Falls, Zimbabwe',
    'maps': 'https://maps.google.com/?q=Kalai+Safaris+Victoria+Falls',
}


def customer_email(booking: Booking) -> str:
    """The address the customer gave: their profile, else the website checkout form."""
    if booking.customer_id and booking.customer and booking.customer.email:
        return booking.customer.email.strip()
    payload = booking.booking_details_payload if isinstance(booking.booking_details_payload, dict) else {}
    customer = payload.get('customer') if isinstance(payload.get('customer'), dict) else {}
    return str(customer.get('email') or '').strip()


def wants_confirmation_email(booking: Booking) -> bool:
    """Confirmed, not yet emailed, has an address, and the trip hasn't happened yet."""
    return (
        booking.payment_status in Booking.CONFIRMED_PAYMENT_STATUSES
        and booking.confirmation_email_sent_at is None
        and booking.start_date is not None
        and booking.start_date >= timezone.localdate()
        # Temporary checkout references are replaced before payment; wait for the real one.
        and not str(booking.booking_reference or '').startswith('PENDING-')
        and bool(customer_email(booking))
    )


def _context(booking: Booking) -> dict:
    from .manage_links import manage_url, needs_id

    customer = booking.customer
    name = (customer.get_full_name() if customer else '') or ''
    balance = max(booking.total_amount - booking.amount_paid, 0)
    return {
        'booking': booking,
        'first_name': name.split(' ')[0] if name else '',
        'travelers': list(booking.travelers.order_by('traveler_type', 'name')),
        'departure': booking.departure_display,
        'balance': balance,
        'contact': CONTACT,
        # Secure self-service page: pay the balance in instalments, upload missing IDs.
        'manage_url': manage_url(booking),
        'missing_ids': [t.name for t in booking.travelers.all() if needs_id(t)],
    }


def send_booking_confirmation(booking_id: int) -> bool:
    """
    Sends the email if the booking still wants one. Returns True when sent.

    The booking is claimed (stamped) in a short locked transaction first, so two
    triggers can't both send it, and the lock isn't held while talking to the
    mail server. If sending fails the stamp is removed so a retry can send.
    """
    claimed_at = timezone.now()
    with transaction.atomic():
        booking = Booking.objects.select_for_update().select_related('customer').filter(pk=booking_id).first()
        if booking is None or not wants_confirmation_email(booking):
            return False
        Booking.objects.filter(pk=booking.pk).update(confirmation_email_sent_at=claimed_at)

    to = customer_email(booking)
    context = _context(booking)
    message = EmailMultiAlternatives(
        subject=f"Booking confirmed: {booking.tour_name} on {booking.start_date:%d %b %Y} — {booking.booking_reference}",
        body=render_to_string('customer_data/emails/booking_confirmation.txt', context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
        reply_to=[CONTACT['email']],
    )
    message.attach_alternative(render_to_string('customer_data/emails/booking_confirmation.html', context), 'text/html')
    try:
        message.send()
    except Exception:
        Booking.objects.filter(pk=booking.pk, confirmation_email_sent_at=claimed_at).update(confirmation_email_sent_at=None)
        raise
    logger.info("Booking confirmation email sent for %s to %s", booking.booking_reference, to)
    return True
