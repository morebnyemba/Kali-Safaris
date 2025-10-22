# customer_data/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Payment

@receiver([post_save, post_delete], sender=Payment)
def update_booking_amount_paid(sender, instance, **kwargs):
    """
    When a Payment is created, updated, or deleted,
    recalculate the total amount paid on the parent Booking.
    """
    if instance.booking:
        instance.booking.update_amount_paid()