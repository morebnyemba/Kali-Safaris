"""
Secure "manage my booking" links.

One link per booking lets the customer, without an account:
- upload missing ID/passport photos (and ID numbers) for travellers aged 12+;
- pay the outstanding balance in instalments with any website payment method.

Token = Django-signed [booking id, booking.access_key] (SECRET_KEY + salt), so it
can't be guessed or forged, carries no personal data, and every link ever sent
is revoked at once by rotating `access_key`. Links also stop working after
LINK_MAX_AGE, and uploads/payments stop once the trip is over.

Booking references can't be used for this: after payment, all bookings on one
departure share a reference (it's the manifest key).
"""
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core import signing
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from .models import Booking
from .traveler_validation import ID_REQUIRED_FROM_AGE

SALT = 'customer_data.manage-booking'
LINK_MAX_AGE = timedelta(days=180)
MIN_INSTALMENT = Decimal('10.00')
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
CLOSED_STATUSES = (Booking.PaymentStatus.CANCELLED, Booking.PaymentStatus.REFUNDED)

# Magic bytes -> (mime, extension). Never trust the browser's declared type.
_SIGNATURES = (
    (b'\xff\xd8\xff', 'image/jpeg', '.jpg'),
    (b'\x89PNG\r\n\x1a\n', 'image/png', '.png'),
    (b'%PDF-', 'application/pdf', '.pdf'),
)


class ManageLinkError(Exception):
    """Shown to the customer as-is."""


def _ensure_key(booking):
    if not booking.access_key:
        booking.access_key = secrets.token_urlsafe(16)
        Booking.objects.filter(pk=booking.pk, access_key='').update(access_key=booking.access_key)
        booking.refresh_from_db(fields=['access_key'])
    return booking.access_key


def issue_token(booking):
    return signing.dumps([booking.pk, _ensure_key(booking)], salt=SALT)


def manage_url(booking):
    return f"{settings.PUBLIC_SITE_URL}/manage/{issue_token(booking)}"


def revoke_links(booking):
    """Invalidate every link sent so far; the next manage_url() is a new one."""
    booking.access_key = secrets.token_urlsafe(16)
    Booking.objects.filter(pk=booking.pk).update(access_key=booking.access_key)


def resolve_token(token, lock=False):
    """The booking for a valid, unrevoked, unexpired token; else None."""
    try:
        booking_id, key = signing.loads(str(token or ''), salt=SALT, max_age=LINK_MAX_AGE)
    except (signing.BadSignature, ValueError, TypeError):
        return None
    queryset = Booking.objects.select_related('customer', 'tour')
    if lock:
        queryset = queryset.select_for_update()
    booking = queryset.filter(pk=booking_id).first()
    if booking is None or not booking.access_key or not constant_time_compare(booking.access_key, str(key)):
        return None
    return booking


def trip_is_over(booking):
    return (booking.end_date or booking.start_date) < timezone.localdate()


def balance_due(booking):
    return max((booking.total_amount or Decimal('0')) - (booking.amount_paid or Decimal('0')), Decimal('0')).quantize(Decimal('0.01'))


def can_pay(booking):
    return booking.payment_status not in CLOSED_STATUSES and not trip_is_over(booking) and balance_due(booking) > 0


def minimum_payment(booking):
    """Smallest instalment accepted: MIN_INSTALMENT, or the whole balance if less."""
    return min(MIN_INSTALMENT, balance_due(booking))


def validate_instalment(booking, amount):
    """Raises ManageLinkError unless `amount` is a payable instalment for this booking."""
    if booking.payment_status in CLOSED_STATUSES:
        raise ManageLinkError("This booking is closed, so it can't take payments. Please contact us on WhatsApp.")
    if trip_is_over(booking):
        raise ManageLinkError("This trip has already taken place, so payments are closed.")
    due = balance_due(booking)
    if due <= 0:
        raise ManageLinkError("This booking has already been paid in full.")
    if amount > due + Decimal('0.01'):
        raise ManageLinkError(f"The most you can pay now is the balance of ${due}.")
    from .payment_plan import minimum_charge

    minimum = minimum_charge(booking)
    if amount < minimum - Decimal('0.01'):
        if (booking.amount_paid or 0) > 0:
            raise ManageLinkError(f"The smallest instalment is ${minimum}.")
        raise ManageLinkError(f"The first payment for this booking must be at least ${minimum}.")


def needs_id(traveler):
    return traveler.age >= ID_REQUIRED_FROM_AGE and (not traveler.id_document or not traveler.id_number)


