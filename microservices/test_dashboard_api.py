#!/usr/bin/env python3
"""
Dashboard API Test - Simulates the Dashboard's API calls
"""

import requests
import json
import time

def test_dashboard_api_flow():
    """Test the exact API flow that the Dashboard uses"""
    api_base = "http://localhost:8000"
    user_id = "dashboard_user"
    
    print("🎯 Testing Dashboard API Flow")
    print("="*50)
    
    # 1. Test loading chat history (like Dashboard does on startup)
    print("\n📋 1. Loading Chat History...")
    try:
        response = requests.get(f"{api_base}/api/conversations/?user_id={user_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            print(f"   ✅ Found {len(conversations)} conversations")
            for conv in conversations[:3]:  # Show first 3
                print(f"      - {conv.get('title', 'Untitled')} (ID: {conv.get('id', 'N/A')})")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Test creating new conversation (like handleNewChat)
    print("\n📝 2. Creating New Conversation...")
    try:
        create_data = {
            "user_id": user_id,
            "session_name": "Test Dashboard Session",
            "lesson_content": {}
        }
        response = requests.post(f"{api_base}/api/conversations/", json=create_data)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            conv_id = data.get('id') or data.get('conversation_id') or data.get('_id')
            print(f"   ✅ Created conversation: {conv_id}")
            print(f"   Title: {data.get('title', 'N/A')}")
            return conv_id
        else:
            print(f"   ❌ Failed: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None
    
    # 3. Test API Gateway service discovery
    print("\n🔍 3. Checking Service Discovery...")
    try:
        response = requests.get(f"{api_base}/api/services")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', {})
            print(f"   ✅ Found {len(services)} registered services")
            for name, info in services.items():
                status = "Healthy" if info.get('healthy') else "Unhealthy"
                print(f"      - {name}: {status}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Test direct service health
    print("\n🩺 4. Direct Service Health Checks...")
    services = [
        ("Teaching Service", "http://localhost:8004/health"),
        ("Lesson Service", "http://localhost:8003/health"),
    ]
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            print(f"   {name}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ {data.get('status', 'unknown')} - {data.get('service', 'N/A')}")
            else:
                print(f"      ❌ Failed")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🏁 Dashboard API Flow Test Complete")
    print("\n💡 If all tests pass, the Dashboard should work correctly!")
    print("📋 If any tests fail, check the corresponding service logs.")

if __name__ == "__main__":
    test_dashboard_api_flow()