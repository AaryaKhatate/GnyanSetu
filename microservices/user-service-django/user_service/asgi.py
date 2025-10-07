"""
ASGI config for GnyanSetu User Authentication Service.
Production-ready ASGI configuration with Daphne support.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

# Export the ASGI application
application = django_asgi_app
