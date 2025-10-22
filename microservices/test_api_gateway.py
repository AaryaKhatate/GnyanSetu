#!/usr/bin/env python3
"""
Comprehensive API Gateway Test Script
Tests all routes and service integrations
"""

import requests
import json
import time
import sys
from datetime import datetime

class APIGatewayTester:
    def __init__(self, gateway_url="http://localhost:8000"):
        self.gateway_url = gateway_url
        self.auth_token = None
        self.test_user = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
    def print_header(self, title):
        print("\n" + "="*60)
        print(f"🧪 {title}")
        print("="*60)
    
    def print_result(self, test_name, success, message="", data=None):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   📝 {message}")
        if data and isinstance(data, dict):
            print(f"   📊 Response: {json.dumps(data, indent=2)}")
        print()
    
    def test_gateway_health(self):
        """Test API Gateway health endpoint"""
        self.print_header("API Gateway Health Check")
        
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                self.print_result("Gateway Health", True, 
                                f"Status: {data.get('status', 'unknown')}", data)
                return True
            else:
                self.print_result("Gateway Health", False, 
                                f"Status Code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("Gateway Health", False, f"Connection Error: {str(e)}")
            return False
    
    def test_service_health(self):
        """Test individual service health through gateway"""
        self.print_header("Service Health Checks")
        
        services = [
            ("PDF Service", "/api/pdf/health"),
            ("User Service", "/api/auth/health")
        ]
        
        all_healthy = True
        for service_name, endpoint in services:
            try:
                response = requests.get(f"{self.gateway_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.print_result(f"{service_name} Health", True, 
                                    f"Status: {data.get('status', 'unknown')}")
                else:
                    self.print_result(f"{service_name} Health", False, 
                                    f"Status Code: {response.status_code}")
                    all_healthy = False
            except requests.exceptions.RequestException as e:
                self.print_result(f"{service_name} Health", False, 
                                f"Connection Error: {str(e)}")
                all_healthy = False
        
        return all_healthy
    
    def test_user_registration(self):
        """Test user registration through gateway"""
        self.print_header("User Registration Test")
        
        try:
            response = requests.post(
                f"{self.gateway_url}/api/auth/signup/",
                json=self.test_user,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.print_result("User Registration", True, 
                                "User created successfully", data)
                return True
            elif response.status_code == 400:
                data = response.json()
                if "already exists" in data.get('error', '').lower():
                    self.print_result("User Registration", True, 
                                    "User already exists (expected)")
                    return True
                else:
                    self.print_result("User Registration", False, 
                                    f"Bad Request: {data.get('error', 'Unknown error')}")
                    return False
            else:
                self.print_result("User Registration", False, 
                                f"Status Code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("User Registration", False, 
                            f"Connection Error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login through gateway"""
        self.print_header("User Login Test")
        
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/auth/login/",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.print_result("User Login", True, 
                                f"Token received: {self.auth_token[:20]}..." if self.auth_token else "No token",
                                data)
                return True
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                self.print_result("User Login", False, 
                                f"Status Code: {response.status_code}, Error: {data.get('error', 'Unknown')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("User Login", False, 
                            f"Connection Error: {str(e)}")
            return False
    
    def test_authenticated_request(self):
        """Test authenticated request through gateway"""
        if not self.auth_token:
            self.print_result("Authenticated Request", False, 
                            "Cannot test - no auth token available")
            return False
        
        self.print_header("Authenticated Request Test")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.gateway_url}/api/auth/profile/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_result("Authenticated Profile Request", True, 
                                f"User: {data.get('user', {}).get('email', 'unknown')}", data)
                return True
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                self.print_result("Authenticated Profile Request", False, 
                                f"Status Code: {response.status_code}, Error: {data.get('error', 'Unknown')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("Authenticated Profile Request", False, 
                            f"Connection Error: {str(e)}")
            return False
    
    def test_pdf_service_integration(self):
        """Test PDF service integration through gateway"""
        self.print_header("PDF Service Integration Test")
        
        # Test PDF health endpoint
        try:
            response = requests.get(f"{self.gateway_url}/api/pdf/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_result("PDF Service Health via Gateway", True, 
                                f"Service Status: {data.get('status', 'unknown')}")
                
                # Test PDF list endpoint (requires auth)
                if self.auth_token:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    list_response = requests.get(
                        f"{self.gateway_url}/api/pdf/documents/",
                        headers=headers,
                        timeout=10
                    )
                    
                    if list_response.status_code == 200:
                        list_data = list_response.json()
                        self.print_result("PDF Document List", True, 
                                        f"Found {len(list_data.get('documents', []))} documents")
                        return True
                    else:
                        self.print_result("PDF Document List", False, 
                                        f"Status Code: {list_response.status_code}")
                        return False
                else:
                    self.print_result("PDF Document List", False, 
                                    "Cannot test - no auth token")
                    return False
            else:
                self.print_result("PDF Service Health via Gateway", False, 
                                f"Status Code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("PDF Service Integration", False, 
                            f"Connection Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test gateway error handling"""
        self.print_header("Error Handling Tests")
        
        # Test invalid route
        try:
            response = requests.get(f"{self.gateway_url}/api/invalid/route", timeout=5)
            if response.status_code == 404:
                self.print_result("Invalid Route Handling", True, 
                                "Gateway properly returned 404")
            else:
                self.print_result("Invalid Route Handling", False, 
                                f"Expected 404, got {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.print_result("Invalid Route Handling", False, 
                            f"Connection Error: {str(e)}")
        
        # Test unauthorized access
        try:
            response = requests.get(f"{self.gateway_url}/api/auth/profile/", timeout=5)
            if response.status_code == 401:
                self.print_result("Unauthorized Access Handling", True, 
                                "Gateway properly returned 401")
            else:
                self.print_result("Unauthorized Access Handling", False, 
                                f"Expected 401, got {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.print_result("Unauthorized Access Handling", False, 
                            f"Connection Error: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"🚀 Starting API Gateway Test Suite")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Gateway URL: {self.gateway_url}")
        
        test_results = []
        
        # Core functionality tests
        test_results.append(("Gateway Health", self.test_gateway_health()))
        test_results.append(("Service Health", self.test_service_health()))
        test_results.append(("User Registration", self.test_user_registration()))
        test_results.append(("User Login", self.test_user_login()))
        test_results.append(("Authenticated Request", self.test_authenticated_request()))
        test_results.append(("PDF Integration", self.test_pdf_service_integration()))
        
        # Error handling tests
        self.test_error_handling()
        
        # Summary
        self.print_header("Test Summary")
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API Gateway is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the services and gateway configuration.")
            return False

def main():
    """Main test execution"""
    gateway_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("🧪 GnyanSetu API Gateway Test Suite")
    print("=" * 50)
    
    tester = APIGatewayTester(gateway_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()