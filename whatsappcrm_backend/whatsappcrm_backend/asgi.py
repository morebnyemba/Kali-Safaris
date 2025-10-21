# whatsappcrm_backend/whatsappcrm_backend/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Set the DJANGO_SETTINGS_MODULE environment variable.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')

# Initialize Django's ASGI application early to populate the apps registry.
django_asgi_app = get_asgi_application()

# Import middleware and routing after Django has been initialized.
from whatsappcrm_backend.middleware import TokenAuthMiddleware

import stats.routing
import conversations.routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(URLRouter(
            stats.routing.websocket_urlpatterns + conversations.routing.websocket_urlpatterns
        ))
    ),
})