#!/usr/bin/env python3
"""
Test the PDF processor directly to verify the fix
"""
import sys
import os
sys.path.append(r'e:\Project\Gnyansetu_Updated_Architecture\microservices\lesson-service')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesson_service.settings')
import django
django.setup()

from lessons.pdf_processor_simple import PDFProcessor
from io import BytesIO
import requests

def test_pdf_processor_fix():
    """Test the fixed PDF processor with a real PDF"""
    
    processor = PDFProcessor()
    
    # Download a small test PDF (Python logo from matplotlib)
    pdf_path = r"E:\Project\venv\Lib\site-packages\matplotlib\mpl-data\images\back.pdf"
    
    try:
        print("🔍 Testing fixed PDF processor...")
        
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"📄 PDF file size: {len(pdf_content)} bytes")
        
        # Create a file-like object
        class MockFile:
            def __init__(self, content):
                self.content = content
                self.position = 0
            
            def read(self):
                data = self.content[self.position:]
                self.position = len(self.content)
                return data
            
            def seek(self, position):
                self.position = position
        
        mock_file = MockFile(pdf_content)
        
        # Test validation first
        print("\n🔧 Testing PDF validation...")
        is_valid, message = processor.validate_pdf(mock_file)
        print(f"   Validation result: {is_valid}")
        print(f"   Message: {message}")
        
        if is_valid:
            # Test processing
            print("\n⚙️ Testing PDF processing...")
            result = processor.process_pdf(mock_file, "test_user", "test.pdf")
            
            print(f"\n✅ Processing result:")
            print(f"   Success: {result.get('success')}")
            print(f"   Text length: {len(result.get('text_content', ''))}")
            print(f"   Pages: {result.get('metadata', {}).get('total_pages', 0)}")
            print(f"   Images: {result.get('metadata', {}).get('total_images', 0)}")
            
            if result.get('success'):
                text_preview = result.get('text_content', '')[:200]
                print(f"\n📝 Text preview: {text_preview}...")
                print("\n🎉 PDF processor fix successful!")
                return True
            else:
                print(f"\n❌ Processing failed: {result.get('error')}")
                return False
        else:
            print(f"\n❌ Validation failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_processor_fix()
    if success:
        print("\n🚀 The PDF upload fix should now work!")
        print("   Try uploading a PDF through the Dashboard again.")
    else:
        print("\n⚠️  The fix needs more work.")