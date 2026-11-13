"""
Staff alerts: what the team needs to know, with enough detail to act on it.

Two channels:
- Email to settings.STAFF_ALERT_EMAILS — the reliable one (branded, logged in
  EmailLog, deduped per event so a re-saved row never alerts twice).
- WhatsApp to settings.STAFF_ALERT_GROUPS via the notification templates in
  flows/management/commands/load_notification_templates.py — delivered only
  for staff users with a linked WhatsApp contact, once the templates are
  approved by Meta (sync_meta_templates).

Payment alerts carry everything the gateway gave us (merchant / bank /
authorisation references, masked card, EcoCash/Omari number, result codes and
the stored gateway response, card data redacted) so finance can match each
payment to the bank or gateway statement.
"""
import json
import logging
import re

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Unmasked card numbers never leave the system, even if a gateway echoed one.
_PAN_RE = re.compile(r'\b\d{13,19}\b')


def _money(value, currency='USD'):
    try:
        return f"{currency} {float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value or '—')


def _when(value):
    if not value:
        return '—'
    if hasattr(value, 'tzinfo') and value.tzinfo is not None:
        value = timezone.localtime(value)
    return value.strftime('%d %b %Y, %H:%M') if hasattr(value, 'hour') else value.strftime('%d %b %Y')


def dashboard_link(path=''):
    return f"{getattr(settings, 'DASHBOARD_URL', '').rstrip('/')}{path}"


# --- Facts ---

def booking_facts(booking):
    from customer_data.booking_emails import customer_email
    from customer_data.manage_links import balance_due

    customer = booking.customer if booking.customer_id else None
    contact = getattr(customer, 'contact', None) if customer else None
    guests = f"{booking.number_of_adults or 0} adult(s)" + (
        f", {booking.number_of_children} child(ren)" if booking.number_of_children else '')
    return [
        ('Booking reference', booking.booking_reference),
        ('Customer', (customer.get_full_name() if customer else '') or '—'),
        ('WhatsApp / phone', getattr(contact, 'whatsapp_id', '') or '—'),
        ('Email', customer_email(booking) or '—'),
        ('Cruise', booking.tour_name),
        ('Date', booking.start_date.strftime('%a %d %b %Y') if booking.start_date else '—'),
        ('Departure', booking.departure_display or '—'),
        ('Guests', guests),
        ('Total', _money(booking.total_amount)),
        ('Paid to date', _money(booking.amount_paid)),
        ('Balance', _money(balance_due(booking))),
        ('Status', booking.get_payment_status_display()),
        ('Source', booking.get_source_display()),
    ]


def payment_facts(payment):
    return [
        ('Amount', _money(payment.amount, payment.currency)),
        ('Method', payment.get_payment_method_display()),
        ('Status', payment.get_status_display()),
        ('Payment reference', payment.transaction_reference or '—'),
        ('Payment ID', str(payment.pk)),
        ('Recorded', _when(payment.created_at)),
        ('Notes', payment.notes or '—'),
    ]


def _safe_dump(data):
    """Gateway response for the email: card fields redacted, internal keys dropped, size capped."""
    if not data:
        return ''
    try:
        from cbz_integration.views import _scrub_pci_fields
        data = _scrub_pci_fields(data)
    except Exception:
        pass

    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items() if not str(k).startswith('_')}
        if isinstance(obj, list):
            return [_clean(v) for v in obj]
        return obj

    text = json.dumps(_clean(data), indent=2, sort_keys=True, default=str)
    text = _PAN_RE.sub('[REDACTED]', text)
    return text[:4000] + ('\n…(truncated)' if len(text) > 4000 else '')


