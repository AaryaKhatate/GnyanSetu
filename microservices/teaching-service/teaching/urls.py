# URL Configuration for Teaching App
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Teaching session endpoints
    path('api/sessions/start/', views.start_teaching_session, name='start_session'),
    path('api/sessions/<str:session_id>/stop/', views.stop_teaching_session, name='stop_session'),
    path('api/sessions/<str:session_id>/status/', views.get_session_status, name='session_status'),
    
    # AI Tutor endpoints
    path('api/tutor/ask/', views.ask_ai_tutor, name='ask_tutor'),
    path('api/tutor/explain/', views.explain_concept, name='explain_concept'),
    path('api/tutor/quiz/', views.generate_quiz, name='generate_quiz'),
    
    # Voice service endpoints
    path('api/voice/synthesize/', views.synthesize_speech, name='synthesize_speech'),
    path('api/voice/recognize/', views.recognize_speech, name='recognize_speech'),
    
    # Lesson integration endpoints
    path('api/lessons/<str:lesson_id>/teach/', views.start_lesson_teaching, name='teach_lesson'),
    path('api/lessons/<str:lesson_id>/progress/', views.get_lesson_progress, name='lesson_progress'),
    
    # Canvas/Konva integration endpoints
    path('api/canvas/save/', views.save_canvas_state, name='save_canvas'),
    path('api/canvas/<str:session_id>/load/', views.load_canvas_state, name='load_canvas'),
]