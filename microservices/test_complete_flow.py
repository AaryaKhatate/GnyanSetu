#!/usr/bin/env python3
"""
Complete Authentication + PDF Upload Flow Test
Tests the entire user journey from login to PDF upload
"""

import requests
import json
import os
import time

def create_test_pdf():
    """Create a simple test PDF file."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        filename = "test_document.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 750, "GnyanSetu Test Document")
        c.drawString(100, 700, "This is a test PDF file for the microservices architecture.")
        c.drawString(100, 650, "It contains some sample text to test PDF processing capabilities.")
        c.drawString(100, 600, "The PDF service should extract this text and store it in MongoDB.")
        c.drawString(100, 550, "Document ID should be generated for lesson service integration.")
        c.drawString(100, 500, "This text will be used to generate AI-powered lessons and quizzes.")
        c.showPage()
        c.save()
        return filename
    except ImportError:
        print("⚠️  reportlab not installed. Please install: pip install reportlab")
        print("Using existing PDF file if available...")
        return None

def test_user_auth():
    """Test user authentication."""
    print("🔐 Testing User Authentication...")
    
    # Test signup
    signup_data = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "TestPassword123",
        "confirm_password": "TestPassword123"
    }
    
    try:
        response = requests.post("http://localhost:8002/api/auth/signup/", 
                               json=signup_data, timeout=10)
        if response.status_code == 201:
            print("✅ User signup successful!")
            data = response.json()
            return data.get('token')
        elif response.status_code == 409:
            print("ℹ️  User already exists, trying login...")
        else:
            print(f"❌ Signup failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signup error: {e}")
    
    # Test login
    login_data = {
        "email": "testuser@example.com",
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post("http://localhost:8002/api/auth/login/", 
                               json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ User login successful!")
            data = response.json()
            return data.get('token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_pdf_upload(auth_token):
    """Test PDF upload functionality."""
    print("\n📄 Testing PDF Upload...")
    
    # Create or use test PDF
    pdf_file = create_test_pdf()
    if not pdf_file:
        # Look for any PDF in current directory
        for file in os.listdir('.'):
            if file.endswith('.pdf'):
                pdf_file = file
                break
    
    if not pdf_file or not os.path.exists(pdf_file):
        print("❌ No PDF file available for testing")
        return None
    
    print(f"📄 Using PDF file: {pdf_file}")
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'pdf_file': f}
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            print("🚀 Uploading PDF to service...")
            response = requests.post("http://localhost:8001/api/upload", 
                                   files=files, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ PDF upload successful!")
                print(f"   📄 Document ID: {data.get('document_id')}")
                print(f"   📝 Filename: {data.get('filename')}")
                print(f"   📊 Pages: {data.get('page_count')}")
                print(f"   📈 Words: {data.get('word_count')}")
                print(f"   💾 Size: {data.get('file_size'):,} bytes")
                print(f"   🎯 Lesson Ready: {data.get('lesson_ready')}")
                
                # Show text preview
                text_preview = data.get('text', '')[:200]
                if len(data.get('text', '')) > 200:
                    text_preview += "..."
                print(f"   📖 Text Preview: {text_preview}")
                
                return data
            else:
                print(f"❌ PDF upload failed: {response.status_code}")
                error_text = response.text
                print(f"   Error: {error_text}")
                return None
                
    except Exception as e:
        print(f"❌ PDF upload error: {e}")
        return None
    finally:
        # Clean up test PDF
        if pdf_file == "test_document.pdf" and os.path.exists(pdf_file):
            os.remove(pdf_file)

def test_pdf_retrieval(document_id):
    """Test retrieving PDF documents."""
    print("\n📋 Testing PDF Document Retrieval...")
    
    try:
        response = requests.get("http://localhost:8001/api/documents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            print(f"✅ Found {len(documents)} documents in database")
            
            # Look for our uploaded document
            for doc in documents:
                if doc.get('document_id') == document_id:
                    print(f"✅ Found our uploaded document:")
                    print(f"   📄 ID: {doc.get('document_id')}")
                    print(f"   📝 Filename: {doc.get('filename')}")
                    print(f"   🕒 Uploaded: {doc.get('upload_timestamp')}")
                    return True
            
            print("⚠️  Our document not found in the list")
            return False
        else:
            print(f"❌ Document retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document retrieval error: {e}")
        return False

def main():
    """Run the complete test suite."""
    print("🧪 GnyanSetu Complete Flow Test")
    print("=" * 50)
    
    # Test services health
    print("🏥 Checking service health...")
    try:
        user_health = requests.get("http://localhost:8002/health", timeout=5)
        pdf_health = requests.get("http://localhost:8001/health", timeout=5)
        
        if user_health.status_code == 200:
            print("✅ User Service is healthy")
        else:
            print("❌ User Service is not responding")
            
        if pdf_health.status_code == 200:
            print("✅ PDF Service is healthy")
        else:
            print("❌ PDF Service is not responding")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("Please ensure services are running!")
        return
    
    print("\n" + "="*50)
    
    # Test authentication
    auth_token = test_user_auth()
    if not auth_token:
        print("❌ Authentication failed - cannot continue")
        return
    
    print("\n" + "="*50)
    
    # Test PDF upload
    pdf_result = test_pdf_upload(auth_token)
    if not pdf_result:
        print("❌ PDF upload failed")
        return
    
    document_id = pdf_result.get('document_id')
    
    print("\n" + "="*50)
    
    # Test PDF retrieval
    test_pdf_retrieval(document_id)
    
    print("\n" + "="*50)
    print("🎉 Complete Flow Test Finished!")
    print("\n💡 Next Steps:")
    print("   1. Open browser to http://localhost:3000 (Landing Page)")
    print("   2. Sign up or log in")
    print("   3. You'll be redirected to http://localhost:3001 (Dashboard)")
    print("   4. Upload a PDF file")
    print("   5. Check PDF service terminal for beautiful output!")
    print(f"   6. Document ID {document_id} is ready for lesson generation")

if __name__ == "__main__":
    main()