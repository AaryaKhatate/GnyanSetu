# PDF Processing Service with OCR and Image Extraction
import os
import io
import logging
import base64
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
from django.conf import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Advanced PDF processing with text extraction, OCR, and image handling"""
    
    def __init__(self):
        self.tesseract_path = settings.PDF_SETTINGS.get('TESSERACT_PATH')
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
    
    def process_pdf(self, pdf_file, user_id, filename):
        """
        Complete PDF processing pipeline:
        1. Extract text content
        2. Extract images
        3. Apply OCR on images
        4. Combine all text
        """
        try:
            logger.info(f"Processing PDF: {filename} for user: {user_id}")
            
            # Open PDF document
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
            
            # Initialize results
            text_content = ""
            images_data = []
            page_data = []
            
            # Process each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Extract text from page
                page_text = page.get_text()
                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                # Extract images from page
                page_images = self._extract_images_from_page(page, page_num)
                images_data.extend(page_images)
                
                # Apply OCR if page has little text but images
                if len(page_text.strip()) < 50 and page_images:
                    ocr_text = self._apply_ocr_to_page(page)
                    if ocr_text:
                        text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}\n"
                
                page_data.append({
                    'page_number': page_num + 1,
                    'text_length': len(page_text),
                    'image_count': len(page_images),
                    'has_ocr': len(page_text.strip()) < 50 and len(page_images) > 0
                })
            
            pdf_document.close()
            
            # Prepare metadata
            metadata = {
                'filename': filename,
                'total_pages': len(pdf_document),
                'total_images': len(images_data),
                'text_length': len(text_content),
                'processing_method': 'text_extraction_with_ocr',
                'page_data': page_data
            }
            
            logger.info(f"PDF processed successfully: {len(text_content)} chars, {len(images_data)} images")
            
            return {
                'text_content': text_content,
                'images_data': images_data,
                'metadata': metadata,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            return {
                'text_content': "",
                'images_data': [],
                'metadata': {'error': str(e)},
                'success': False
            }
    
    def _extract_images_from_page(self, page, page_num):
        """Extract images from a PDF page"""
        images_data = []
        
        try:
            # Get image list from page
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Convert to PIL Image
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Convert to base64 for storage
                        buffered = io.BytesIO()
                        pil_image.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Apply OCR to extract text from image
                        ocr_text = ""
                        try:
                            ocr_text = pytesseract.image_to_string(pil_image)
                        except Exception as ocr_e:
                            logger.warning(f"OCR failed for image {img_index} on page {page_num}: {ocr_e}")
                        
                        images_data.append({
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'image_data': img_base64,
                            'ocr_text': ocr_text.strip(),
                            'image_format': 'PNG',
                            'image_size': pil_image.size
                        })
                    
                    pix = None
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting images from page {page_num}: {e}")
        
        return images_data
    
    def _apply_ocr_to_page(self, page):
        """Apply OCR to entire page when text extraction yields little content"""
        try:
            # Render page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Apply OCR
            ocr_text = pytesseract.image_to_string(pil_image)
            pix = None
            
            return ocr_text.strip()
            
        except Exception as e:
            logger.error(f"OCR failed for page: {e}")
            return ""
    
    def validate_pdf(self, pdf_file):
        """Validate PDF file before processing"""
        try:
            # Check file size
            pdf_file.seek(0, 2)  # Seek to end
            file_size = pdf_file.tell()
            pdf_file.seek(0)  # Reset to beginning
            
            max_size = settings.PDF_SETTINGS.get('MAX_FILE_SIZE', 50 * 1024 * 1024)
            if file_size > max_size:
                return False, f"File size ({file_size}) exceeds maximum allowed size ({max_size})"
            
            # Try to open with PyMuPDF
            test_doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            page_count = len(test_doc)
            test_doc.close()
            pdf_file.seek(0)  # Reset for actual processing
            
            if page_count == 0:
                return False, "PDF contains no pages"
            
            return True, f"Valid PDF with {page_count} pages"
            
        except Exception as e:
            return False, f"Invalid PDF file: {e}"