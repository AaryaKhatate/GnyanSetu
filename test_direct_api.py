#!/usr/bin/env python3
"""
Direct test of the lesson service without PDF
"""
import requests

def test_direct_api():
    """Test the generate lesson endpoint directly"""
    
    try:
        # Test health first
        health_response = requests.get("http://localhost:8003/health/")
        print(f"🔍 Health Check: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Service: {health_data.get('service')}")
            print(f"   Status: {health_data.get('status')}")
            print(f"   AI Model: {health_data.get('ai_model')}")
        
        print("\n" + "="*50)
        
        # Test the generate endpoint with minimal data
        url = "http://localhost:8003/api/generate-lesson/"
        
        # Create minimal form data without file
        data = {
            'user_id': 'test_user_direct',
            'lesson_type': 'interactive'
        }
        
        print(f"🚀 Testing generate lesson endpoint...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        # Test POST request without file to see what error we get
        response = requests.post(url, data=data)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Content: {response.text}")
        
        if response.status_code in [200, 400]:  # Expected responses
            try:
                result = response.json()
                print(f"\n📋 Parsed Response:")
                for key, value in result.items():
                    print(f"   {key}: {value}")
            except:
                print("   Could not parse JSON response")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_direct_api()