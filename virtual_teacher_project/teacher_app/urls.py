# teacher_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_view, name='dashboard'),  # Main dashboard at root
    path('dashboard/', views.teacher_view, name='teacher'),  # Also available at /dashboard/
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    
    # Authentication endpoints
    path('api/auth/login/', views.api_login, name='api_login'),
    path('api/auth/signup/', views.api_signup, name='api_signup'),
    path('api/auth/logout/', views.api_logout, name='api_logout'),
    path('api/auth/forgot-password/', views.api_forgot_password, name='api_forgot_password'),
    path('api/auth/profile/', views.api_user_profile, name='api_user_profile'),
    
    # API endpoints for React frontend
    path('api/students/', views.api_students, name='api_students'),
    path('api/lessons/', views.api_lessons, name='api_lessons'),
    path('api/quizzes/', views.api_quizzes, name='api_quizzes'),
    path('api/progress/', views.api_progress, name='api_progress'),
    
    # Chat History endpoints
    path('api/conversations/', views.api_conversations, name='api_conversations'),
    path('api/conversations/<str:conversation_id>/messages/', views.api_conversation_messages, name='api_conversation_messages'),
    path('api/conversations/<str:conversation_id>/delete/', views.api_delete_conversation, name='api_conversation_delete'),
    path('api/conversations/<str:conversation_id>/rename/', views.api_rename_conversation, name='api_rename_conversation'),
]
