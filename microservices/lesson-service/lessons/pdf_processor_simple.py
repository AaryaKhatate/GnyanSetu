# Simplified PDF Processing Service (no OCR dependency)
import os
import io
import logging
import base64
from PIL import Image
import fitz  # PyMuPDF
from django.conf import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Simplified PDF processing with text extraction"""
    
    def __init__(self):
        self.use_ocr = False  # Disable OCR for now
    
    def validate_pdf(self, pdf_file):
        """Validate if the uploaded file is a valid PDF"""
        doc = None
        try:
            # Reset file pointer
            pdf_file.seek(0)
            
            # Read content into memory
            pdf_content = pdf_file.read()
            
            # Try to open with PyMuPDF
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            page_count = len(doc)
            
            # Reset file pointer for future use
            pdf_file.seek(0)
            
            if page_count == 0:
                return None, "PDF has no pages"
            
            return True, f"Valid PDF with {page_count} pages"
            
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            # Reset file pointer even on error
            try:
                pdf_file.seek(0)
            except:
                pass
            return None, f"Invalid PDF file: {str(e)}"
            
        finally:
            # Always close the document if it was opened
            if doc is not None:
                try:
                    doc.close()
                except:
                    pass
    
    def process_pdf(self, pdf_file, user_id, filename):
        """
        Simplified PDF processing pipeline:
        1. Extract text content
        2. Extract basic metadata
        3. Return results without OCR
        """
        pdf_document = None
        try:
            logger.info(f"Processing PDF: {filename} for user: {user_id}")
            
            # Reset file pointer
            pdf_file.seek(0)
            
            # Read file content into memory to avoid stream issues
            pdf_content = pdf_file.read()
            
            # Open PDF document from memory
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            
            # Get document info before processing
            total_pages = len(pdf_document)
            logger.info(f"PDF has {total_pages} pages")
            
            # Initialize results
            text_content = ""
            images_data = []
            
            # Process each page
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                
                # Extract text from page
                page_text = page.get_text()
                if page_text.strip():  # Only add if there's actual text
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                # Extract images from page
                image_list = page.get_images()
                if image_list:
                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            base_image = pdf_document.extract_image(xref)
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]
                            
                            # Convert to PIL Image
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            
                            # Resize if too large (max 1024px for LLM efficiency)
                            max_size = 1024
                            if pil_image.width > max_size or pil_image.height > max_size:
                                pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                            
                            # Convert to base64 for storage and LLM
                            buffered = io.BytesIO()
                            pil_image.save(buffered, format="PNG")
                            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            
                            images_data.append({
                                'page': page_num + 1,
                                'image_index': img_index,
                                'width': pil_image.width,
                                'height': pil_image.height,
                                'format': image_ext,
                                'base64': f"data:image/png;base64,{img_base64}",
                                'ocr_text': ""  # Can add OCR later if needed
                            })
                            
                            logger.info(f"✅ Extracted image {img_index} from page {page_num + 1}: {pil_image.width}x{pil_image.height}")
                            
                        except Exception as e:
                            logger.error(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
            
            # Prepare metadata while document is still open
            metadata = {
                'total_pages': total_pages,
                'total_images': len(images_data),  # Now actual extracted images
                'text_length': len(text_content),
                'has_text': len(text_content.strip()) > 0,
                'processing_method': 'text_and_image_extraction'  # Updated
            }
            
            # Check if we got any content
            if len(text_content.strip()) < 10:
                logger.warning(f"PDF {filename} has very little text content")
                text_content = f"PDF processed but minimal text found. File: {filename}\nPlease ensure the PDF contains readable text."
            
            logger.info(f"PDF processing completed: {len(text_content)} characters extracted")
            
            return {
                'success': True,
                'text_content': text_content,
                'images_data': images_data,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {'error': str(e)}
            }
            
        finally:
            # Always close the document if it was opened
            if pdf_document is not None:
                try:
                    pdf_document.close()
                except:
                    pass  # Ignore cleanup errors