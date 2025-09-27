#!/usr/bin/env python3
"""
Test script to upload PDF to Lesson Service
"""
import requests
import json

def test_pdf_upload():
    """Test PDF upload to lesson service"""
    
    # Create a simple test file
    test_content = """
    This is a test PDF content for lesson generation.
    
    Topic: Introduction to Python Programming
    
    Python is a high-level, interpreted programming language with dynamic semantics.
    Its high-level built-in data structures, combined with dynamic typing and dynamic binding,
    make it very attractive for Rapid Application Development.
    
    Key Features:
    1. Easy to learn and use
    2. Expressive syntax
    3. Large standard library
    4. Cross-platform compatibility
    
    Python is widely used in:
    - Web development
    - Data science and analytics
    - Artificial intelligence and machine learning
    - Automation and scripting
    """
    
    # Save as text file (we'll use this to simulate PDF content)
    with open('test_lesson.txt', 'w') as f:
        f.write(test_content)
    
    # Test the endpoint
    url = "http://localhost:8003/api/generate-lesson/"
    
    # Prepare form data with actual PDF
    pdf_path = r"E:\Project\venv\Lib\site-packages\matplotlib\mpl-data\images\back.pdf"
    files = {
        'pdf_file': ('back.pdf', open(pdf_path, 'rb'), 'application/pdf')
    }
    
    data = {
        'user_id': 'test_user_123',
        'lesson_type': 'interactive'
    }
    
    try:
        print("🚀 Testing PDF upload to Lesson Service...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        response = requests.post(url, files=files, data=data)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"📝 Lesson ID: {result.get('lesson_id')}")
            print(f"📄 PDF ID: {result.get('pdf_id')}")
            print(f"🎓 Lesson Title: {result.get('lesson', {}).get('title')}")
            print(f"📊 PDF Stats: {result.get('pdf_stats')}")
            
            print(f"\n📚 Lesson Content Preview:")
            content = result.get('lesson', {}).get('content', '')[:200]
            print(f"{content}...")
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    finally:
        # Cleanup
        try:
            files['pdf_file'][1].close()
        except:
            pass

if __name__ == "__main__":
    test_pdf_upload()