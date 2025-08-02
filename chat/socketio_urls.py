"""
Socket.io URL patterns
"""

from django.urls import path, re_path
from . import socketio_views

urlpatterns = [
    # Handle all Socket.io paths
    re_path(r'^.*$', socketio_views.socketio_endpoint, name='socketio-endpoint'),
]