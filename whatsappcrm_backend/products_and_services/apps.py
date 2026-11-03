from django.apps import AppConfig


class ProductsAndServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products_and_services'

    def ready(self):
        from . import signals  # noqa: F401
