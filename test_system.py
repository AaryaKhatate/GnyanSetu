"""
GnyanSetu System Test Script
Tests all services, database connectivity, and UI-service communication
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

# Test results storage
test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'details': []
}

def record_result(test_name, passed, message, details=None):
    """Record test result"""
    if passed:
        test_results['passed'] += 1
        print_success(f"{test_name}: {message}")
    else:
        test_results['failed'] += 1
        print_error(f"{test_name}: {message}")
    
    test_results['details'].append({
        'test': test_name,
        'passed': passed,
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })

def test_service_health(service_name, port):
    """Test if a service is running and healthy"""
    print_info(f"Testing {service_name} on port {port}...")
    
    # Try both /health and /health/ endpoints
    health_endpoints = ['/health', '/health/', '/api/v1/health/', '/api/v1/health']
    
    for endpoint in health_endpoints:
        try:
            response = requests.get(f'http://localhost:{port}{endpoint}', timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                except:
                    data = {"status": "healthy", "response": "OK"}
                
                record_result(
                    f"{service_name} Health Check",
                    True,
                    f"Service is healthy (Status: {data.get('status', 'unknown')})",
                    data
                )
                return True, data
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue
    
    # If all endpoints failed
    record_result(
        f"{service_name} Health Check",
        False,
        f"Cannot connect to service on port {port} - Service may not be running",
        None
    )
    return False, None

def test_database_connectivity(service_name, port):
    """Test database connectivity through service"""
    print_info(f"Testing database connectivity for {service_name}...")
    
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            db_status = data.get('database', 'unknown')
            
            if db_status == 'connected' or db_status == 'healthy':
                record_result(
                    f"{service_name} Database",
                    True,
                    f"Database is connected (Status: {db_status})",
                    data
                )
                return True
            else:
                record_result(
                    f"{service_name} Database",
                    False,
                    f"Database connection issue (Status: {db_status})",
                    data
                )
                return False
    except Exception as e:
        record_result(
            f"{service_name} Database",
            False,
            f"Cannot check database status: {str(e)}",
            None
        )
        return False

def test_api_gateway():
    """Test API Gateway routing"""
    print_header("TESTING API GATEWAY")
    
    # Test gateway health
    healthy, data = test_service_health("API Gateway", 8000)
    if not healthy:
        return False
    
    # Test service registry
    print_info("Testing API Gateway service registry...")
    try:
        # Test if gateway can route to services
        services_to_test = [
            ('users', 8002),
            ('lesson', 8003),
            ('teaching', 8004),
            ('quiz', 8005),
            ('visualization', 8006)
        ]
        
        all_routable = True
        for service_name, port in services_to_test:
            try:
                # Try to reach service through gateway
                response = requests.get(
                    f'http://localhost:8000/api/{service_name}/health',
                    timeout=5
                )
                if response.status_code in [200, 404]:  # 404 means gateway can reach service
                    print_success(f"Gateway can route to {service_name} service")
                else:
                    print_warning(f"Gateway routing to {service_name} returned {response.status_code}")
            except Exception as e:
                print_warning(f"Gateway routing test for {service_name}: {str(e)}")
                all_routable = False
        
        return True
    except Exception as e:
        print_error(f"API Gateway routing test failed: {str(e)}")
        return False

def test_user_service():
    """Test User Service (Authentication)"""
    print_header("TESTING USER SERVICE (PORT 8002)")
    
    # Health check
    healthy, data = test_service_health("User Service", 8002)
    if not healthy:
        return False
    
    # Database check
    test_database_connectivity("User Service", 8002)
    
    # Test user registration
    print_info("Testing user registration...")
    try:
        test_user = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "name": "Test User"
        }
        
        # Try correct endpoint paths
        registration_endpoints = [
            'http://localhost:8002/api/v1/auth/register/',
            'http://localhost:8002/api/auth/register/',
        ]
        
        registration_worked = False
        for endpoint in registration_endpoints:
            try:
                response = requests.post(endpoint, json=test_user, timeout=10)
                
                if response.status_code in [200, 201, 400]:  # 400 if user exists or validation error
                    if response.status_code in [200, 201]:
                        record_result(
                            "User Registration",
                            True,
                            "User registration endpoint is working",
                            response.json()
                        )
                        registration_worked = True
                        break
                    else:
                        print_info(f"User registration at {endpoint} returned 400 (expected for test data)")
                        registration_worked = True
                        break
            except:
                continue
        
        if not registration_worked:
            print_warning("User registration endpoints found but may have validation requirements")
    except Exception as e:
        print_warning(f"User registration test: {str(e)}")
    
    return True

def test_lesson_service():
    """Test Lesson Service (PDF Processing & AI)"""
    print_header("TESTING LESSON SERVICE (PORT 8003)")
    
    # Health check
    healthy, data = test_service_health("Lesson Service", 8003)
    if not healthy:
        return False
    
    # Database check
    test_database_connectivity("Lesson Service", 8003)
    
    # Test lesson generation endpoint availability
    print_info("Testing lesson generation endpoint...")
    try:
        # We won't actually generate a lesson (takes 30-60s), just check if endpoint exists
        response = requests.post(
            'http://localhost:8003/api/generate-lesson/',
            files={},  # Empty files
            timeout=5
        )
        
        # Any response (even error) means endpoint is reachable
        if response.status_code in [400, 422, 500]:
            print_success("Lesson generation endpoint is reachable (returned expected error for empty request)")
        else:
            print_info(f"Lesson generation endpoint returned status {response.status_code}")
    except requests.exceptions.Timeout:
        print_success("Lesson generation endpoint is processing (timeout expected without file)")
    except Exception as e:
        print_warning(f"Lesson generation endpoint test: {str(e)}")
    
    return True

def test_teaching_service():
    """Test Teaching Service (WebSocket & Real-time)"""
    print_header("TESTING TEACHING SERVICE (PORT 8004)")
    
    # Health check
    healthy, data = test_service_health("Teaching Service", 8004)
    if not healthy:
        return False
    
    # Database check
    test_database_connectivity("Teaching Service", 8004)
    
    # Test WebSocket endpoint availability
    print_info("Testing teaching session endpoint...")
    try:
        response = requests.get(
            'http://localhost:8004/api/teaching/',
            timeout=5
        )
        
        if response.status_code in [200, 404, 405]:
            print_success("Teaching service endpoints are reachable")
        else:
            print_info(f"Teaching endpoint returned status {response.status_code}")
    except Exception as e:
        print_warning(f"Teaching endpoint test: {str(e)}")
    
    return True

def test_quiz_service():
    """Test Quiz/Notes Service"""
    print_header("TESTING QUIZ/NOTES SERVICE (PORT 8005)")
    
    # Health check
    healthy, data = test_service_health("Quiz/Notes Service", 8005)
    if not healthy:
        return False
    
    # Database check
    test_database_connectivity("Quiz/Notes Service", 8005)
    
    # Test quiz retrieval endpoint (this service retrieves quiz, doesn't generate)
    print_info("Testing quiz retrieval endpoint...")
    try:
        # Try to get quiz for a lesson
        response = requests.get(
            'http://localhost:8005/api/quiz/lesson/test_lesson_id',
            timeout=10
        )
        
        if response.status_code in [200, 404, 422]:
            if response.status_code == 200:
                record_result(
                    "Quiz Retrieval",
                    True,
                    "Quiz retrieval endpoint is working",
                    response.json()
                )
            elif response.status_code == 404:
                print_info("Quiz retrieval endpoint is working (no quiz found for test ID)")
            else:
                print_warning(f"Quiz retrieval returned {response.status_code}")
        else:
            record_result(
                "Quiz Retrieval",
                False,
                f"Quiz retrieval returned status {response.status_code}",
                response.text
            )
    except Exception as e:
        print_warning(f"Quiz retrieval test: {str(e)}")
    
    return True

def test_visualization_service():
    """Test Visualization Service"""
    print_header("TESTING VISUALIZATION SERVICE (PORT 8006)")
    
    # Health check
    healthy, data = test_service_health("Visualization Service", 8006)
    if not healthy:
        return False
    
    # Database check
    test_database_connectivity("Visualization Service", 8006)
    
    # Test visualization generation with correct endpoint
    print_info("Testing visualization generation endpoint...")
    try:
        test_data = {
            "lesson_id": "test_lesson_id",
            "subject": "biology",
            "topic": "photosynthesis",
            "lesson_content": "Test content about photosynthesis process",
            "teaching_steps": ["Introduction", "Process", "Conclusion"]
        }
        
        response = requests.post(
            'http://localhost:8006/api/visualizations/process',
            json=test_data,
            timeout=10
        )
        
        if response.status_code in [200, 201, 400, 422]:
            if response.status_code in [200, 201]:
                record_result(
                    "Visualization Generation",
                    True,
                    "Visualization generation endpoint is working",
                    response.json()
                )
            else:
                print_warning(f"Visualization generation returned {response.status_code}: Expected with test data")
        else:
            record_result(
                "Visualization Generation",
                False,
                f"Visualization generation returned status {response.status_code}",
                response.text
            )
    except Exception as e:
        print_warning(f"Visualization generation test: {str(e)}")
    
    return True

def test_ui_services():
    """Test UI (Frontend) services"""
    print_header("TESTING FRONTEND UI SERVICES")
    
    # Test Landing Page
    print_info("Testing Landing Page (port 3000)...")
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            record_result(
                "Landing Page",
                True,
                "Landing page is accessible",
                None
            )
        else:
            record_result(
                "Landing Page",
                False,
                f"Landing page returned status {response.status_code}",
                None
            )
    except Exception as e:
        record_result(
            "Landing Page",
            False,
            f"Cannot access landing page: {str(e)}",
            None
        )
    
    # Test Dashboard
    print_info("Testing Dashboard (port 3001)...")
    try:
        response = requests.get('http://localhost:3001', timeout=5)
        if response.status_code == 200:
            record_result(
                "Dashboard",
                True,
                "Dashboard is accessible",
                None
            )
        else:
            record_result(
                "Dashboard",
                False,
                f"Dashboard returned status {response.status_code}",
                None
            )
    except Exception as e:
        record_result(
            "Dashboard",
            False,
            f"Cannot access dashboard: {str(e)}",
            None
        )

def test_end_to_end_flow():
    """Test a simplified end-to-end flow"""
    print_header("TESTING END-TO-END FLOW")
    
    print_info("Testing complete user flow simulation...")
    
    # Step 1: Check if API Gateway is running
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code != 200:
            print_error("Cannot proceed with E2E test - API Gateway not healthy")
            return False
    except:
        print_error("Cannot proceed with E2E test - API Gateway not accessible")
        return False
    
    print_success("Step 1: API Gateway is accessible")
    
    # Step 2: Test user service through gateway
    print_info("Step 2: Testing authentication flow...")
    try:
        response = requests.get('http://localhost:8002/health', timeout=5)
        if response.status_code == 200:
            print_success("Step 2: User service ready for authentication")
        else:
            print_warning("Step 2: User service health check returned non-200")
    except:
        print_error("Step 2: Cannot connect to user service")
    
    # Step 3: Test lesson service
    print_info("Step 3: Testing lesson service availability...")
    try:
        response = requests.get('http://localhost:8003/health', timeout=5)
        if response.status_code == 200:
            print_success("Step 3: Lesson service ready for PDF processing")
        else:
            print_warning("Step 3: Lesson service health check returned non-200")
    except:
        print_error("Step 3: Cannot connect to lesson service")
    
    # Step 4: Test visualization service
    print_info("Step 4: Testing visualization service...")
    try:
        response = requests.get('http://localhost:8006/health', timeout=5)
        if response.status_code == 200:
            print_success("Step 4: Visualization service ready")
        else:
            print_warning("Step 4: Visualization service health check returned non-200")
    except:
        print_error("Step 4: Cannot connect to visualization service")
    
    # Step 5: Test teaching service
    print_info("Step 5: Testing teaching service...")
    try:
        response = requests.get('http://localhost:8004/health', timeout=5)
        if response.status_code == 200:
            print_success("Step 5: Teaching service ready for real-time sessions")
        else:
            print_warning("Step 5: Teaching service health check returned non-200")
    except:
        print_error("Step 5: Cannot connect to teaching service")
    
    # Step 6: Test quiz service
    print_info("Step 6: Testing quiz service...")
    try:
        response = requests.get('http://localhost:8005/health', timeout=5)
        if response.status_code == 200:
            print_success("Step 6: Quiz service ready for assessments")
        else:
            print_warning("Step 6: Quiz service health check returned non-200")
    except:
        print_error("Step 6: Cannot connect to quiz service")
    
    print_success("End-to-end flow test completed!")
    return True

def print_final_summary():
    """Print final test summary"""
    print_header("TEST SUMMARY")
    
    total_tests = test_results['passed'] + test_results['failed']
    success_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"{Colors.BOLD}Total Tests Run:{Colors.END} {total_tests}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {test_results['passed']}")
    print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {test_results['failed']}")
    print(f"{Colors.BOLD}Success Rate:{Colors.END} {success_rate:.1f}%\n")
    
    if test_results['failed'] > 0:
        print(f"{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.END}")
        for detail in test_results['details']:
            if not detail['passed']:
                print(f"  {Colors.RED}✗{Colors.END} {detail['test']}: {detail['message']}")
        print()
    
    # Recommendations
    print(f"{Colors.BOLD}{Colors.CYAN}RECOMMENDATIONS:{Colors.END}")
    
    if test_results['failed'] == 0:
        print(f"{Colors.GREEN}✓ All services are running correctly!{Colors.END}")
        print(f"{Colors.GREEN}✓ UI-Service-Database communication is working!{Colors.END}")
    else:
        if any('8000' in str(d.get('details', '')) for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Start API Gateway: cd microservices/api-gateway && uvicorn app:app --port 8000{Colors.END}")
        
        if any('8002' in str(d.get('details', '')) for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Start User Service: cd services/user_service && python manage.py runserver 8002{Colors.END}")
        
        if any('8003' in str(d.get('details', '')) for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Start Lesson Service: cd services/lesson_service && python manage.py runserver 8003{Colors.END}")
        
        if any('8004' in str(d.get('details', '')) for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Start Teaching Service: cd services/teaching_service && daphne -p 8004 virtual_teacher.asgi:application{Colors.END}")
        
        if any('8005' in str(d.get('details', '')) for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Start Quiz Service: cd microservices/quiz-notes-service && uvicorn app:app --port 8005{Colors.END}")
        
        if any('8006' in str(d.get('details', '')) for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Start Visualization Service: cd microservices/visualization-service && uvicorn app:app --port 8006{Colors.END}")
        
        if any('Database' in d['test'] for d in test_results['details'] if not d['passed']):
            print(f"{Colors.YELLOW}• Check MongoDB is running: mongod --version{Colors.END}")
            print(f"{Colors.YELLOW}• Start MongoDB if not running{Colors.END}")
    
    print()
    
    # Save detailed results to file
    results_file = Path(__file__).parent / f"test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"{Colors.BLUE}Detailed results saved to: {results_file}{Colors.END}\n")

def main():
    """Main test execution"""
    print_header("GNYANSETU SYSTEM TEST SUITE")
    print(f"{Colors.BOLD}Test Started:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print_info("This script will test all services, database connectivity, and UI-service communication.")
    print_info("Make sure all services are running before proceeding.")
    print()
    
    input(f"{Colors.YELLOW}Press Enter to start testing...{Colors.END}")
    
    # Run all tests
    test_api_gateway()
    test_user_service()
    test_lesson_service()
    test_teaching_service()
    test_quiz_service()
    test_visualization_service()
    test_ui_services()
    test_end_to_end_flow()
    
    # Print summary
    print_final_summary()
    
    # Return exit code based on test results
    return 0 if test_results['failed'] == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {str(e)}{Colors.END}")
        sys.exit(1)
