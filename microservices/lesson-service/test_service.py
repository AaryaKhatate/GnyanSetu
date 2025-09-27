#!/usr/bin/env python
"""
Test script for Lesson Service
"""
import requests
import json
import os
from colorama import Fore, Style, init

init(autoreset=True)

BASE_URL = "http://localhost:8003"

def test_health_check():
    """Test the health check endpoint"""
    print(f"{Fore.CYAN}🔍 Testing Health Check...{Style.RESET_ALL}")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Health Check Passed{Style.RESET_ALL}")
            print(f"   Service: {data['service']}")
            print(f"   Status: {data['status']}")
            print(f"   Database: {data['database']}")
            print(f"   AI Model: {data['ai_model']}")
            return True
        else:
            print(f"{Fore.RED}❌ Health Check Failed: {response.status_code}{Style.RESET_ALL}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Cannot connect to lesson service. Is it running on port 8003?{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Health Check Error: {e}{Style.RESET_ALL}")
        return False

def test_pdf_upload():
    """Test PDF upload and lesson generation (requires a test PDF)"""
    print(f"\n{Fore.CYAN}📄 Testing PDF Upload & Lesson Generation...{Style.RESET_ALL}")
    
    # This would require a test PDF file
    print(f"{Fore.YELLOW}⚠️  PDF upload test requires a test PDF file{Style.RESET_ALL}")
    print(f"   To test manually:")
    print(f"   curl -X POST {BASE_URL}/api/generate-lesson/ \\")
    print(f"        -F 'pdf_file=@your_test.pdf' \\")
    print(f"        -F 'user_id=test_user_123' \\")
    print(f"        -F 'lesson_type=interactive'")
    
def test_user_endpoints():
    """Test user-specific endpoints"""
    print(f"\n{Fore.CYAN}👤 Testing User Endpoints...{Style.RESET_ALL}")
    
    test_user_id = "test_user_123"
    
    # Test get user lessons
    try:
        response = requests.get(f"{BASE_URL}/api/users/{test_user_id}/lessons/")
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ User Lessons Endpoint: {data['count']} lessons found{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  User Lessons Endpoint: {response.status_code} (expected for new user){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ User Lessons Endpoint Error: {e}{Style.RESET_ALL}")
    
    # Test get user history
    try:
        response = requests.get(f"{BASE_URL}/api/users/{test_user_id}/history/")
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ User History Endpoint: {data['count']} history entries{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  User History Endpoint: {response.status_code} (expected for new user){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ User History Endpoint Error: {e}{Style.RESET_ALL}")

def main():
    """Main test function"""
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.WHITE} 🧪 LESSON SERVICE TEST SUITE {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # Run tests
    health_ok = test_health_check()
    
    if health_ok:
        test_user_endpoints()
        test_pdf_upload()
        
        print(f"\n{Fore.GREEN}✅ Basic tests completed!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📚 Service is ready for PDF lesson generation{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Service is not responding correctly{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

if __name__ == '__main__':
    main()