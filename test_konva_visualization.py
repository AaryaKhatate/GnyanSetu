"""
Test Konva.js Visualization Implementation
==========================================
Tests the complete flow:
1. Upload PDF
2. Extract images with explanations
3. Generate lesson
4. Generate Konva.js visualization (v2)
5. Verify whiteboard commands

Run this after starting all services:
- Lesson Service: localhost:8003
- Visualization Service: localhost:8006
"""

import requests
import json
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Service URLs
LESSON_SERVICE_URL = "http://localhost:8003"
VISUALIZATION_SERVICE_URL = "http://localhost:8006"

def create_test_pdf():
    """Create a sample PDF for testing"""
    print("📝 Creating test PDF...")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    story.append(Paragraph("Photosynthesis: How Plants Make Food", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Content
    content = [
        "Photosynthesis is the process by which green plants use sunlight to make their own food.",
        "",
        "The Three Key Ingredients:",
        "1. Sunlight - Energy from the sun",
        "2. Water - Absorbed through roots from soil",
        "3. Carbon Dioxide (CO₂) - Taken from air through leaf pores",
        "",
        "The Chemical Equation:",
        "6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂",
        "",
        "This means: Six molecules of carbon dioxide plus six molecules of water, using light energy, produce one molecule of glucose (sugar) and six molecules of oxygen.",
        "",
        "Where It Happens:",
        "Photosynthesis occurs in chloroplasts, tiny structures inside plant cells. Chloroplasts contain chlorophyll, the green pigment that captures sunlight.",
        "",
        "Why It Matters:",
        "- Plants produce oxygen that we breathe",
        "- Plants create food (glucose) for themselves and other organisms",
        "- It's the foundation of most food chains on Earth"
    ]
    
    for line in content:
        if line:
            story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    
    print("✅ Test PDF created")
    return buffer

def test_pdf_upload_and_lesson():
    """Test PDF upload and lesson generation"""
    print("\n" + "="*60)
    print("TEST 1: PDF Upload & Lesson Generation")
    print("="*60)
    
    pdf_buffer = create_test_pdf()
    
    # Upload PDF
    files = {'pdf_file': ('test_photosynthesis.pdf', pdf_buffer, 'application/pdf')}
    data = {
        'user_id': 'test_user_123',
        'lesson_type': 'interactive'
    }
    
    print("📤 Uploading PDF to lesson service...")
    response = requests.post(
        f"{LESSON_SERVICE_URL}/upload_pdf/",
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Lesson generated successfully!")
        print(f"   Lesson ID: {result.get('lesson_id')}")
        print(f"   Title: {result.get('lesson_title', 'N/A')}")
        print(f"   Content length: {len(result.get('lesson_content', ''))} chars")
        print(f"   Images extracted: {len(result.get('pdf_images', []))}")
        
        # Check if images have explanations
        if result.get('pdf_images'):
            print("\n   📷 Image Analysis:")
            for idx, img in enumerate(result['pdf_images']):
                print(f"      Image {idx+1}:")
                print(f"        - ID: {img.get('id', 'N/A')}")
                print(f"        - Description: {img.get('description', 'N/A')[:60]}...")
                print(f"        - Has narration: {'Yes' if img.get('narration') else 'No'}")
        
        return result.get('lesson_id')
    else:
        print(f"❌ Failed to upload PDF: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_visualization_v2(lesson_id):
    """Test new Konva.js visualization generation"""
    print("\n" + "="*60)
    print("TEST 2: Konva.js Visualization Generation (v2)")
    print("="*60)
    
    if not lesson_id:
        print("❌ No lesson ID provided, skipping test")
        return
    
    print(f"🎨 Requesting v2 visualization for lesson: {lesson_id}")
    
    response = requests.get(
        f"{VISUALIZATION_SERVICE_URL}/visualization/v2/{lesson_id}"
    )
    
    if response.status_code == 200:
        viz_data = response.json()
        print("✅ Visualization generated successfully!")
        
        # Analyze teaching sequence
        teaching_sequence = viz_data.get('teaching_sequence', [])
        print(f"\n   📚 Teaching Sequence:")
        print(f"      Total steps: {len(teaching_sequence)}")
        
        for idx, step in enumerate(teaching_sequence):
            print(f"\n      Step {idx + 1}: {step.get('type')}")
            print(f"         Text: {step.get('text_explanation', '')[:60]}...")
            print(f"         TTS: {step.get('tts_text', '')[:60]}...")
            print(f"         Commands: {len(step.get('whiteboard_commands', []))}")
            
            # Show first few commands
            commands = step.get('whiteboard_commands', [])
            if commands:
                print(f"         Command types:")
                for cmd in commands[:5]:  # Show first 5
                    print(f"            - {cmd.get('action')}")
                if len(commands) > 5:
                    print(f"            ... and {len(commands) - 5} more")
        
        # Check images
        images = viz_data.get('images', [])
        if images:
            print(f"\n   🖼️ Images: {len(images)}")
            for img in images:
                print(f"      - {img.get('id')}: {img.get('explanation', 'N/A')[:50]}...")
        
        print("\n   ✅ Visualization structure validated!")
        return viz_data
    else:
        print(f"❌ Failed to generate visualization: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_whiteboard_commands_validity(viz_data):
    """Validate whiteboard commands structure"""
    print("\n" + "="*60)
    print("TEST 3: Whiteboard Commands Validation")
    print("="*60)
    
    if not viz_data:
        print("❌ No visualization data provided")
        return
    
    valid_actions = [
        "clear_all", "write_text", "draw_text_box", "draw_circle",
        "draw_rectangle", "draw_line", "draw_arrow", "draw_image",
        "highlight_object", "draw_equation", "draw_path"
    ]
    
    issues = []
    
    for step_idx, step in enumerate(viz_data.get('teaching_sequence', [])):
        commands = step.get('whiteboard_commands', [])
        
        for cmd_idx, cmd in enumerate(commands):
            action = cmd.get('action')
            
            # Check valid action
            if action not in valid_actions:
                issues.append(f"Step {step_idx+1}, Command {cmd_idx+1}: Invalid action '{action}'")
            
            # Check required fields based on action
            if action == "write_text":
                if not all(k in cmd for k in ['text', 'x_percent', 'y_percent']):
                    issues.append(f"Step {step_idx+1}, Command {cmd_idx+1}: write_text missing required fields")
            
            elif action == "draw_text_box":
                if not all(k in cmd for k in ['text', 'x_percent', 'y_percent', 'width_percent']):
                    issues.append(f"Step {step_idx+1}, Command {cmd_idx+1}: draw_text_box missing required fields")
            
            elif action == "draw_circle":
                if not all(k in cmd for k in ['x_percent', 'y_percent', 'radius']):
                    issues.append(f"Step {step_idx+1}, Command {cmd_idx+1}: draw_circle missing required fields")
            
            elif action == "draw_arrow":
                if not all(k in cmd for k in ['from_percent', 'to_percent']):
                    issues.append(f"Step {step_idx+1}, Command {cmd_idx+1}: draw_arrow missing required fields")
    
    if issues:
        print("❌ Validation issues found:")
        for issue in issues[:10]:  # Show first 10
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
    else:
        print("✅ All whiteboard commands are valid!")
        print(f"   Validated {sum(len(s.get('whiteboard_commands', [])) for s in viz_data.get('teaching_sequence', []))} commands")

def test_service_health():
    """Test if services are running"""
    print("\n" + "="*60)
    print("PRE-TEST: Service Health Check")
    print("="*60)
    
    services = [
        ("Lesson Service", f"{LESSON_SERVICE_URL}/health"),
        ("Visualization Service", f"{VISUALIZATION_SERVICE_URL}/health")
    ]
    
    all_healthy = True
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"⚠️  {name}: Unhealthy (Status: {response.status_code})")
                all_healthy = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Not running (Connection refused)")
            all_healthy = False
        except Exception as e:
            print(f"❌ {name}: Error ({str(e)})")
            all_healthy = False
    
    if not all_healthy:
        print("\n⚠️  Some services are not running. Please start all services first.")
        print("   Start lesson service: python manage.py runserver 8003")
        print("   Start visualization service: python app.py (in visualization-service)")
        return False
    
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("Konva.js Visualization Implementation Test Suite")
    print("="*60)
    
    # Check services
    if not test_service_health():
        print("\n❌ Tests aborted - services not available")
        return
    
    # Test 1: PDF Upload & Lesson Generation
    lesson_id = test_pdf_upload_and_lesson()
    
    if not lesson_id:
        print("\n❌ Tests aborted - lesson generation failed")
        return
    
    # Wait for async processing
    print("\n⏳ Waiting 5 seconds for lesson processing...")
    time.sleep(5)
    
    # Test 2: Visualization Generation
    viz_data = test_visualization_v2(lesson_id)
    
    # Test 3: Validate Commands
    test_whiteboard_commands_validity(viz_data)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Lesson ID: {lesson_id}")
    if viz_data:
        print(f"Teaching Steps: {len(viz_data.get('teaching_sequence', []))}")
        print(f"Total Commands: {sum(len(s.get('whiteboard_commands', [])) for s in viz_data.get('teaching_sequence', []))}")
        print(f"Images: {len(viz_data.get('images', []))}")
        print("\n✅ All tests completed successfully!")
        print("\n📖 Next Steps:")
        print(f"   1. Frontend: Navigate to TeachingSession component with lessonId='{lesson_id}'")
        print(f"   2. API Test: GET {VISUALIZATION_SERVICE_URL}/visualization/v2/{lesson_id}")
    else:
        print("\n⚠️  Some tests failed - check logs above")

if __name__ == "__main__":
    main()
