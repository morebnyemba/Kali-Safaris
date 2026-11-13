# customer_data/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Booking, Payment, Traveler

@receiver([post_save, post_delete], sender=Payment)
def update_booking_amount_paid(sender, instance, **kwargs):
    """
    When a Payment is saved (created/updated) or deleted, find its related
    booking and trigger the recalculation of the `amount_paid` field.
    """
    # The 'instance' is the Payment object that was just saved or deleted.
    if instance.booking:
        # Calling this method will sum up all successful payments for the booking
        # and save the result.
        instance.booking.update_amount_paid(commit=True)

@receiver([post_save, post_delete], sender=Traveler)
def recheck_booking_traveler_details(sender, instance, origin=None, **kwargs):
    """
    Adding, editing or removing a traveler re-evaluates the booking's
    passenger-details invariant (Booking._enforce_traveler_details): an
    AWAITING_DETAILS booking is promoted once complete, and a confirmed booking
    that becomes incomplete is held again.
    """
    if isinstance(origin, Booking):
        return  # the booking itself is being deleted
    booking = Booking.objects.filter(pk=instance.booking_id).first()
    if booking and (
        booking.payment_status in Booking.CONFIRMED_PAYMENT_STATUSES
        or booking.payment_status == Booking.PaymentStatus.AWAITING_DETAILS
    ):
        booking.save(update_fields=['updated_at'])


@receiver(post_save, sender=Booking)
def queue_booking_confirmation_email(sender, instance, **kwargs):
    """Once a booking is confirmed (any payment path), email the customer — once."""
    from django.db import transaction
    from .booking_emails import wants_confirmation_email
    from .tasks import send_booking_confirmation_email_task

    if wants_confirmation_email(instance):
        booking_id = instance.pk
        transaction.on_commit(lambda: send_booking_confirmation_email_task.delay(booking_id))


@receiver(post_save, sender=Payment)
def queue_payment_receipt(sender, instance, **kwargs):
    """Email a receipt for each successful payment after the booking's confirmation email (instalments)."""
    if instance.status != Payment.PaymentStatus.SUCCESSFUL or not instance.booking_id:
        return
    from django.db import transaction
    from .customer_emails import receipt_wanted
    from .tasks import send_payment_receipt_email_task

    booking = Booking.objects.filter(pk=instance.booking_id).only('confirmation_email_sent_at').first()
    instance.booking = booking
    if booking is not None and receipt_wanted(instance):  # decided now: the confirmation email may follow this save
        payment_id = instance.pk
        transaction.on_commit(lambda: send_payment_receipt_email_task.delay(str(payment_id)))


# --- Staff alerts: payments and booking changes (notifications/staff_alerts.py) ---

from django.db.models.signals import pre_save

@receiver(post_save, sender=Payment)
def alert_staff_on_payment(sender, instance, created, **kwargs):
    """Every successful payment (with its gateway details), and every reported payment that needs verifying."""
    from django.db import transaction
    from notifications.tasks import staff_payment_pending_task, staff_payment_received_task

    payment_id = str(instance.pk)
    if instance.status == Payment.PaymentStatus.SUCCESSFUL:
        transaction.on_commit(lambda: staff_payment_received_task.delay(payment_id))  # deduped per payment
    elif (created and instance.status == Payment.PaymentStatus.PENDING
          and not str(instance.payment_method).startswith('paynow')):  # Paynow rows start pending, then the gateway confirms
        transaction.on_commit(lambda: staff_payment_pending_task.delay(payment_id))


@receiver(pre_save, sender=Booking)
def remember_booking_state(sender, instance, **kwargs):
    """Keep the row as it was, so post_save can tell what changed."""
    previous = None
    if instance.pk:
        previous = Booking.objects.filter(pk=instance.pk).values(
            'payment_status', 'start_date', 'start_time', 'amount_paid', 'booking_reference').first()
    instance._previous_state = previous


def _is_unpaid_draft(booking):
    return str(booking.booking_reference or '').startswith('PENDING-') and not booking.amount_paid


@receiver(post_save, sender=Booking)
def alert_staff_on_booking_change(sender, instance, created, **kwargs):
    from django.db import transaction
    from notifications.tasks import staff_booking_event_task

    S = Booking.PaymentStatus
    events = []  # (event, extra_rows, key_suffix)
    previous = getattr(instance, '_previous_state', None)
    if created or previous is None:
        if instance.source != Booking.BookingSource.EMAIL_IMPORT and not _is_unpaid_draft(instance):
            events.append(('confirmed' if instance.payment_status in Booking.CONFIRMED_PAYMENT_STATUSES else 'new_booking', [], 'once'))
    else:
        old, new = previous['payment_status'], instance.payment_status
        if old != new:
            if new == S.PAID and old == S.DEPOSIT_PAID:
                events.append(('fully_paid', [], 'once'))
            elif new in Booking.CONFIRMED_PAYMENT_STATUSES and old not in Booking.CONFIRMED_PAYMENT_STATUSES and old != S.ON_HOLD:
                events.append(('confirmed', [], 'once'))
            elif new == S.AWAITING_DETAILS:
                events.append(('awaiting_details', [('Missing', ' '.join(instance.traveler_details_problems()) or '—')], ''))
            elif new == S.ON_HOLD:
                events.append(('on_hold', [('Original date', str(instance.held_from_date or previous['start_date']))], ''))
            elif new == S.CANCELLED and not _is_unpaid_draft(instance):
                events.append(('cancelled', [('Previous status', S(old).label if old in S.values else old)], 'once'))
            elif new == S.REFUNDED:
                events.append(('refunded', [], 'once'))
        moved = (previous['start_date'], previous['start_time']) != (instance.start_date, instance.start_time)
        if moved and not _is_unpaid_draft(instance) and new not in (S.PENDING, S.CANCELLED):
            was = f"{previous['start_date']}" + (f" {previous['start_time']:%H:%M}" if previous['start_time'] else '')
            now = f"{instance.start_date}" + (f" {instance.start_time:%H:%M}" if instance.start_time else '')
            events.append(('rescheduled', [('From', was), ('To', now)], f"{instance.start_date}-{instance.start_time}"))

    booking_id = instance.pk
    for event, rows, suffix in events:
        transaction.on_commit(lambda e=event, r=rows, k=suffix: staff_booking_event_task.delay(booking_id, e, r, k))
