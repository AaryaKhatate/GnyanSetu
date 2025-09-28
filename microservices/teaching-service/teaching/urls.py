# URL Configuration for Teaching App
from django.urls import path
from . import views
from . import simple_views

urlpatterns = [
    # Health check - using simple version to avoid model import issues
    path('health/', simple_views.simple_health_check, name='health_check'),
    
    # AI Tutor endpoints (existing)
    path('api/tutor/ask/', views.ask_ai_tutor, name='ask_tutor'),
    
    # Add more endpoints as views are implemented
]