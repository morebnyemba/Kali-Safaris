# customer_data/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Payment

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