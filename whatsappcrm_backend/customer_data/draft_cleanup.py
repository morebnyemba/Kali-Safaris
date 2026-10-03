# whatsappcrm_backend/customer_data/draft_cleanup.py
"""
Cancels website checkout drafts that were never paid.

Every website payment attempt creates a draft Booking (with its passengers)
before the gateway is contacted, so abandoned or failed checkouts leave unpaid
drafts behind. They are cancelled — never deleted — so staff keep the history.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from .models import Booking, Payment

logger = logging.getLogger(__name__)

# Set by cbz_integration.views._resolve_or_create_booking on every website draft.
WEBSITE_DRAFT_NOTE_PREFIX = 'Website checkout draft booking'
DEFAULT_MAX_AGE_HOURS = 48


def stale_website_drafts(max_age_hours: int = DEFAULT_MAX_AGE_HOURS):
    """Unpaid website drafts older than the cutoff with no payment activity in that window."""
    from cbz_integration.models import CBZTransaction
    from omari_integration.models import OmariTransaction

    cutoff = timezone.now() - timedelta(hours=max_age_hours)

    any_payment = Payment.objects.filter(booking=OuterRef('pk'))
    cbz_blocking = CBZTransaction.objects.filter(booking=OuterRef('pk')).filter(
        Q(status=CBZTransaction.TransactionStatus.APPROVED) | Q(updated_at__gte=cutoff)
    )
    omari_blocking = OmariTransaction.objects.filter(booking=OuterRef('pk')).filter(
        Q(status='SUCCESS') | Q(updated_at__gte=cutoff)
    )

    return (
        Booking.objects
        .filter(
            notes__startswith=WEBSITE_DRAFT_NOTE_PREFIX,
            payment_status=Booking.PaymentStatus.PENDING,
            amount_paid=0,
            created_at__lt=cutoff,
        )
        .exclude(Exists(any_payment))
        .exclude(Exists(cbz_blocking))
        .exclude(Exists(omari_blocking))
    )


def cancel_stale_website_drafts(max_age_hours: int = DEFAULT_MAX_AGE_HOURS, dry_run: bool = False) -> list[str]:
    """Cancel stale drafts; returns the affected booking references."""
    cancelled = []
    stamp = timezone.localtime().strftime('%Y-%m-%d %H:%M')
    for booking in stale_website_drafts(max_age_hours).iterator():
        cancelled.append(booking.booking_reference or str(booking.pk))
        if dry_run:
            continue
        with transaction.atomic():
            locked = Booking.objects.select_for_update().get(pk=booking.pk)
            # Re-check under the lock: a payment may have landed since the query.
            if locked.payment_status != Booking.PaymentStatus.PENDING or locked.amount_paid:
                cancelled.pop()
                continue
            locked.payment_status = Booking.PaymentStatus.CANCELLED
            locked.notes = (
                f"{locked.notes}\n[{stamp}] Auto-cancelled: unpaid website checkout draft "
                f"older than {max_age_hours}h."
            ).strip()
            locked.save(update_fields=['payment_status', 'notes', 'updated_at'])
    if cancelled:
        logger.info("%s %d stale website draft booking(s): %s",
                    'Would cancel' if dry_run else 'Cancelled', len(cancelled), ', '.join(cancelled))
    return cancelled
