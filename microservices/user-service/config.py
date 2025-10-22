# User Management Service Configuration
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'Gnyansetu_Users')
    
    # JWT Configuration
    JWT_SECRET = os.getenv('JWT_SECRET', 'gnyansetu-secret-key-2024')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    
    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@gnyansetu.com')
    
    # Service Configuration
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8002))
    SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3001,http://localhost:8000,http://localhost:3000').split(',')
    
    # Security Configuration
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 6))
    RESET_TOKEN_EXPIRY_HOURS = int(os.getenv('RESET_TOKEN_EXPIRY_HOURS', 1))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

config = Config()