"""
GnyanSetu User Authentication Service URLs
Comprehensive REST API for user management and authentication
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from test_view import simple_test
from authentication.views import google_oauth_placeholder


def api_root(request):
    """API root endpoint with service information"""
    return JsonResponse({
        'service': 'GnyanSetu User Authentication Service',
        'version': '1.0.0',
        'status': 'active',
        'timestamp': timezone.now().isoformat(),
        'endpoints': {
            'authentication': '/api/v1/',
            'admin': '/admin/',
            'health': '/api/v1/health/',
            'docs': '/api/docs/',
        }
    })


def favicon(request):
    """Return empty favicon response"""
    return HttpResponse(status=204)


urlpatterns = [
    # Test endpoint
    path('test/', simple_test, name='simple_test'),
    
    # API root
    path('', api_root, name='api_root'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints - Primary versioned endpoints
    path('api/v1/', include('authentication.urls')),
    
    # API endpoints - Legacy/Frontend compatibility endpoints 
    path('api/', include('authentication.urls', namespace='api-compat')),
    
    # Social authentication (allauth)
    path('accounts/', include('allauth.urls')),
    
    # Favicon handler
    path('favicon.ico', favicon, name='favicon'),
    
    # Google OAuth compatibility (direct path)
    path('accounts/google/login/', google_oauth_placeholder, name='google_oauth'),
    
    # API documentation (when drf-spectacular is configured)
    # path('api/docs/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
