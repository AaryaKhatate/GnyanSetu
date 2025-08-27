# teacher_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_view, name='teacher'),
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    
    # API endpoints for React frontend
    path('api/students/', views.api_students, name='api_students'),
    path('api/lessons/', views.api_lessons, name='api_lessons'),
    path('api/quizzes/', views.api_quizzes, name='api_quizzes'),
    path('api/progress/', views.api_progress, name='api_progress'),
]