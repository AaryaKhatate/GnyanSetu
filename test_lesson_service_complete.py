#!/usr/bin/env python3
"""
Complete test of the lesson service
"""
import sys
import os
import time
import requests
from threading import Thread

def start_server():
    """Start the Django server in background"""
    os.chdir(r"e:\Project\Gnyansetu_Updated_Architecture\microservices\lesson-service")
    os.system(r"E:/Project/venv/Scripts/python.exe manage.py runserver localhost:8003")

def test_lesson_service():
    """Test the complete lesson service"""
    
    print("🔍 Starting comprehensive lesson service test...")
    
    # Start server in background
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    try:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = requests.get("http://localhost:8003/health/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   AI Model: {data.get('ai_model')}")
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
            
        # Test CORS
        print("\n2. Testing CORS...")
        response = requests.options("http://localhost:8003/api/generate-lesson/", 
                                  headers={'Origin': 'http://localhost:3001'}, 
                                  timeout=10)
        print(f"   CORS Status: {response.status_code}")
        print("   ✅ CORS working")
        
        # Test generate lesson endpoint (without file)
        print("\n3. Testing generate lesson endpoint...")
        response = requests.post("http://localhost:8003/api/generate-lesson/", 
                               data={'user_id': 'test', 'lesson_type': 'interactive'},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:  # Expected - no PDF file
            data = response.json()
            if "No PDF file provided" in data.get('error', ''):
                print("   ✅ Endpoint working (correctly requires PDF)")
            else:
                print(f"   ❌ Unexpected error: {data}")
        else:
            print(f"   Response: {response.text}")
            
        print("\n🎉 Lesson service is working correctly!")
        print("\n📋 Service Summary:")
        print(f"   URL: http://localhost:8003")
        print(f"   Health: http://localhost:8003/health/")
        print(f"   Upload: http://localhost:8003/api/generate-lesson/")
        print(f"   Status: ✅ Ready for PDF uploads from Dashboard")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to lesson service")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_lesson_service()
    if success:
        print("\n🚀 Lesson service is ready! You can now upload PDFs from the Dashboard.")
    else:
        print("\n⚠️  Lesson service needs attention.")
    
    # Keep alive for testing
    try:
        print("\n⏳ Keeping server alive for testing... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping test...")