def gateway_facts(payment):
    """(title, rows, raw) for the gateway transaction behind a payment, or None."""
    ref = (payment.transaction_reference or '').strip()
    if not ref:
        return None
    try:
        from cbz_integration.models import CBZTransaction
        txn = CBZTransaction.objects.filter(merchant_reference=ref).first()
    except Exception:
        txn = None
    if txn is not None:
        card = ' '.join(x for x in (txn.masked_pan, f"(BIN {txn.card_bin})" if txn.card_bin else '') if x)
        rows = [
            ('Gateway', f"CBZ / iVeri — {txn.get_payment_type_display()}"),
            ('Merchant reference', txn.merchant_reference),
            ('iVeri transaction index', txn.transaction_index or '—'),
            ('Request ID', txn.request_id or '—'),
            ('Bank reference', txn.bank_reference or '—'),
            ('Authorisation code', txn.authorisation_code or '—'),
            ('Result', f"{txn.result_code or '—'} {txn.result_description or ''}".strip()),
            ('Card', card or '—'),
            ('EcoCash number', txn.msisdn or '—'),
            ('Consumer order ID', txn.consumer_order_id or '—'),
            ('Command', txn.command or '—'),
            ('Gateway status', txn.get_status_display()),
            ('Amount (gateway)', _money(txn.amount, txn.currency)),
            ('Started', _when(txn.created_at)),
            ('Completed', _when(txn.completed_at)),
        ]
        return 'Gateway transaction (CBZ / iVeri)', rows, _safe_dump(txn.gateway_response)
    try:
        from django.db.models import Q
        from omari_integration.models import OmariTransaction
        txn = OmariTransaction.objects.filter(Q(payment_reference=ref) | Q(reference=ref)).first()
    except Exception:
        txn = None
    if txn is not None:
        rows = [
            ('Gateway', 'Omari'),
            ('Merchant reference', txn.reference),
            ('Omari payment reference', txn.payment_reference or '—'),
            ('Debit reference', txn.debit_reference or '—'),
            ('OTP reference', txn.otp_reference or '—'),
            ('Omari number', txn.msisdn or '—'),
            ('Channel', txn.channel or '—'),
            ('Response', f"{txn.response_code or '—'} {txn.response_message or ''}".strip()),
            ('Gateway status', txn.get_status_display()),
            ('Amount (gateway)', _money(txn.amount, txn.currency)),
            ('Started', _when(txn.created_at)),
            ('Completed', _when(txn.completed_at)),
        ]
        return 'Gateway transaction (Omari)', rows, ''
    return None


# --- Sending ---

def alert_staff(*, key, subject, headline, intro='', sections=(), raw=None, link=None,
                whatsapp_template=None, whatsapp_context=None, tone='info'):
    """
    Emails every address in STAFF_ALERT_EMAILS (once per key) and queues the
    WhatsApp template for STAFF_ALERT_GROUPS. Never raises for one channel
    failing; email failures re-raise after the loop so a Celery task retries.
    """
    from .emailing import send_branded_email

    errors = []
    for address in getattr(settings, 'STAFF_ALERT_EMAILS', []):
        try:
            send_branded_email(
                template='staff_alert', to=address, key=f"{key}:{address}",
                subject=f"[Kalai] {subject}", preheader=intro[:120],
                context={'headline': headline, 'intro': intro, 'sections': sections, 'raw': raw,
                         'link': link, 'tone': tone},
            )
        except Exception as exc:  # SMTP down: retried by the task
            errors.append(exc)
    if whatsapp_template:
        try:
            from .services import queue_notifications_to_users
            queue_notifications_to_users(
                template_name=whatsapp_template, template_context=whatsapp_context or {},
                group_names=getattr(settings, 'STAFF_ALERT_GROUPS', []),
            )
        except Exception:
            logger.exception("Staff WhatsApp alert %s failed", whatsapp_template)
    if errors:
        raise errors[0]


def payment_received(payment):
    booking = payment.booking
    gateway = gateway_facts(payment)
    sections = [('Payment', payment_facts(payment))]
    if gateway:
        sections.append((gateway[0], gateway[1]))
    if booking is not None:
        sections.append(('Booking', booking_facts(booking)))
    ref = booking.booking_reference if booking else 'no booking'
    alert_staff(
        key=f"staff-payment:{payment.pk}",
        subject=f"Payment received {_money(payment.amount, payment.currency)} · {ref}",
        headline=f"{_money(payment.amount, payment.currency)} received",
        intro=(f"{payment.get_payment_method_display()} payment for {booking.tour_name} on "
               f"{booking.start_date:%d %b %Y} ({ref})." if booking else "Payment not linked to a booking."),
        sections=sections, raw=gateway[2] if gateway else '', tone='success',
        link=dashboard_link(f"/payments?q={payment.transaction_reference or ref}"),
        whatsapp_template='staff_payment_received',
        whatsapp_context={
            'amount': _money(payment.amount, payment.currency), 'method': payment.get_payment_method_display(),
            'payment_reference': payment.transaction_reference or '—', 'booking_reference': ref,
            'customer': dict(booking_facts(booking)).get('Customer', '—') if booking else '—',
            'tour_name': booking.tour_name if booking else '—',
            'start_date': booking.start_date.isoformat() if booking and booking.start_date else '—',
            'balance': dict(booking_facts(booking)).get('Balance', '—') if booking else '—',
        },
    )


