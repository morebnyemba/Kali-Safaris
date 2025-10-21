from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class DailyStat(models.Model):
    """
    Stores aggregated daily statistics for quick dashboard retrieval.
    This model can be updated by Celery tasks triggered by signals.
    """
    date = models.DateField(_("Date"), primary_key=True, default=timezone.now)
    
    # Message Stats
    messages_sent = models.PositiveIntegerField(_("Messages Sent"), default=0)
    messages_received = models.PositiveIntegerField(_("Messages Received"), default=0)
    
    # Contact Stats
    new_contacts = models.PositiveIntegerField(_("New Contacts"), default=0)
    
    # Order Stats
    new_orders_count = models.PositiveIntegerField(_("New Orders Count"), default=0)
    won_orders_count = models.PositiveIntegerField(_("Won Orders Count"), default=0)
    revenue = models.DecimalField(_("Revenue from Won Orders"), max_digits=14, decimal_places=2, default=0.00)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = _("Daily Stat")
        verbose_name_plural = _("Daily Stats")
        ordering = ['-date']
