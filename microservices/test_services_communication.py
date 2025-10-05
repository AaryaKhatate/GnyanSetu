#!/usr/bin/env python3
"""
Comprehensive Service Communication Test
Tests all critical endpoints and communication between services
"""

import requests
import json
import time
from datetime import datetime

class ServiceTester:
    def __init__(self):
        self.api_gateway = "http://localhost:8000"
        self.teaching_service = "http://localhost:8004"
        self.lesson_service = "http://localhost:8003"
        self.results = {}
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print('='*60)
        
    def print_result(self, test_name, success, message="", data=None):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   📝 {message}")
        if data and isinstance(data, dict):
            for key, value in data.items():
                print(f"   📊 {key}: {value}")
        
    def test_service_health(self):
        """Test individual service health"""
        self.print_header("Service Health Checks")
        
        services = [
            ("API Gateway", f"{self.api_gateway}/health"),
            ("Teaching Service", f"{self.teaching_service}/health"),
            ("Lesson Service", f"{self.lesson_service}/health"),
        ]
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                success = response.status_code == 200
                if success:
                    data = response.json()
                    self.print_result(f"{service_name} Health", True, 
                                    f"Status: {data.get('status', 'unknown')}")
                else:
                    self.print_result(f"{service_name} Health", False, 
                                    f"Status Code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.print_result(f"{service_name} Health", False, 
                                f"Connection Error: {str(e)}")
                
    def test_conversations_api(self):
        """Test conversations API through gateway"""
        self.print_header("Conversations API Test")
        
        # Test listing conversations
        try:
            response = requests.get(f"{self.api_gateway}/api/conversations/?user_id=test_user", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                conv_count = len(data.get('conversations', []))
                self.print_result("List Conversations", True, 
                                f"Found {conv_count} conversations")
            else:
                self.print_result("List Conversations", False, 
                                f"Status Code: {response.status_code}")
        except Exception as e:
            self.print_result("List Conversations", False, str(e))
            
        # Test creating conversation
        try:
            create_data = {
                "user_id": "test_user",
                "title": "Test Conversation"
            }
            response = requests.post(f"{self.api_gateway}/api/conversations/", 
                                   json=create_data, timeout=10)
            success = response.status_code in [200, 201]
            if success:
                data = response.json()
                conv_id = data.get('id') or data.get('conversation_id')
                self.print_result("Create Conversation", True, 
                                f"Created conversation: {conv_id}")
                return conv_id
            else:
                self.print_result("Create Conversation", False, 
                                f"Status Code: {response.status_code}")
                return None
        except Exception as e:
            self.print_result("Create Conversation", False, str(e))
            return None
            
    def test_direct_service_communication(self):
        """Test direct communication with services"""
        self.print_header("Direct Service Communication")
        
        # Test Teaching Service directly
        try:
            response = requests.get(f"{self.teaching_service}/api/conversations/?user_id=test_user", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                self.print_result("Direct Teaching Service", True, 
                                f"Response received: {len(data.get('conversations', []))} conversations")
            else:
                self.print_result("Direct Teaching Service", False, 
                                f"Status Code: {response.status_code}")
        except Exception as e:
            self.print_result("Direct Teaching Service", False, str(e))
            
        # Test Lesson Service directly
        try:
            response = requests.get(f"{self.lesson_service}/health", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                self.print_result("Direct Lesson Service", True, 
                                f"Service status: {data.get('status', 'unknown')}")
            else:
                self.print_result("Direct Lesson Service", False, 
                                f"Status Code: {response.status_code}")
        except Exception as e:
            self.print_result("Direct Lesson Service", False, str(e))
            
    def test_api_gateway_routing(self):
        """Test API Gateway routing functionality"""
        self.print_header("API Gateway Routing Test")
        
        # Test service discovery
        try:
            response = requests.get(f"{self.api_gateway}/api/services", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                services = data.get('services', {})
                healthy_services = [name for name, info in services.items() if info.get('healthy')]
                self.print_result("Service Discovery", True, 
                                f"Found {len(services)} services, {len(healthy_services)} healthy")
                
                for service_name, service_info in services.items():
                    health_status = "Healthy" if service_info.get('healthy') else "Unhealthy"
                    print(f"   🔧 {service_name}: {health_status} - {service_info.get('url')}")
            else:
                self.print_result("Service Discovery", False, 
                                f"Status Code: {response.status_code}")
        except Exception as e:
            self.print_result("Service Discovery", False, str(e))
            
    def test_cors_and_headers(self):
        """Test CORS and header handling"""
        self.print_header("CORS and Headers Test")
        
        try:
            headers = {
                'Origin': 'http://localhost:3001',
                'Content-Type': 'application/json'
            }
            response = requests.options(f"{self.api_gateway}/api/conversations/", headers=headers, timeout=10)
            success = response.status_code in [200, 204]
            if success:
                cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
                self.print_result("CORS Preflight", True, 
                                f"Allowed methods: {cors_headers.get('Access-Control-Allow-Methods', 'Unknown')}")
            else:
                self.print_result("CORS Preflight", False, 
                                f"Status Code: {response.status_code}")
        except Exception as e:
            self.print_result("CORS Preflight", False, str(e))
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Service Communication Test")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.test_service_health()
        self.test_api_gateway_routing()
        self.test_direct_service_communication()
        self.test_conversations_api()
        self.test_cors_and_headers()
        
        self.print_header("Test Summary")
        print("✅ All tests completed!")
        print("📋 Review the results above to identify any issues")
        print("\n💡 Next Steps:")
        print("   1. Fix any failed tests")
        print("   2. Check service logs for errors")
        print("   3. Verify database connections")
        print("   4. Test frontend integration")

if __name__ == "__main__":
    tester = ServiceTester()
    tester.run_all_tests()