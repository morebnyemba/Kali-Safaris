"""
Branded customer email: one way to send every email the system writes.

    send_branded_email(
        template='payment_receipt',                # templates/emails/<template>.html + .txt
        to='ann@example.com', subject='…',
        context={...}, key='payment-receipt:<id>', booking=booking,
    )

- Every HTML email extends templates/emails/base.html (logo, brand colours,
  contact footer); BRAND below is available to all templates as `brand`.
- `key` makes a send idempotent: once a send with that key succeeded, later
  calls are skipped (an earlier *failed* attempt is retried). Every attempt is
  recorded in EmailLog, so staff can see what a customer was sent.
- Headers: Reply-To goes to the reservations inbox; `Auto-Submitted` marks the
  mail as machine-generated (RFC 3834) and `X-Auto-Response-Suppress` asks
  Outlook/Exchange not to answer it with out-of-office replies — together they
  stop autoresponder loops between us and customers' mail servers.
"""
import logging
from email.utils import parseaddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailLog

logger = logging.getLogger(__name__)


def brand():
    site = getattr(settings, 'PUBLIC_SITE_URL', 'https://kalaisafaris.com').rstrip('/')
    return {
        'name': 'Kalai Safaris',
        'tagline': 'Zambezi River cruises · Victoria Falls',
        'site_url': site,
        'logo_url': f"{site}/images/kalailogo.png",
        'red': '#C8102E',
        'orange': '#E8600A',
        'gold': '#E09A18',
        'cream': '#FFF9F5',
        'ink': '#1A1A1A',
        'muted': '#6B7280',
        'phone': '+263 712 629 336',
        'phone_href': 'tel:+263712629336',
        'whatsapp': 'https://wa.me/263712629336',
        'email': 'reservation@kalaisafaris.com',
        'address': 'Riverside jetty next to Palm Lodge, Victoria Falls, Zimbabwe',
        'maps': 'https://maps.google.com/?q=Kalai+Safaris+Victoria+Falls',
        'facebook': 'https://www.facebook.com/KalaiSafari',
        'year': timezone.localdate().year,
    }


def _claim(key, template, to, subject, booking):
    """Returns the EmailLog to send under, or None when this key was already sent / is being sent."""
    fields = {'template': template, 'to_email': to, 'subject': subject[:255], 'booking': booking}
    if not key:
        return EmailLog.objects.create(**fields)
    try:
        with transaction.atomic():
            return EmailLog.objects.create(key=key, **fields)
    except IntegrityError:
        # Retry only a previous failure; take it over atomically.
        claimed = EmailLog.objects.filter(key=key, status=EmailLog.Status.FAILED).update(
            status=EmailLog.Status.SENDING, error='', **fields)
        return EmailLog.objects.get(key=key) if claimed else None


def send_branded_email(*, template, to, subject, context=None, key=None, booking=None,
                       auto_reply=False, preheader='', reply_to=None):
    """
    Renders emails/<template>.html (extends base.html) and .txt and sends them.
    Returns the EmailLog, or None if skipped (already sent, or no address).
    Raises on SMTP errors (after logging) so Celery tasks can retry.
    """
    _, address = parseaddr(str(to or ''))
    if not address or '@' not in address:
        logger.info("Email %s skipped: no valid address (%r)", template, to)
        return None
    log = _claim(key, template, address, subject, booking)
    if log is None:
        logger.info("Email %s skipped: %s already sent", template, key)
        return None

    b = brand()
    ctx = {**(context or {}), 'brand': b, 'subject': subject, 'preheader': preheader}
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f'emails/{template}.txt', ctx),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[address],
        reply_to=reply_to or [b['email']],
        headers={
            'Auto-Submitted': 'auto-replied' if auto_reply else 'auto-generated',
            'X-Auto-Response-Suppress': 'All',
        },
    )
    message.attach_alternative(render_to_string(f'emails/{template}.html', ctx), 'text/html')
    try:
        message.send()
    except Exception as exc:
        EmailLog.objects.filter(pk=log.pk).update(status=EmailLog.Status.FAILED, error=str(exc)[:2000])
        logger.exception("Email %s to %s failed", template, address)
        raise
    EmailLog.objects.filter(pk=log.pk).update(status=EmailLog.Status.SENT, sent_at=timezone.now())
    logger.info("Email %s sent to %s (%s)", template, address, key or 'no key')
    log.status = EmailLog.Status.SENT
    return log


# --- Inbound mail: don't answer machines (RFC 3834 §2) ---

_AUTOMATED_LOCALPARTS = ('mailer-daemon', 'postmaster', 'noreply', 'no-reply', 'donotreply', 'do-not-reply',
                         'bounce', 'bounces', 'notifications', 'notification', 'auto-reply', 'autoreply')


def is_automated_message(msg) -> bool:
    """True for bounces, mailing lists, autoresponders and no-reply senders: never auto-reply to these."""
    auto_submitted = (msg.get('Auto-Submitted') or 'no').strip().lower()
    if auto_submitted != 'no':
        return True
    if (msg.get('Precedence') or '').strip().lower() in ('bulk', 'list', 'junk', 'auto_reply'):
        return True
    for header in ('List-Id', 'List-Unsubscribe', 'X-Autoreply', 'X-Autorespond', 'X-Auto-Response-Suppress'):
        if msg.get(header):
            return True
    if (msg.get('Return-Path') or '').strip() in ('<>', ''):
        # Bounces have an empty envelope sender; a missing header (some fetchers drop it) is fine.
        if msg.get('Return-Path') is not None:
            return True
    _, address = parseaddr(msg.get('From') or '')
    local = address.split('@')[0].lower()
    return not address or any(local == p or local.startswith(p + '+') or local.startswith(p) for p in _AUTOMATED_LOCALPARTS)
