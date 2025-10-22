# Test script for PDF Service
import requests
import json
import sys
import os

# PDF Service URL
PDF_SERVICE_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{PDF_SERVICE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check Passed")
            print(f"   Status: {data['status']}")
            print(f"   MongoDB Connected: {data['mongodb_connected']}")
            print(f"   RabbitMQ Connected: {data['rabbitmq_connected']}")
            return True
        else:
            print(f"❌ Health Check Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_pdf_upload():
    """Test PDF upload functionality."""
    print("\n📄 Testing PDF Upload...")
    
    # Create a simple test PDF content
    test_content = """
    # Test PDF Content
    
    This is a test PDF document for the microservices architecture.
    
    ## Chapter 1: Introduction
    Welcome to the PDF Service test.
    
    ## Chapter 2: Features
    - PDF text extraction
    - File validation  
    - Metadata storage
    - Event publishing
    
    ## Conclusion
    This completes our test document.
    """
    
    # For testing, we'll create a simple text file (in real scenario, use actual PDF)
    test_file = "test_document.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'pdf_file': (test_file, f, 'application/pdf')}
            response = requests.post(f"{PDF_SERVICE_URL}/api/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PDF Upload Successful")
            print(f"   Document ID: {data.get('document_id')}")
            print(f"   Filename: {data.get('filename')}")
            print(f"   Word Count: {data.get('word_count')}")
            return data.get('document_id')
        else:
            print(f"❌ PDF Upload Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ PDF Upload Error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

def test_get_documents():
    """Test getting list of documents."""
    print("\n📋 Testing Get Documents...")
    try:
        response = requests.get(f"{PDF_SERVICE_URL}/api/documents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get Documents Successful")
            print(f"   Found {len(data['documents'])} documents")
            return True
        else:
            print(f"❌ Get Documents Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get Documents Error: {e}")
        return False

def test_get_specific_document(document_id):
    """Test getting specific document details."""
    if not document_id:
        print("\n⚠️  Skipping specific document test (no document ID)")
        return False
        
    print(f"\n📖 Testing Get Specific Document (ID: {document_id[:8]}...)")
    try:
        response = requests.get(f"{PDF_SERVICE_URL}/api/documents/{document_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get Specific Document Successful")
            print(f"   Filename: {data['document']['filename']}")
            print(f"   Text Length: {len(data['document']['text_content'])} characters")
            return True
        else:
            print(f"❌ Get Specific Document Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get Specific Document Error: {e}")
        return False

def run_all_tests():
    """Run all PDF Service tests."""
    print("🚀 Starting PDF Service Tests")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("\n❌ Health check failed. Make sure the PDF Service is running.")
        print("   Start the service with: python app.py")
        sys.exit(1)
    
    # Test PDF upload
    document_id = test_pdf_upload()
    
    # Test get documents
    test_get_documents()
    
    # Test get specific document
    test_get_specific_document(document_id)
    
    print("\n" + "=" * 50)
    print("🎉 PDF Service Tests Completed!")
    
    if document_id:
        print(f"\n💡 You can test the document endpoint manually:")
        print(f"   GET {PDF_SERVICE_URL}/api/documents/{document_id}")

if __name__ == "__main__":
    run_all_tests()