#!/usr/bin/env python3
"""
TEACHING SERVICE - REAL-TIME AI TEACHER
Django Channels + WebSockets + Natural Voice
Interactive Teaching with Konva.js Integration
WebSocket URL: ws://localhost:8004/ws/teaching/

This script starts the Teaching Service with proper configuration.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Start the Teaching Service"""
    print(" Starting Teaching Service - Real-Time AI Teacher")
    print("=" * 60)
    print(" Django Channels + WebSockets + Natural Voice")
    print(" Interactive Teaching with Konva.js Integration")
    print(" WebSocket URL: ws://localhost:8004/ws/teaching/")
    print("=" * 60)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teaching_service.settings')
    
    # Initialize Django
    django.setup()
    
    # Start the server
    try:
        execute_from_command_line(['manage.py', 'runserver', '8004'])
    except KeyboardInterrupt:
        print("\n� Teaching Service stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f" Error starting Teaching Service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()