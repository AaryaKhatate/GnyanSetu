"""
Test Teaching System - End-to-End Verification
Tests the complete flow from API to frontend
"""

import requests
import json
import sys

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_visualization_api(lesson_id):
    """Test visualization service API"""
    print_section("Testing Visualization API")
    
    url = f"http://localhost:8006/visualization/v2/{lesson_id}"
    print(f"📡 Calling: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received")
            print(f"   - Teaching sequence steps: {len(data.get('teaching_sequence', []))}")
            print(f"   - Images: {len(data.get('images', []))}")
            print(f"   - Has notes: {bool(data.get('notes_content'))}")
            print(f"   - Has quiz: {bool(data.get('quiz'))}")
            
            # Show first step details
            if data.get('teaching_sequence'):
                first_step = data['teaching_sequence'][0]
                print(f"\n📝 First Step Preview:")
                print(f"   - Type: {first_step.get('type')}")
                print(f"   - TTS Text: {first_step.get('tts_text', '')[:60]}...")
                print(f"   - Whiteboard Commands: {len(first_step.get('whiteboard_commands', []))}")
                
                # Show command types
                if first_step.get('whiteboard_commands'):
                    actions = [cmd.get('action') for cmd in first_step['whiteboard_commands']]
                    print(f"   - Command Actions: {', '.join(set(actions))}")
            
            return True, data
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to visualization service")
        print("   Make sure service is running on port 8006")
        return False, None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def test_frontend_components():
    """Test if frontend components exist"""
    print_section("Testing Frontend Components")
    
    import os
    base_path = "E:/Project/GnyanSetu/virtual_teacher_project/UI/Dashboard/Dashboard/src"
    
    components = [
        ("App.jsx", "App.jsx"),
        ("TeachingSessionSimple.jsx", "components/TeachingSessionSimple.jsx"),
        ("TeachingSession.css", "components/TeachingSession.css"),
        ("TeachingCanvas.jsx", "components/TeachingCanvas.jsx"),
        ("ttsController.js", "utils/ttsController.js"),
    ]
    
    all_exist = True
    for name, path in components:
        full_path = os.path.join(base_path, path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✅ {name} exists ({size} bytes)")
        else:
            print(f"❌ {name} NOT FOUND at {full_path}")
            all_exist = False
    
    return all_exist

def test_routing_config():
    """Test if routing is properly configured"""
    print_section("Testing React Router Configuration")
    
    app_jsx_path = "E:/Project/GnyanSetu/virtual_teacher_project/UI/Dashboard/Dashboard/src/App.jsx"
    
    try:
        with open(app_jsx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("BrowserRouter import", "BrowserRouter" in content),
            ("Routes component", "<Routes>" in content),
            ("/teaching route", 'path="/teaching"' in content),
            ("/teaching/:lessonId route", 'path="/teaching/:lessonId"' in content),
            ("TeachingSessionSimple import", "TeachingSessionSimple" in content),
        ]
        
        all_passed = True
        for check_name, result in checks:
            if result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error reading App.jsx: {str(e)}")
        return False

def test_whiteboard_button():
    """Test if Whiteboard has teaching button"""
    print_section("Testing Whiteboard Teaching Button")
    
    whiteboard_path = "E:/Project/GnyanSetu/virtual_teacher_project/UI/Dashboard/Dashboard/src/components/Whiteboard.jsx"
    
    try:
        with open(whiteboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("Teaching button exists", "Start Interactive Teaching" in content),
            ("Button navigates to /teaching", "window.location.href = '/teaching'" in content or "navigate('/teaching')" in content),
            ("Button shows when ready", "teachingSteps.length > 0" in content),
        ]
        
        all_passed = True
        for check_name, result in checks:
            if result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error reading Whiteboard.jsx: {str(e)}")
        return False

def test_dependencies():
    """Test if required npm packages are installed"""
    print_section("Testing NPM Dependencies")
    
    import subprocess
    import os
    
    dashboard_path = "E:/Project/GnyanSetu/virtual_teacher_project/UI/Dashboard/Dashboard"
    os.chdir(dashboard_path)
    
    packages = ["react-router-dom", "axios", "use-image"]
    
    all_installed = True
    for package in packages:
        try:
            result = subprocess.run(
                ["npm", "list", package],
                capture_output=True,
                text=True,
                shell=True
            )
            if package in result.stdout:
                print(f"✅ {package} installed")
            else:
                print(f"❌ {package} NOT installed")
                all_installed = False
        except Exception as e:
            print(f"⚠️  Could not check {package}: {str(e)}")
    
    return all_installed

def main():
    print("\n" + "="*60)
    print("  🧪 GnyanSetu Teaching System Test Suite")
    print("="*60)
    
    # Test with a known lesson ID (from your terminal history)
    lesson_id = "68fcdc37c28f3607dee67d06"
    
    print(f"\n📌 Testing with Lesson ID: {lesson_id}")
    
    results = {}
    
    # Run all tests
    results['api'] = test_visualization_api(lesson_id)[0]
    results['components'] = test_frontend_components()
    results['routing'] = test_routing_config()
    results['button'] = test_whiteboard_button()
    results['dependencies'] = test_dependencies()
    
    # Final summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name.upper()}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        print("\n📝 Next Steps:")
        print("   1. Go to http://localhost:3001")
        print("   2. Upload a PDF")
        print("   3. Click '🎓 Start Interactive Teaching' button")
        print("   4. Test TTS and whiteboard rendering")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
