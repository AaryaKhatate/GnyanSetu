"""
Django settings for lesson_service project.
GnyanSetu Lesson Generation Service - Port 8003
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='lesson-service-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0','api-gateway-2bhq.onrender.com']

# Application definition
INSTALLED_APPS = [
    'daphne',  # ASGI server for production-grade Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'lessons',  # Our main lessons app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lesson_service.urls'

# ASGI application
ASGI_APPLICATION = 'lesson_service.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lesson_service.wsgi.application'

# Database - Using MongoDB
DATABASES = {}

# MongoDB Configuration
MONGODB_SETTINGS = {
    'host': config('MONGODB_HOST', default='localhost'),
    'port': config('MONGODB_PORT', default=27017, cast=int),
    'db': config('MONGODB_NAME', default='Gnyansetu_Lessons'),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Allow specific origins for your GnyanSetu services
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Landing Page
    "http://localhost:3001",  # Dashboard  
    "http://localhost:8000",  # API Gateway
    "http://localhost:8001",  # PDF Service
    "http://localhost:8002",  # User Service
    "http://localhost:8003",  # Lesson Service (self)
    "http://localhost:8004",  # Teaching Service
    "http://127.0.0.1:3001",  # Dashboard alternate
    "http://127.0.0.1:8003",  # Lesson Service alternate
]

CORS_ALLOW_CREDENTIALS = True

# Allow all methods for CORS - Enhanced for ASGI
CORS_ALLOW_ALL_ORIGINS = False  # Keep specific origins for security
CORS_PREFLIGHT_MAX_AGE = 86400  # Cache preflight for 24 hours

# Allow these methods
CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Allow these headers in requests
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF trusted origins for ASGI
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3001",  # Dashboard
    "http://127.0.0.1:3001",  # Dashboard alternate
    "http://localhost:8003",  # Self
    "http://127.0.0.1:8003",  # Self alternate
]

# AI Configuration - Google Gemini
AI_SETTINGS = {
    'GEMINI_API_KEY': config('GEMINI_API_KEY', default=''),
    'MODEL_NAME': config('GEMINI_MODEL', default='gemini-2.0-flash-exp'),
    'MAX_TOKENS': config('MAX_TOKENS', default=8000, cast=int),
    'TEMPERATURE': config('TEMPERATURE', default=0.7, cast=float),
}

# PDF Processing Settings
PDF_SETTINGS = {
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
    'ALLOWED_EXTENSIONS': ['.pdf'],
    'EXTRACT_IMAGES': True,
    'OCR_ENABLED': True,
    'TESSERACT_PATH': config('TESSERACT_PATH', default=''),
}

# Service URLs
SERVICE_URLS = {
    'PDF_SERVICE': config('PDF_SERVICE_URL', default='http://localhost:8001'),
    'USER_SERVICE': config('USER_SERVICE_URL', default='http://localhost:8002'),
    'API_GATEWAY': config('API_GATEWAY_URL', default='http://localhost:8000'),
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'lessons': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Django Channels Configuration with RabbitMQ
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_rabbitmq.core.RabbitmqChannelLayer",
        "CONFIG": {
            "host": config('RABBITMQ_HOST', default='localhost'),
            "port": config('RABBITMQ_PORT', default=5672, cast=int),
            "username": config('RABBITMQ_USER', default='guest'),
            "password": config('RABBITMQ_PASS', default='guest'),
            "virtual_host": config('RABBITMQ_VHOST', default='/'),
        },
    },
}

