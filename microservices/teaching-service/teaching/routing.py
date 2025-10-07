# WebSocket routing for real-time teaching sessions
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Allow connections with session_id
    re_path(r'ws/teaching/(?P<session_id>\w+)/$', consumers.TeachingConsumer.as_asgi()),
    # Allow connections without session_id (will be assigned dynamically)
    re_path(r'ws/teaching/$', consumers.TeachingConsumer.as_asgi()),
]