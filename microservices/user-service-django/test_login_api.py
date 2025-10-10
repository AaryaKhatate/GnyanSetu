"""
Test login to verify MongoDB session creation
"""
import requests
import json

print("=" * 60)
print("Testing Login with MongoDB Session Storage")
print("=" * 60)

# Login credentials
login_data = {
    "email": "aarya@gmail.com",
    "password": "Aarya@123"
}

# API endpoint
url = "http://localhost:8000/api/auth/login/"

print(f"\nSending login request to: {url}")
print(f"Email: {login_data['email']}")

try:
    response = requests.post(url, json=login_data, timeout=10)
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ LOGIN SUCCESSFUL!")
        
        data = response.json()
        print(f"\nUser Info:")
        print(f"  - ID: {data.get('user', {}).get('id')}")
        print(f"  - Email: {data.get('user', {}).get('email')}")
        print(f"  - Name: {data.get('user', {}).get('full_name')}")
        
        print(f"\nTokens:")
        print(f"  - Access Token: {data.get('access', 'N/A')[:50]}...")
        print(f"  - Refresh Token: {data.get('refresh', 'N/A')[:50]}...")
        
        print("\n" + "=" * 60)
        print("NOW CHECK DJANGO LOGS FOR:")
        print("✅ MongoDB Session Manager initialized")
        print("✅ Session created in MongoDB for aarya@gmail.com")
        print("=" * 60)
    else:
        print(f"❌ LOGIN FAILED!")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to API Gateway")
    print("   Make sure services are running: http://localhost:8000")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n")
