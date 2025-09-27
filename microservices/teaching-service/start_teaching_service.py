#!/usr/bin/env python3
"""
Real-Time Teaching Service Startup Script
Django Channels + WebSockets + Voice + AI Tutor
"""
import os
import sys
import logging
import subprocess
import time
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teaching_service.settings')

# Configure logging with colors
import colorlog

def setup_logging():
    """Setup colored logging for better visibility"""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s%(reset)s %(asctime)s %(name)s %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger

def check_dependencies():
    """Check if required services are running"""
    logger = logging.getLogger(__name__)
    
    print("🔍 Checking Teaching Service dependencies...")
    
    # Check MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        logger.info("✅ MongoDB is running")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}")
        logger.info("📝 MongoDB is recommended but not required for basic testing")
    
    # Check Redis (for Django Channels)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        logger.info("✅ Redis is running")
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")
        logger.info("📝 Redis is required for WebSocket functionality")
    
    # Check if lesson service is running
    try:
        import requests
        response = requests.get('http://localhost:8003/health/', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Lesson Service is running")
        else:
            logger.warning("⚠️  Lesson Service not responding properly")
    except Exception as e:
        logger.warning(f"⚠️  Lesson Service connection failed: {e}")
        logger.info("📝 Lesson Service integration will be limited")

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'media/voice',
        'static',
        'staticfiles'
    ]
    
    for directory in directories:
        dir_path = current_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)

def run_django_setup():
    """Run Django setup commands"""
    logger = logging.getLogger(__name__)
    
    logger.info("⚙️  Running Django setup...")
    
    try:
        # Import Django
        import django
        from django.core.management import execute_from_command_line
        
        # Setup Django
        django.setup()
        
        # Run migrations (for SQLite fallback database)
        logger.info("🔄 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        
        # Collect static files
        logger.info("📦 Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        
        logger.info("✅ Django setup completed")
        
    except Exception as e:
        logger.error(f"❌ Django setup failed: {e}")
        return False
    
    return True

def start_service():
    """Start the teaching service using Daphne (ASGI server)"""
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Real-Time Teaching Service...")
    
    # Service information
    service_info = """
╭─────────────────────────────────────────────────────────────╮
│  🎓 GnyanSetu Real-Time Teaching Service                    │
│                                                             │
│  🌐 Service URL: http://localhost:8004                      │
│  📡 WebSocket Support: ✅ Enabled                           │
│  🎤 Voice Synthesis: ✅ Enabled                             │
│  🤖 AI Tutor: ✅ Enabled                                    │
│  🎨 Whiteboard: ✅ Enabled                                  │
│  📊 Real-time Analytics: ✅ Enabled                         │
│                                                             │
│  📋 API Endpoints:                                          │
│    • Health: /health/                                       │
│    • Sessions: /api/sessions/                               │
│    • Voice: /api/voice/                                     │
│    • AI Tutor: /api/ai-tutor/                              │
│    • Whiteboard: /api/whiteboard/                          │
│                                                             │
│  🔌 WebSocket Endpoints:                                    │
│    • Teaching: /ws/teaching/{session_id}/                   │
│    • Whiteboard: /ws/whiteboard/{session_id}/               │
│    • Voice: /ws/voice/{session_id}/                         │
│    • AI Tutor: /ws/ai-tutor/{session_id}/                  │
│    • Session Control: /ws/session-control/{session_id}/     │
│                                                             │
│  🎯 Integration:                                            │
│    • Lesson Service: http://localhost:8003                  │
│    • API Gateway: http://localhost:8000                     │
│                                                             │
╰─────────────────────────────────────────────────────────────╯
    """
    
    print(service_info)
    
    try:
        # Start Daphne ASGI server
        logger.info("🔥 Starting Daphne ASGI server on port 8004...")
        
        # Run Daphne
        subprocess.run([
            sys.executable, '-m', 'daphne',
            '-b', '0.0.0.0',
            '-p', '8004',
            'teaching_service.asgi:application'
        ], cwd=current_dir)
        
    except KeyboardInterrupt:
        logger.info("🛑 Teaching Service stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting Teaching Service: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    # Setup logging
    logger = setup_logging()
    
    print("🎓 GnyanSetu Real-Time Teaching Service")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    
    # Create directories
    create_directories()
    
    # Setup Django
    if not run_django_setup():
        logger.error("❌ Failed to setup Django. Exiting...")
        sys.exit(1)
    
    # Start the service
    logger.info("🎯 All checks passed! Starting teaching service...")
    time.sleep(1)
    
    start_service()

if __name__ == '__main__':
    main()