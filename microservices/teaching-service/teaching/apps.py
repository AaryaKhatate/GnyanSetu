from django.apps import AppConfig

class TeachingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'teaching'
    verbose_name = 'Real-Time Teaching Service'
    
    def ready(self):
        """Initialize teaching service components"""
        # Import services to ensure they're initialized
        try:
            from .voice_service import voice_service
            from .ai_tutor import ai_tutor_service  
            from .lesson_integration import lesson_integration_service
        except ImportError:
            pass  # Services will be imported when needed