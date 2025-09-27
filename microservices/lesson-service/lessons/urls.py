# URL Configuration for Lessons App
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Main lesson generation endpoint
    path('api/generate-lesson/', views.process_pdf_and_generate_lesson, name='generate_lesson'),
    
    # User-specific endpoints
    path('api/users/<str:user_id>/lessons/', views.get_user_lessons, name='user_lessons'),
    path('api/users/<str:user_id>/history/', views.get_user_history, name='user_history'),
    
    # Lesson-specific endpoints
    path('api/lessons/<str:lesson_id>/', views.get_lesson_detail, name='lesson_detail'),
    path('api/lessons/<str:lesson_id>/regenerate/', views.regenerate_lesson, name='regenerate_lesson'),
]