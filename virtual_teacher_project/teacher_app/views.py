# teacher_app/views.py

import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
import fitz  # PyMuPDF

# It's good practice to get a logger instance.
logger = logging.getLogger(__name__)

def teacher_view(request: HttpRequest):
    """Renders the main teacher page."""
    return render(request, "teacher_app/teacher.html")

@require_POST  # Ensures this view only accepts POST requests.
def upload_pdf(request: HttpRequest):
    """Handles PDF file uploads, extracts text, and returns it as JSON."""
    if not request.FILES.get('pdf_file'):
        return JsonResponse({'error': 'No PDF file found in the request.'}, status=400)

    pdf_file = request.FILES['pdf_file']
    
    # Validate that it's a PDF file
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Invalid file type. Please upload a PDF.'}, status=400)
    
    try:
        # Open the PDF from the in-memory file
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        
        if not text_content.strip():
             return JsonResponse({'error': 'Could not extract any text from the PDF.'}, status=400)

        # Return only the text, as that's what the consumer needs
        return JsonResponse({'text': text_content})
    
    except Exception as e:
        logger.error(f"Error processing PDF '{pdf_file.name}': {e}")
        return JsonResponse({'error': f'An unexpected error occurred while processing the PDF: {str(e)}'}, status=500)