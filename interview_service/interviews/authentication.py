"""
Custom JWT authentication for interview_service.
Validates tokens issued by auth_service using shared secret key.
"""

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import UserProfile


class JWTAuthenticationFromAuthService(authentication.BaseAuthentication):
    """
    Custom JWT authentication that validates tokens from auth_service
    and maps to interview_service UserProfile.

    Tokens are validated using a shared secret key between auth_service
    and interview_service, enabling stateless authentication.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).

        Returns None if authentication is not attempted (no token provided).
        Raises AuthenticationFailed if authentication fails.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        # Check for Bearer token format
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed('Invalid authorization header format. Expected: Bearer <token>')

        token = parts[1]

        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                settings.JWT_SIGNING_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Extract user_id from token payload
            user_id = payload.get('user_id')
            if not user_id:
                raise exceptions.AuthenticationFailed('Token payload missing user_id')

            # Get UserProfile (synced from auth_service via Kafka)
            try:
                user_profile = UserProfile.objects.get(id=user_id)
            except UserProfile.DoesNotExist:
                raise exceptions.AuthenticationFailed(
                    'User profile not found. User may not be synced yet.'
                )

            # Check if user is active
            if not user_profile.is_active:
                raise exceptions.AuthenticationFailed('User account is disabled')

            # Return user profile and token payload
            return (user_profile, payload)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return 'Bearer realm="api"'


class WebSocketJWTAuthentication:
    """
    JWT authentication for WebSocket connections.
    Token is extracted from query parameters since WebSockets don't support headers.

    Usage in WebSocket consumer:
        from interviews.authentication import WebSocketJWTAuthentication

        async def connect(self):
            user = await WebSocketJWTAuthentication.authenticate_websocket(self.scope)
            if not user:
                await self.close()
            self.user = user
    """

    @staticmethod
    async def authenticate_websocket(scope):
        """
        Authenticate WebSocket connection using token from query string.

        Args:
            scope: ASGI scope dict containing connection info

        Returns:
            UserProfile instance if authentication succeeds, None otherwise
        """
        from channels.db import database_sync_to_async

        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = params.get('token')

        if not token:
            return None

        try:
            # Decode token
            payload = jwt.decode(
                token,
                settings.JWT_SIGNING_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            user_id = payload.get('user_id')
            if not user_id:
                return None

            # Get user profile from database (async-safe)
            @database_sync_to_async
            def get_user_profile(user_id):
                try:
                    profile = UserProfile.objects.get(id=user_id, is_active=True)
                    return profile
                except UserProfile.DoesNotExist:
                    return None

            user_profile = await get_user_profile(user_id)
            return user_profile

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
        except Exception:
            return None
