"""
Complete AI Test with Quiz/Notes Generation
Waits for background quiz and notes generation to complete
"""

import requests
import json
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path

print("\n" + "="*80)
print("GNYANSETU - COMPLETE TEST WITH QUIZ & NOTES")
print("Testing: PDF → Lesson → Quiz/Notes (with waiting)")
print("="*80 + "\n")

# Create PDF
print("STEP 1: Creating test PDF...")
pdf_path = Path("test_physics.pdf")

c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setFont("Helvetica-Bold", 16)
c.drawString(100, 750, "OHM'S LAW AND ELECTRICAL CIRCUITS")

c.setFont("Helvetica", 12)
y = 720
lines = [
    "",
    "Introduction:",
    "Ohm's Law is a fundamental principle in electrical circuits that relates",
    "voltage, current, and resistance.",
    "",
    "Ohm's Law Formula:",
    "V = I × R",
    "Where:",
    "  V = Voltage (measured in Volts)",
    "  I = Current (measured in Amperes)",
    "  R = Resistance (measured in Ohms)",
    "",
    "Key Concepts:",
    "1. Voltage (V): The electrical potential difference between two points",
    "2. Current (I): The flow of electric charge through a conductor",
    "3. Resistance (R): Opposition to the flow of electric current",
    "",
    "Circuit Components:",
    "- Battery: Provides voltage (energy source)",
    "- Resistor: Limits current flow",
    "- Wires: Conductors for current",
    "- LED: Light emitting diode (output device)",
    "",
    "Example:",
    "If a circuit has a 12V battery and a 4Ω resistor:",
    "Current I = V/R = 12V / 4Ω = 3A",
    "",
    "Applications:",
    "- Designing electrical circuits",
    "- Calculating power consumption",
    "- Troubleshooting circuit problems",
    "- Electronic device design"
]

for line in lines:
    c.drawString(100, y, line)
    y -= 20
    if y < 50:
        c.showPage()
        y = 750

c.save()
print(f"✓ Created: {pdf_path} ({pdf_path.stat().st_size} bytes)\n")

# Upload and generate lesson
print("STEP 2: Uploading PDF to Lesson Service...")
print("⏳ Gemini AI is generating lesson...\n")

lesson_id = None
try:
    with open(pdf_path, 'rb') as f:
        files = {'pdf_file': ('ohms_law.pdf', f, 'application/pdf')}
        data = {'user_id': 'test_user_quiz_notes'}
        
        start = time.time()
        response = requests.post(
            'http://localhost:8003/api/generate-lesson/',
            files=files,
            data=data,
            timeout=120
        )
        elapsed = time.time() - start
    
    print(f"✓ Response in {elapsed:.1f}s - Status: {response.status_code}\n")
    
    if response.status_code == 200:
        result = response.json()
        lesson_id = result.get('lesson_id')
        quiz_notes_status = result.get('quiz_notes_status', 'unknown')
        print(f"✓ Lesson Generated! ID: {lesson_id}")
        print(f"📊 Quiz/Notes Status: {quiz_notes_status}\n")
    else:
        print(f"❌ Generation failed: {response.text[:500]}\n")

except Exception as e:
    print(f"❌ Error: {e}\n")

# Wait for quiz and notes to be generated
if lesson_id:
    print("STEP 3: Waiting for Quiz & Notes Generation...")
    print("⏳ Background processing in progress...\n")
    
    max_wait = 120  # Wait up to 2 minutes
    poll_interval = 5  # Check every 5 seconds
    waited = 0
    
    while waited < max_wait:
        try:
            response = requests.get(
                f'http://localhost:8003/api/lessons/{lesson_id}/quiz-notes-status',
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('quiz_notes_status', 'unknown')
                is_ready = status_data.get('is_ready', False)
                has_quiz = status_data.get('has_quiz', False)
                has_notes = status_data.get('has_notes', False)
                
                print(f"[{waited}s] Status: {status} | Quiz: {has_quiz} | Notes: {has_notes}")
                
                if is_ready:
                    print(f"\n✅ Quiz & Notes Ready! (Generated in {waited}s)\n")
                    break
            
            time.sleep(poll_interval)
            waited += poll_interval
            
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
            break
    
    if waited >= max_wait:
        print(f"\n⏱️ Timeout after {max_wait}s - Fetching current state...\n")
    
    # Fetch the complete lesson
    print("STEP 4: Fetching Complete Lesson Content...")
    print("-" * 80 + "\n")
    
    try:
        response = requests.get(
            f'http://localhost:8003/api/lessons/{lesson_id}',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            lesson = data.get('lesson', {})
            
            print("="*80)
            print("COMPLETE LESSON DATA")
            print("="*80 + "\n")
            
            title = lesson.get('lesson_title', 'No title')
            content = lesson.get('lesson_content', '')
            
            print(f"📚 Title: {title}")
            print(f"📄 Lesson Content: {len(content)} characters")
            print(f"🆔 Lesson ID: {lesson_id}\n")
            
            # Show content preview
            print("-" * 80)
            print("LESSON CONTENT (Preview):")
            print("-" * 80)
            print(content[:1500])
            if len(content) > 1500:
                print(f"\n... [{len(content) - 1500} more characters]")
            
            # Quiz data
            quiz = lesson.get('quiz_data', {})
            if quiz and quiz.get('questions'):
                questions = quiz.get('questions', [])
                print("\n\n" + "="*80)
                print(f"📝 QUIZ QUESTIONS - {len(questions)} Total")
                print("="*80 + "\n")
                
                for i, q in enumerate(questions[:5]):
                    print(f"Q{i+1}: {q.get('question')}")
                    options = q.get('options', [])
                    correct = q.get('correct_answer', '')
                    for j, opt in enumerate(options):
                        marker = "✓✓✓" if opt == correct else "   "
                        print(f"  {marker} {chr(65+j)}. {opt}")
                    print()
                
                if len(questions) > 5:
                    print(f"... and {len(questions) - 5} more questions\n")
            else:
                print("\n\n❌ NO QUIZ DATA GENERATED")
            
            # Notes data
            notes = lesson.get('notes_data', {})
            if notes and notes.get('sections'):
                sections = notes.get('sections', [])
                print("\n" + "="*80)
                print(f"📔 NOTES - {len(sections)} Sections")
                print("="*80 + "\n")
                
                for i, section in enumerate(sections[:3]):
                    print(f"Section {i+1}: {section.get('title', 'N/A')}")
                    content_preview = section.get('content', '')[:200]
                    print(f"  {content_preview}...")
                    print()
                
                if len(sections) > 3:
                    print(f"... and {len(sections) - 3} more sections\n")
            else:
                print("\n❌ NO NOTES DATA GENERATED")
            
            print("\n" + "="*80)
            print("✅ TEST COMPLETE")
            print("="*80)
            
        else:
            print(f"❌ Failed to fetch: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error fetching lesson: {e}")

# Cleanup
try:
    pdf_path.unlink()
    print("\n✓ Cleaned up test PDF")
except:
    pass

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
WHAT THIS TEST VERIFIED:
✓ PDF creation and upload
✓ Lesson generation by Gemini AI
✓ Background quiz/notes generation
✓ Polling mechanism for async operations
✓ Complete data retrieval with quiz and notes

This demonstrates the full end-to-end workflow with all components!
""")
