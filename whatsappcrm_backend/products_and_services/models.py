from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class Tour(models.Model):
    """
    Represents a tour package offered by the agency.
    This replaces the previous Product model.
    """
    # Constants for validation and conversion
    MINUTES_PER_HOUR = 60
    HOURS_PER_DAY = 24
    MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR  # 1440
    HOURS_PER_YEAR = 365 * HOURS_PER_DAY  # 8760 hours
    DAYS_PER_YEAR = 365
    
    class TourCategory(models.TextChoices):
        SAFARI = 'safari', _('Safari')
        CULTURAL = 'cultural', _('Cultural Tour')
        ADVENTURE = 'adventure', _('Adventure & Sports')
        CITY = 'city', _('City Tour')
        CUSTOM = 'custom', _('Custom Package')
    
    class DurationUnit(models.TextChoices):
        HOURS = 'hours', _('Hours')
        DAYS = 'days', _('Days')
        MINUTES = 'minutes', _('Minutes')

    name = models.CharField(_("Tour Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=TourCategory.choices,
        default=TourCategory.SAFARI
    )
    base_price = models.DecimalField(_("Base Price"), max_digits=10, decimal_places=2, help_text=_("Base price per adult."))
    
    # New flexible duration field
    duration_value = models.PositiveIntegerField(
        _("Duration Value"),
        default=1,
        help_text=_("Numeric value for the duration (e.g., 2, 30, 1)")
    )
    duration_unit = models.CharField(
        _("Duration Unit"),
        max_length=10,
        choices=DurationUnit.choices,
        default=DurationUnit.DAYS,
        help_text=_("Unit of time for the duration")
    )
    
    # Keep old field for backward compatibility
    duration_days = models.PositiveIntegerField(
        _("Duration in Days"),
        default=1,
        help_text=_("Deprecated: Use duration_value and duration_unit instead. This field is kept for backward compatibility.")
    )
    
    location = models.CharField(_("Location / Region"), max_length=255, blank=True)
    image = models.ImageField(_("Tour Image"), upload_to='tours/', blank=True, null=True, help_text=_("A representative image for the tour."))
    is_active = models.BooleanField(_("Is Active"), default=True, help_text=_("Is this tour currently available for booking?"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_duration_display_text(self):
        """Returns a human-readable duration string."""
        value = self.duration_value
        
        if self.duration_unit == self.DurationUnit.MINUTES:
            if value == 1:
                return "1 minute"
            return f"{value} minutes"
        elif self.duration_unit == self.DurationUnit.HOURS:
            if value == 1:
                return "1 hour"
            return f"{value} hours"
        else:  # DAYS
            if value == 1:
                return "1 day"
            return f"{value} days"
    
    def get_duration_in_days(self):
        """Returns duration converted to days (for backward compatibility)."""
        if self.duration_unit == self.DurationUnit.MINUTES:
            # Convert minutes to days (rounded up using ceiling division)
            return max(1, (self.duration_value + self.MINUTES_PER_DAY - 1) // self.MINUTES_PER_DAY)
        elif self.duration_unit == self.DurationUnit.HOURS:
            # Convert hours to days (rounded up using ceiling division)
            return max(1, (self.duration_value + self.HOURS_PER_DAY - 1) // self.HOURS_PER_DAY)
        return self.duration_value
    
    def clean(self):
        """Validate duration values."""
        if self.duration_value <= 0:
            raise ValidationError({'duration_value': 'Duration value must be greater than 0.'})
        
        if self.duration_unit == self.DurationUnit.MINUTES and self.duration_value > self.HOURS_PER_YEAR * self.MINUTES_PER_HOUR:
            raise ValidationError({
                'duration_value': f'Duration in minutes cannot exceed {self.HOURS_PER_YEAR * self.MINUTES_PER_HOUR} (1 year).'
            })
        
        if self.duration_unit == self.DurationUnit.HOURS and self.duration_value > self.HOURS_PER_YEAR:
            raise ValidationError({
                'duration_value': f'Duration in hours cannot exceed {self.HOURS_PER_YEAR} (1 year).'
            })
        
        if self.duration_unit == self.DurationUnit.DAYS and self.duration_value > self.DAYS_PER_YEAR:
            raise ValidationError({
                'duration_value': f'Duration in days cannot exceed {self.DAYS_PER_YEAR} (1 year).'
            })
    
    def save(self, *args, **kwargs):
        """Auto-sync duration_days with new duration fields for backward compatibility."""
        self.full_clean()
        # Update duration_days based on new fields
        self.duration_days = self.get_duration_in_days()
        super().save(*args, **kwargs)

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
