from django.apps import AppConfig


class CBZIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cbz_integration'
    verbose_name = 'CBZ/iVeri Payment Integration'

    def ready(self):
        """Register flow actions when app is ready."""
        # Import here to avoid circular imports
        from .flow_actions import register_cbz_payment_actions
        register_cbz_payment_actions()
