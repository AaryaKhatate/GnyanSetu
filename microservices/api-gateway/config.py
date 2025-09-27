# API Gateway Configuration
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gateway Configuration
    GATEWAY_PORT = int(os.getenv('GATEWAY_PORT', 8000))
    GATEWAY_HOST = os.getenv('GATEWAY_HOST', '0.0.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3001,http://localhost:8000,http://localhost:3000').split(',')
    
    # Timeout Configuration
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', 5))
    
    # Service URLs (can be overridden via environment variables)
    PDF_SERVICE_URL = os.getenv('PDF_SERVICE_URL', 'http://localhost:8001')
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:8002')
    AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8003')
    QUIZ_SERVICE_URL = os.getenv('QUIZ_SERVICE_URL', 'http://localhost:8004')
    REALTIME_SERVICE_URL = os.getenv('REALTIME_SERVICE_URL', 'http://localhost:8005')
    ANALYTICS_SERVICE_URL = os.getenv('ANALYTICS_SERVICE_URL', 'http://localhost:8006')
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Security Configuration
    API_KEY_REQUIRED = os.getenv('API_KEY_REQUIRED', 'False').lower() == 'true'
    API_KEY = os.getenv('API_KEY', '')

config = Config()