# customer_data/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CustomerDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customer_data'
    verbose_name = _("Customer & Order Data")

    def ready(self):
        import customer_data.signals  # noqa