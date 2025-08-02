"""
WSGI config for backend project with Socket.IO support.
CRITICAL FIX: Proper request routing to prevent Socket.io from breaking API calls
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

def conditional_wsgi_app(environ, start_response):
    """
    Route requests properly:
    - /socket.io/* goes to Socket.IO
    - Everything else goes to Django
    """
    path = environ.get('PATH_INFO', '')
    
    # Socket.IO requests
    if path.startswith('/socket.io/'):
        # Create a temporary Socket.IO WSGI app just for this request
        socketio_app = socketio.WSGIApp(sio, None, socketio_path='socket.io')
        return socketio_app(environ, start_response)
    
    # All other requests go to Django
    return django_app(environ, start_response)

# Use the conditional WSGI app
application = conditional_wsgi_app

# Request routing:
# - /socket.io/* → Socket.IO server ONLY
# - /api/* → Django REST API  
# - /admin/* → Django Admin
# - /* → Django views