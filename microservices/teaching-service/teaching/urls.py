# Teaching Service URL Configuration
from django.urls import path, include
from . import views

app_name = 'teaching'

# API URL patterns
urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Lesson history and management (Dashboard integration)
    path('lessons/', views.get_user_lessons, name='get_user_lessons'),
    path('lessons/<str:lesson_id>/', views.get_lesson_detail, name='get_lesson_detail'),
    
    # Conversation endpoints (Dashboard needs these exact paths)
    path('conversations/', views.list_conversations, name='list_conversations'),
    path('conversations/create/', views.create_conversation, name='create_conversation'),
    path('conversations/<str:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    
    # User profile endpoints
    path('users/<str:user_id>/profile/', views.get_user_profile, name='get_user_profile'),
    
    # Teaching session management
    path('sessions/start/', views.start_teaching_session, name='start_teaching_session'),
    path('sessions/stop/', views.stop_teaching_session, name='stop_teaching_session'),
    
    # Konva.js whiteboard endpoints
    path('konva/update/', views.update_konva_state, name='update_konva_state'),
    path('konva/<str:session_id>/', views.get_konva_state, name='get_konva_state'),
]