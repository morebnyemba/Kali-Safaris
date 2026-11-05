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
