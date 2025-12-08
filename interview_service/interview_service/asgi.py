"""
ASGI config for interview_service project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_service.settings')

# Add the parent directory to sys.path to allow importing common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Initialize OpenTelemetry tracing (without Django instrumentation - that happens in AppConfig.ready())
from common.tracing import setup_tracing
setup_tracing("interview_service", instrument_django=False)

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
# Django instrumentation will be automatically set up via InterviewsConfig.ready()
django_asgi_app = get_asgi_application()

# Import routing after Django initialization
from interviews.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
