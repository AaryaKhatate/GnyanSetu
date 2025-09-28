# Simple health check without model imports
from django.http import JsonResponse
from datetime import datetime, timezone

def simple_health_check(request):
    """Simple health check without MongoDB models"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Teaching Service',
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database': 'available',
        'features': {
            'websockets': True,
            'voice_synthesis': True,
            'ai_tutor': True,
            'whiteboard': True,
            'lesson_integration': True
        }
    })