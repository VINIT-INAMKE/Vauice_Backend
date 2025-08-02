"""
ASGI config for backend project - DEPRECATED

NOTE: This file is deprecated. We now use Socket.io with WSGI deployment.
Socket.io provides better WebSocket reliability and mobile browser support.

For Socket.io deployment, use backend/wsgi_socketio.py instead.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# DEPRECATED: Django Channels imports commented out (using Socket.io instead)
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from chat.routing import websocket_urlpatterns

# Simple ASGI application without WebSocket routing (Socket.io handles WebSockets)
application = django_asgi_app

# DEPRECATED: Django Channels WebSocket routing
# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             websocket_urlpatterns
#         )
#     ),
# })
