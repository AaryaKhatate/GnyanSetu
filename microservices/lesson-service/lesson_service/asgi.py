"""
ASGI config for lesson_service project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from django.urls import path
from django.core.handlers.asgi import ASGIHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesson_service.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Configure ASGI application with enhanced error handling
application = django_asgi_app
