# customer_data/signals.py
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    pass