# whatsappcrm_backend/conversations/apps.py

from django.apps import AppConfig

class ConversationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'conversations'
    verbose_name = "Conversations Management"

    def ready(self):
        """
        Import signals so they are connected when the app is ready.
        """
        import conversations.signals  # noqa
