#!/usr/bin/env python
"""
GnyanSetu Lesson Service Startup Script
Port: 8003
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings
from colorama import Fore, Back, Style, init

# Initialize colorama for colored output
init(autoreset=True)

def print_startup_banner():
    """Print colorful startup banner"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{Back.GREEN} 🎓 GNYANSETU LESSON SERVICE - AI LESSON GENERATOR {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🔥 Advanced PDF Processing with OCR")
    print(f"{Fore.GREEN}🤖 AI-Powered Lesson Generation using Google Gemini")
    print(f"{Fore.GREEN}📚 User-specific Lesson History & Management")
    print(f"{Fore.GREEN}🎯 Multiple Lesson Types: Interactive, Quiz, Summary, Detailed")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🌐 Starting on: http://localhost:8003")
    print(f"{Fore.YELLOW}📊 Health Check: http://localhost:8003/health/")
    print(f"{Fore.YELLOW}📋 API Docs: http://localhost:8003/api/")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

def check_environment():
    """Check if all required environment variables and dependencies are available"""
    print(f"{Fore.CYAN}🔍 Checking Environment...{Style.RESET_ALL}")
    
    # Check Django settings
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesson_service.settings')
        django.setup()
        print(f"{Fore.GREEN}✅ Django settings loaded{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Django setup failed: {e}{Style.RESET_ALL}")
        return False
    
    # Check MongoDB connection
    try:
        from lessons.models import check_database_connection
        if check_database_connection():
            print(f"{Fore.GREEN}✅ MongoDB connected{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  MongoDB connection failed (will retry){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️  MongoDB check failed: {e}{Style.RESET_ALL}")
    
    # Check AI configuration
    try:
        ai_key = settings.AI_SETTINGS.get('GEMINI_API_KEY')
        if ai_key and len(ai_key) > 10:
            print(f"{Fore.GREEN}✅ Google Gemini AI configured{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Gemini API key not configured (lessons will use fallback){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️  AI configuration check failed: {e}{Style.RESET_ALL}")
    
    # Check PDF processing capabilities
    try:
        import fitz
        import pytesseract
        from PIL import Image
        print(f"{Fore.GREEN}✅ PDF processing libraries available{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}❌ Missing PDF processing library: {e}{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.CYAN}✅ Environment check completed\n{Style.RESET_ALL}")
    return True

def main():
    """Main startup function"""
    print_startup_banner()
    
    if not check_environment():
        print(f"{Fore.RED}❌ Environment check failed. Please resolve issues before starting.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesson_service.settings')
    
    # Run Django development server
    try:
        print(f"{Fore.GREEN}🚀 Starting Lesson Service...{Style.RESET_ALL}\n")
        execute_from_command_line([
            'manage.py', 
            'runserver', 
            '0.0.0.0:8003',
            '--noreload'  # Disable auto-reload for production-like behavior
        ])
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Lesson Service stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Lesson Service failed to start: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == '__main__':
    main()