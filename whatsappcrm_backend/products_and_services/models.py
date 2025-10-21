from django.db import models
from django.utils.translation import gettext_lazy as _

class ProductCategory(models.Model):
    """
    A category for organizing products.
    """
    name = models.CharField(_("Category Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        help_text=_("Parent category for creating a hierarchy (e.g., 'Software' -> 'Accounting').")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        ordering = ['name']


class Product(models.Model):
    """
    A generic model for all sellable items, including software, hardware, and services.
    """
    class ProductType(models.TextChoices):
        SOFTWARE = 'software', _('Software Package')
        SERVICE = 'service', _('Professional Service')
        HARDWARE = 'hardware', _('Hardware Device')
        MODULE = 'module', _('Software Module')

    class LicenseType(models.TextChoices):
        SUBSCRIPTION = 'subscription', _('Subscription')
        PERPETUAL = 'perpetual', _('Perpetual License')
        ONE_TIME = 'one_time', _('One-Time Purchase')

    name = models.CharField(_("Product Name"), max_length=255)
    sku = models.CharField(_("SKU / Product Code"), max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    product_type = models.CharField(_("Product Type"), max_length=20, choices=ProductType.choices, db_index=True)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    is_active = models.BooleanField(_("Is Active"), default=True, help_text=_("Whether this item is available for sale."))
    image = models.ImageField(_("Product Image"), upload_to='products/', blank=True, null=True)
    
    # Software-specific fields
    license_type = models.CharField(_("License Type"), max_length=20, choices=LicenseType.choices, default=LicenseType.SUBSCRIPTION)
    dedicated_flow_name = models.CharField(
        _("Dedicated Flow Name"), max_length=255, blank=True, null=True,
        help_text=_("The name of the flow to trigger for specific follow-up on this product.")
    )
    
    # Relationships
    parent_product = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='modules', help_text=_("If this is a module, this links to the main software product."))
    compatible_products = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='compatible_with', help_text=_("e.g., A hardware device can be compatible with certain software modules."))
    
    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['name']
