#!/usr/bin/env python3
"""
Quick test for User Service endpoints
"""

import requests
import json

def test_user_service():
    """Test User Service directly."""
    base_url = "http://localhost:8002"
    
    print("🧪 Testing User Service Directly")
    print("=" * 40)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test signup endpoint
    test_user = {
        "name": "Test User",
        "email": "test123@example.com", 
        "password": "TestPassword123",
        "confirm_password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/signup/", json=test_user, timeout=10)
        print(f"📝 Signup test: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Signup test failed: {e}")
    
    # Test login endpoint
    login_data = {
        "email": "test123@example.com",
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login/", json=login_data, timeout=10)
        print(f"🔑 Login test: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")

def test_via_gateway():
    """Test User Service via API Gateway."""
    base_url = "http://localhost:8000"
    
    print("\n🌐 Testing via API Gateway")
    print("=" * 40)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/auth/health", timeout=5)
        print(f"✅ Health check via gateway: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check via gateway failed: {e}")
        return False
    
    # Test signup via gateway
    test_user = {
        "name": "Gateway Test User",
        "email": "gateway_test@example.com",
        "password": "TestPassword123",
        "confirm_password": "TestPassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/signup/", json=test_user, timeout=10)
        print(f"📝 Signup via gateway: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Signup via gateway failed: {e}")

if __name__ == "__main__":
    print("🔍 User Service & API Gateway Test")
    print("=" * 50)
    
    test_user_service()
    test_via_gateway()
    
    print("\n💡 If tests fail:")
    print("   1. Make sure MongoDB is running")
    print("   2. Start User Service: cd user-service && python app.py")
    print("   3. Start API Gateway: cd api-gateway && python app.py")
    print("   4. Check service logs for errors")