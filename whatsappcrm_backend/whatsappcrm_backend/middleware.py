# whatsappcrm_backend/whatsappcrm_backend/middleware.py

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.db import close_old_connections

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Asynchronously gets a user from a JWT token.
    """
    try:
        # This will validate the token's signature and expiration
        UntypedToken(token_key)
    except (InvalidToken, TokenError):
        return AnonymousUser()

    from rest_framework_simplejwt.settings import api_settings
    try:
        token = UntypedToken(token_key)
        user_id = token.get(api_settings.USER_ID_CLAIM)
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for Django Channels that authenticates users using a JWT token
    passed in the query string.
    """
    async def __call__(self, scope, receive, send):
        close_old_connections()

        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            # If no token is provided, default to an anonymous user.
            # The consumer will handle the rejection.
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)