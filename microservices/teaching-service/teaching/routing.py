# WebSocket routing for real-time teaching
from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Main teaching session WebSocket
    re_path(r'ws/teaching/(?P<session_id>\w+)/$', consumers.TeachingConsumer.as_asgi()),
    
    # Whiteboard WebSocket for collaborative drawing
    re_path(r'ws/whiteboard/(?P<session_id>\w+)/$', consumers.WhiteboardConsumer.as_asgi()),
    
    # Voice/Audio WebSocket for real-time voice synthesis
    re_path(r'ws/voice/(?P<session_id>\w+)/$', consumers.VoiceConsumer.as_asgi()),
    
    # AI Tutor WebSocket for real-time Q&A
    re_path(r'ws/ai-tutor/(?P<session_id>\w+)/$', consumers.AITutorConsumer.as_asgi()),
    
    # Session control WebSocket for session management
    re_path(r'ws/session-control/(?P<session_id>\w+)/$', consumers.SessionControlConsumer.as_asgi()),
]