def payment_pending(payment):
    booking = payment.booking
    ref = booking.booking_reference if booking else 'no booking'
    alert_staff(
        key=f"staff-payment-pending:{payment.pk}",
        subject=f"Verify payment {_money(payment.amount, payment.currency)} · {ref}",
        headline='Payment waiting for verification',
        intro=(f"A customer reported a {payment.get_payment_method_display().lower()} of "
               f"{_money(payment.amount, payment.currency)}. Check it reached the account, then approve or reject it."),
        sections=[('Payment', payment_facts(payment))] + ([('Booking', booking_facts(booking))] if booking else []),
        link=dashboard_link('/payments?status=pending'), tone='warning',
        whatsapp_template='manual_payment_recorded_alert',
        whatsapp_context={'amount': _money(payment.amount, payment.currency), 'booking_reference': ref,
                          'method': payment.get_payment_method_display()},
    )


BOOKING_EVENTS = {
    # event: (subject, headline, intro, tone)
    'new_booking': ('New booking', 'New booking', 'A booking was created and is waiting for payment.', 'info'),
    'confirmed': ('Booking confirmed', 'Booking confirmed', 'Payment received — this booking is confirmed and on the manifest.', 'success'),
    'fully_paid': ('Booking fully paid', 'Booking fully paid', 'The balance has been paid in full.', 'success'),
    'awaiting_details': ('Paid — passenger details missing', 'Paid, but not on the manifest yet',
                         "Money was received but some passenger details are missing, so the booking is held off the manifest. "
                         "Collect the details; it confirms automatically once complete.", 'warning'),
    'on_hold': ('Booking moved to hold', 'Booking moved off its cruise',
                'The balance was not paid after the final notice. Seats were released and the payment is kept as credit.', 'warning'),
    'hold_expired': ('Booking on hold for a long time', 'Still no new date',
                     'This booking has been on hold without a new date. Please follow up with the customer.', 'warning'),
    'rescheduled': ('Booking date changed', 'Booking moved to a new date', 'The cruise date or departure of this booking changed.', 'info'),
    'cancelled': ('Booking cancelled', 'Booking cancelled', 'This booking was cancelled.', 'danger'),
    'refunded': ('Booking refunded', 'Booking refunded', 'This booking was marked as refunded.', 'danger'),
}


def booking_event(booking, event, *, extra_rows=(), key_suffix=''):
    subject, headline, intro, tone = BOOKING_EVENTS[event]
    sections = [('Booking', booking_facts(booking))]
    if extra_rows:
        sections.insert(0, ('Details', list(extra_rows)))
    alert_staff(
        key=f"staff-booking:{event}:{booking.pk}:{key_suffix or timezone.localdate().isoformat()}",
        subject=f"{subject} · {booking.booking_reference} · {booking.tour_name}",
        headline=headline, intro=intro, sections=sections, tone=tone,
        link=dashboard_link(f"/bookings?q={booking.booking_reference}"),
        whatsapp_template='staff_booking_update',
        whatsapp_context={
            'event': subject, 'booking_reference': booking.booking_reference, 'tour_name': booking.tour_name,
            'start_date': booking.start_date.isoformat() if booking.start_date else '—',
            'customer': dict(booking_facts(booking)).get('Customer', '—'), 'status': booking.get_payment_status_display(),
            'details': '; '.join(f"{label}: {value}" for label, value in extra_rows) or intro,
        },
    )