def summary(booking):
    """What the customer's page shows. No ID numbers or document URLs ever leave here."""
    from .payment_plan import balance_due_date, minimum_charge

    travelers = list(booking.travelers.all().order_by('traveler_type', 'name'))
    over = trip_is_over(booking)
    due_by = balance_due_date(booking)
    return {
        'booking_reference': booking.booking_reference,
        'tour_name': booking.tour_name,
        'start_date': booking.start_date.isoformat(),
        'departure': booking.departure_display,
        'customer_name': booking.customer.get_full_name() if booking.customer_id else '',
        'payment_status': booking.payment_status,
        'payment_status_display': booking.get_payment_status_display(),
        'total_amount': f"{booking.total_amount:.2f}",
        'amount_paid': f"{booking.amount_paid:.2f}",
        'balance_due': f"{balance_due(booking):.2f}",
        'minimum_payment': f"{minimum_charge(booking):.2f}",
        'balance_due_by': due_by.isoformat() if due_by else None,
        'balance_overdue': bool(due_by and balance_due(booking) > 0 and due_by < timezone.localdate()),
        'can_pay': can_pay(booking),
        'can_upload': not over and booking.payment_status not in CLOSED_STATUSES,
        'trip_is_over': over,
        'passengers_booked': (booking.number_of_adults or 0) + (booking.number_of_children or 0),
        'id_required_from_age': ID_REQUIRED_FROM_AGE,
        'travelers': [
            {
                'id': str(t.id),
                'name': t.name,
                'age': t.age,
                'id_required': t.age >= ID_REQUIRED_FROM_AGE,
                'has_document': bool(t.id_document),
                'has_id_number': bool(t.id_number),
                'needs_id': needs_id(t),
            }
            for t in travelers
        ],
        'payments': [
            {
                'date': p.created_at.isoformat(),
                'amount': f"{p.amount:.2f}",
                'currency': p.currency,
                'method': p.get_payment_method_display(),
                'status': p.status,
                'status_display': p.get_status_display(),
            }
            for p in booking.payments.all().order_by('-created_at')
        ],
    }


def sniff_document(head):
    for magic, mime, ext in _SIGNATURES:
        if head.startswith(magic):
            return mime, ext
    return None, None


def attach_id(booking, traveler_id, upload=None, id_number=''):
    """
    Adds a missing ID photo and/or ID number. Never replaces what's on file:
    a leaked link can't swap a passport; corrections go through staff.
    """
    from django.core.files.base import ContentFile
    from .traveler_validation import _text

    if trip_is_over(booking) or booking.payment_status in CLOSED_STATUSES:
        raise ManageLinkError("This booking can no longer be changed online. Please contact us on WhatsApp.")
    traveler = booking.travelers.filter(pk=traveler_id).first()
    if traveler is None:
        raise ManageLinkError("Traveller not found on this booking.")

    id_number = _text(id_number)[:50]
    changed = []
    if upload is not None:
        if traveler.id_document:
            raise ManageLinkError(f"We already have an ID document for {traveler.name}. To replace it, contact us on WhatsApp.")
        if upload.size > MAX_DOCUMENT_BYTES:
            raise ManageLinkError("That file is too large (8 MB max). Please take a smaller photo.")
        raw = upload.read()
        mime, ext = sniff_document(raw[:16])
        if not mime:
            raise ManageLinkError("Please upload a JPG or PNG photo, or a PDF.")
        traveler.id_document.save(f"traveler-{traveler.pk}{ext}", ContentFile(raw), save=False)
        changed.append('id_document')
    if id_number:
        if traveler.id_number:
            raise ManageLinkError(f"We already have an ID number for {traveler.name}. To change it, contact us on WhatsApp.")
        traveler.id_number = id_number
        changed.append('id_number')
    if not changed:
        raise ManageLinkError("Choose a photo or enter an ID number.")
    traveler.save(update_fields=[*changed, 'updated_at'])  # signal re-checks the booking's passenger rule
    return traveler


def link_message(booking, url):
    """WhatsApp/email text inviting the customer to finish what's missing."""
    travelers = list(booking.travelers.all())
    missing_ids = [t.name for t in travelers if needs_id(t)]
    due = balance_due(booking)
    lines = [f"🔐 *Manage your booking {booking.booking_reference}*", f"{booking.tour_name} · {booking.start_date.strftime('%d %b %Y')}", ""]
    if missing_ids:
        lines.append(f"🪪 ID/passport still needed for: {', '.join(missing_ids)}")
    if due > 0 and can_pay(booking):
        from .payment_plan import balance_due_date, minimum_charge
        due_by = balance_due_date(booking)
        lines.append(f"💳 Balance due: *${due:.2f}*{' by ' + due_by.strftime('%d %b') if due_by else ''} — pay all of it or in instalments (from ${minimum_charge(booking):.2f}).")
    if not missing_ids and due <= 0:
        lines.append("✅ Your booking is fully paid and all IDs are in. You can view it any time here.")
    lines += ["", url, "", "This link is private to your booking — please don't share it."]
    return "\n".join(lines)


def send_manage_link(booking, url=None):
    """Sends the link on WhatsApp. Returns (sent, error_message)."""
    from meta_integration.utils import send_whatsapp_message

    contact = getattr(booking.customer, 'contact', None) if booking.customer_id else None
    if not contact or not contact.whatsapp_id:
        return False, "This booking's customer has no WhatsApp number."
    result = send_whatsapp_message(
        contact.whatsapp_id, 'text', {'body': link_message(booking, url or manage_url(booking)), 'preview_url': False},
        contact.associated_app_config,
    )
    if not result:
        return False, ("WhatsApp didn't accept the message. If the customer hasn't messaged in the last 24 hours, "
                       "copy the link and send it another way.")
    return True, ''
