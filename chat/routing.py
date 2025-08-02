# Django Channels routing - Deprecated (using Socket.io instead)
# from django.urls import re_path
# from . import consumers_deprecated

# websocket_urlpatterns = [
#     re_path(r'ws/chat/(?P<room_id>[0-9a-f-]+)/$', consumers_deprecated.ChatConsumer.as_asgi()),
#     re_path(r'ws/presence/$', consumers_deprecated.PresenceConsumer.as_asgi()),
# ]

# Socket.io handles all WebSocket connections now
websocket_urlpatterns = []
