"""
Django settings for teaching_service project.
Real-Time Interactive Teaching with WebSockets
"""
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='teaching-service-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = [
    'daphne',  # ASGI server for Django Channels
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # CORS headers support 
    'rest_framework',
    'channels',
    'teaching',  # Our main teaching app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Fixed CORS middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'teaching_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# ASGI application for WebSockets
ASGI_APPLICATION = 'teaching_service.asgi.application'

# Database (using MongoDB via pymongo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MongoDB Configuration
MONGODB_SETTINGS = {
    'HOST': config('MONGODB_HOST', default='localhost'),
    'PORT': config('MONGODB_PORT', default=27017, cast=int),
    'DATABASE': config('MONGODB_NAME', default='Gnyansetu_Teaching'),
}

# Redis Configuration for Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# RabbitMQ Configuration (for future scaling)
RABBITMQ_SETTINGS = {
    'HOST': config('RABBITMQ_HOST', default='localhost'),
    'PORT': config('RABBITMQ_PORT', default=5672, cast=int),
    'USER': config('RABBITMQ_USER', default='guest'),
    'PASSWORD': config('RABBITMQ_PASSWORD', default='guest'),
    'VHOST': config('RABBITMQ_VHOST', default='/'),
}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')

# Voice & Speech Configuration
VOICE_SETTINGS = {
    'TTS_ENGINE': config('TTS_ENGINE', default='azure'),  # azure, openai, gtts
    'AZURE_SPEECH_KEY': config('AZURE_SPEECH_KEY', default=''),
    'AZURE_SPEECH_REGION': config('AZURE_SPEECH_REGION', default='eastus'),
    'OPENAI_API_KEY': config('OPENAI_API_KEY', default=''),
    'DEFAULT_VOICE': config('DEFAULT_VOICE', default='neural'),
    'SPEECH_SPEED': config('SPEECH_SPEED', default=1.0, cast=float),
    'VOICE_LANGUAGE': config('VOICE_LANGUAGE', default='en-US'),
}

# Teaching Configuration
TEACHING_SETTINGS = {
    'MAX_CONCURRENT_SESSIONS': config('MAX_CONCURRENT_SESSIONS', default=100, cast=int),
    'SESSION_TIMEOUT': config('SESSION_TIMEOUT', default=3600, cast=int),  # 1 hour
    'WHITEBOARD_MAX_SIZE': config('WHITEBOARD_MAX_SIZE', default=10, cast=int),  # MB
    'LESSON_SERVICE_URL': config('LESSON_SERVICE_URL', default='http://localhost:8003'),
    'ENABLE_VOICE_SYNTHESIS': config('ENABLE_VOICE_SYNTHESIS', default=True, cast=bool),
    'ENABLE_REAL_TIME_AI': config('ENABLE_REAL_TIME_AI', default=True, cast=bool),
}

# WebSocket Configuration
WEBSOCKET_SETTINGS = {
    'MAX_CONNECTIONS_PER_USER': config('MAX_CONNECTIONS_PER_USER', default=5, cast=int),
    'HEARTBEAT_INTERVAL': config('HEARTBEAT_INTERVAL', default=30, cast=int),
    'MESSAGE_RATE_LIMIT': config('MESSAGE_RATE_LIMIT', default=100, cast=int),  # per minute
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
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (for audio/video content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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

# CORS settings for frontend integration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Landing Page
    "http://localhost:3001",  # Dashboard
    "http://localhost:8000",  # API Gateway
]

CORS_ALLOW_CREDENTIALS = True

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)s%(reset)s %(asctime)s %(name)s %(message)s',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'teaching_service.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'teaching': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'websockets': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}