from django.db import models
from django.utils.translation import gettext_lazy as _

class Tour(models.Model):
    """
    Represents a tour package offered by the agency.
    This replaces the previous Product model.
    """
    class TourCategory(models.TextChoices):
        SAFARI = 'safari', _('Safari')
        CULTURAL = 'cultural', _('Cultural Tour')
        ADVENTURE = 'adventure', _('Adventure & Sports')
        CITY = 'city', _('City Tour')
        CUSTOM = 'custom', _('Custom Package')

    name = models.CharField(_("Tour Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=TourCategory.choices,
        default=TourCategory.SAFARI
    )
    base_price = models.DecimalField(_("Base Price"), max_digits=10, decimal_places=2, help_text=_("Base price per adult."))
    duration_days = models.PositiveIntegerField(_("Duration in Days"), default=1)
    location = models.CharField(_("Location / Region"), max_length=255, blank=True)
    image = models.ImageField(_("Tour Image"), upload_to='tours/', blank=True, null=True, help_text=_("A representative image for the tour."))
    is_active = models.BooleanField(_("Is Active"), default=True, help_text=_("Is this tour currently available for booking?"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("Tour Package")
        verbose_name_plural = _("Tour Packages")


class SeasonalTourPrice(models.Model):
    """
    Represents seasonal pricing for tours.
    Allows different prices for different date ranges.
    """
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='seasonal_prices',
        verbose_name=_("Tour")
    )
    start_date = models.DateField(_("Start Date"), help_text=_("Start date of the pricing period"))
    end_date = models.DateField(_("End Date"), help_text=_("End date of the pricing period"))
    price_per_adult = models.DecimalField(
        _("Price Per Adult"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Price per adult for this period")
    )
    price_per_child = models.DecimalField(
        _("Price Per Child"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Price per child for this period (optional, defaults to adult price)")
    )
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tour.name} - {self.start_date} to {self.end_date}"

    class Meta:
        ordering = ['tour', 'start_date']
        verbose_name = _("Seasonal Tour Price")
        verbose_name_plural = _("Seasonal Tour Prices")
