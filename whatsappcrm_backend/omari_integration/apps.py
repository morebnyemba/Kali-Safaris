from django.apps import AppConfig


class OmariIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'omari_integration'
    verbose_name = 'Omari Payment Integration'
    
    def ready(self):
        """Register flow actions when app is ready."""
        # Import here to avoid circular imports
        from .flow_actions import register_payment_actions
        register_payment_actions()
