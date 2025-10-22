# Test script for User Management Service
import requests
import json
import sys
import time

# User Service URL
USER_SERVICE_URL = "http://localhost:8002"

# Test data
test_user = {
    "name": "Test User",
    "email": "test@gnyansetu.com",
    "password": "testpass123"
}

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{USER_SERVICE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check Passed")
            print(f"   Status: {data['status']}")
            print(f"   MongoDB Connected: {data['mongodb_connected']}")
            print(f"   RabbitMQ Connected: {data['rabbitmq_connected']}")
            return True
        else:
            print(f"❌ Health Check Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_user_registration():
    """Test user registration."""
    print("\n👤 Testing User Registration...")
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/api/auth/register",
            json=test_user,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ User Registration Successful")
            print(f"   User ID: {data['user']['_id'][:8]}...")
            print(f"   Name: {data['user']['name']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Token: {data['token'][:20]}...")
            return data['token']
        else:
            print(f"❌ User Registration Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ User Registration Error: {e}")
        return None

def test_user_login():
    """Test user login."""
    print("\n🔐 Testing User Login...")
    try:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        response = requests.post(
            f"{USER_SERVICE_URL}/api/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User Login Successful")
            print(f"   User ID: {data['user']['_id'][:8]}...")
            print(f"   Name: {data['user']['name']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Token: {data['token'][:20]}...")
            return data['token']
        else:
            print(f"❌ User Login Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ User Login Error: {e}")
        return None

def test_get_profile(token):
    """Test getting user profile."""
    if not token:
        print("\n⚠️  Skipping profile test (no token)")
        return False
        
    print("\n👤 Testing Get Profile...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{USER_SERVICE_URL}/api/auth/profile", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get Profile Successful")
            print(f"   Name: {data['user']['name']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Role: {data['user']['role']}")
            return True
        else:
            print(f"❌ Get Profile Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get Profile Error: {e}")
        return False

def test_verify_token(token):
    """Test token verification."""
    if not token:
        print("\n⚠️  Skipping token verification test (no token)")
        return False
        
    print("\n🔒 Testing Token Verification...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{USER_SERVICE_URL}/api/auth/verify-token", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token Verification Successful")
            print(f"   User ID: {data['user']['user_id'][:8]}...")
            print(f"   Email: {data['user']['email']}")
            return True
        else:
            print(f"❌ Token Verification Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Token Verification Error: {e}")
        return False

def test_forgot_password():
    """Test forgot password functionality."""
    print("\n🔄 Testing Forgot Password...")
    try:
        forgot_data = {
            "email": test_user["email"]
        }
        
        response = requests.post(
            f"{USER_SERVICE_URL}/api/auth/forgot-password",
            json=forgot_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Forgot Password Request Successful")
            print(f"   Message: {data['message']}")
            print(f"   Check console logs for reset link")
            return True
        else:
            print(f"❌ Forgot Password Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Forgot Password Error: {e}")
        return False

def test_logout(token):
    """Test user logout."""
    if not token:
        print("\n⚠️  Skipping logout test (no token)")
        return False
        
    print("\n🚪 Testing User Logout...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(f"{USER_SERVICE_URL}/api/auth/logout", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User Logout Successful")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ User Logout Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User Logout Error: {e}")
        return False

def run_all_tests():
    """Run all User Service tests."""
    print("🚀 Starting User Management Service Tests")
    print("=" * 60)
    
    # Test health check first
    if not test_health_check():
        print("\n❌ Health check failed. Make sure the User Service is running.")
        print("   Start the service with: python app.py")
        sys.exit(1)
    
    # Test user registration
    token = test_user_registration()
    
    # If registration fails (user already exists), try login
    if not token:
        print("\n💡 Registration failed (user might already exist), trying login...")
        time.sleep(1)
        token = test_user_login()
    
    # Test other endpoints with token
    test_get_profile(token)
    test_verify_token(token)
    test_forgot_password()
    test_logout(token)
    
    print("\n" + "=" * 60)
    print("🎉 User Management Service Tests Completed!")
    
    if token:
        print(f"\n💡 You can test authenticated endpoints manually:")
        print(f"   Authorization: Bearer {token[:30]}...")
        print(f"   GET {USER_SERVICE_URL}/api/auth/profile")
        print(f"   POST {USER_SERVICE_URL}/api/auth/logout")

if __name__ == "__main__":
    run_all_tests()