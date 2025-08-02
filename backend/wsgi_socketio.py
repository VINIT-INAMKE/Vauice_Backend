"""
WSGI config for backend project with Socket.IO support.
This replaces the ASGI setup and uses regular WSGI with Socket.IO
"""

import os
import django
from django.core.wsgi import get_wsgi_application
import socketio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import after Django setup
from chat.socketio_complete import sio

# Create Django WSGI app
django_app = get_wsgi_application()

# Create Socket.IO app that wraps Django
application = socketio.WSGIApp(sio, django_app, socketio_path='/socket.io/')

# This allows both:
# - Regular HTTP/API requests to Django
# - Socket.IO connections on /socket.io/ path