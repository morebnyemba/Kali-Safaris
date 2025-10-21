from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = "System Notifications"

    def ready(self):
        # Import signals so they are connected when the app is ready.
        import notifications.handlers  # noqa