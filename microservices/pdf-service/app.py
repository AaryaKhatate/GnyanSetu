# PDF Service - Microservice for handling PDF upload, validation, and text extraction
# Port: 8001
# Database: MongoDB Collection - pdf_documents

import os
import logging
import json
import uuid
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import fitz  # PyMuPDF
import asyncio
import pika
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import io
from colorama import Fore, Back, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:3001", "http://localhost:8000"])

# Configure logging with custom formatting
class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored logging."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Apply colored formatter
for handler in logger.handlers:
    handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

def print_pdf_data(doc_data):
    """Print PDF data in a beautiful format to terminal."""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{Back.BLUE} 📄 NEW PDF PROCESSED {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}📄 Document ID:{Style.RESET_ALL} {Fore.CYAN}{doc_data.get('document_id', 'N/A')}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📝 Filename:{Style.RESET_ALL} {doc_data.get('filename', 'N/A')}")
    print(f"{Fore.GREEN}📊 Pages:{Style.RESET_ALL} {doc_data.get('page_count', 0)}")
    print(f"{Fore.GREEN}📈 Words:{Style.RESET_ALL} {doc_data.get('word_count', 0)}")
    print(f"{Fore.GREEN}💾 File Size:{Style.RESET_ALL} {doc_data.get('file_size', 0):,} bytes")
    print(f"{Fore.GREEN}🕒 Uploaded:{Style.RESET_ALL} {doc_data.get('upload_timestamp', 'N/A')}")
    
    # Print first 300 characters of extracted text
    text_preview = doc_data.get('text_content', '')[:300]
    if len(doc_data.get('text_content', '')) > 300:
        text_preview += "..."
    
    print(f"\n{Fore.MAGENTA}📖 TEXT PREVIEW:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*60}{Style.RESET_ALL}")
    print(f"{text_preview}")
    print(f"{Fore.WHITE}{'-'*60}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

# MongoDB Configuration
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client.Gnyansetu_PDFs
    pdf_documents = db.pdf_documents
    logger.info("Connected to MongoDB for PDF Service")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    pdf_documents = None

# RabbitMQ Configuration for event publishing
try:
    rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    rabbitmq_channel = rabbitmq_connection.channel()
    
    # Declare exchanges for events
    rabbitmq_channel.exchange_declare(exchange='pdf_events', exchange_type='topic')
    logger.info("Connected to RabbitMQ for PDF Service")
except Exception as e:
    logger.error(f"Failed to connect to RabbitMQ: {e}")
    rabbitmq_connection = None
    rabbitmq_channel = None

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf'}

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Print startup status summary
print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.WHITE}{Back.BLUE} 📄 PDF SERVICE STARTUP STATUS {Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

mongodb_status = "✅ Connected" if pdf_documents else "❌ Disconnected"
rabbitmq_status = "✅ Connected" if rabbitmq_channel else "⚠️  Disconnected (events disabled)"

print(f"{Fore.GREEN}MongoDB:    {mongodb_status}{Style.RESET_ALL}")
print(f"{Fore.YELLOW}RabbitMQ:   {rabbitmq_status}{Style.RESET_ALL}")
print(f"{Fore.CYAN}Upload Dir: ✅ {UPLOAD_FOLDER}{Style.RESET_ALL}")
print(f"{Fore.CYAN}Max Size:   ✅ {MAX_FILE_SIZE // (1024*1024)}MB{Style.RESET_ALL}")
print(f"{Fore.CYAN}Extensions: ✅ {', '.join(ALLOWED_EXTENSIONS)}{Style.RESET_ALL}")

if not pdf_documents:
    print(f"{Fore.RED}⚠️  WARNING: MongoDB unavailable - uploads will fail{Style.RESET_ALL}")
if not rabbitmq_channel:
    print(f"{Fore.YELLOW}⚠️  INFO: RabbitMQ unavailable - events disabled (non-critical){Style.RESET_ALL}")

print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_document_id(filename, content):
    """Generate a unique document ID based on filename and content hash."""
    # Create a hash of the content for uniqueness
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
    # Generate a UUID for additional uniqueness
    unique_id = str(uuid.uuid4())[:8]
    # Combine timestamp, hash, and UUID
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    
    document_id = f"pdf_{timestamp}_{content_hash}_{unique_id}"
    return document_id

def publish_event(event_type, data):
    """Publish event to RabbitMQ with retry logic."""
    if not rabbitmq_channel:
        logger.warning(f"RabbitMQ not available, skipping event: {event_type}")
        return
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            message = {
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'pdf-service',
                'data': data
            }
            
            rabbitmq_channel.basic_publish(
                exchange='pdf_events',
                routing_key=f'pdf.{event_type}',
                body=json.dumps(message)
            )
            logger.info(f"✅ Published event: {event_type}")
            return  # Success - exit retry loop
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"⚠️  Event publish failed (attempt {retry_count}/{max_retries}): {e}")
                # Wait briefly before retry
                import time
                time.sleep(0.5 * retry_count)  # Exponential backoff
            else:
                logger.warning(f"⚠️  Event publishing failed after {max_retries} attempts: {e}")
                logger.info("📄 Core PDF processing continues normally (events are optional)")
                break

def extract_text_from_pdf(pdf_file):
    """Extract text content from PDF file with OCR fallback for images."""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""
        page_count = len(doc)
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            
            if not page_text.strip():
                # Convert page to image and run OCR
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes))
                page_text = pytesseract.image_to_string(image)
            
            text_content += page_text + "\n\n"
            
            # Log progress for large PDFs
            if page_count > 10 and (page_num + 1) % 10 == 0:
                logger.info(f"Processed {page_num + 1}/{page_count} pages")
        
        doc.close()
        
        return {
            'text': text_content.strip(),
            'page_count': page_count,
            'word_count': len(text_content.split()),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return {
            'error': str(e),
            'success': False
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'service': 'pdf-service',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'mongodb_connected': pdf_documents is not None,
        'rabbitmq_connected': rabbitmq_channel is not None
    })

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """
    Handle PDF file uploads, extract text, and store metadata.
    
    Response:
    {
        "success": true,
        "document_id": "64f...",
        "text": "extracted text...",
        "filename": "document.pdf",
        "page_count": 10,
        "word_count": 2500,
        "file_size": 1024000
    }
    """
    try:
        logger.info(f"PDF upload request received from {request.remote_addr}")
        
        # Validate request
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No PDF file found in the request.'}), 400

        pdf_file = request.files['pdf_file']
        
        if pdf_file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400
        
        if not allowed_file(pdf_file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400
        
        # Check file size
        pdf_file.seek(0, os.SEEK_END)
        file_size = pdf_file.tell()
        pdf_file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large. Please upload a PDF smaller than 50MB.'}), 400
        
        # Extract text from PDF
        extraction_result = extract_text_from_pdf(pdf_file)
        
        if not extraction_result['success']:
            return jsonify({'error': f'Failed to extract text: {extraction_result["error"]}'}), 400
        
        if not extraction_result['text'].strip():
            return jsonify({
                'error': 'Could not extract any text from the PDF. The file may be image-based or corrupted.'
            }), 400

        # Generate unique document ID
        unique_doc_id = generate_document_id(pdf_file.filename, extraction_result['text'])
        
        # Prepare enhanced document metadata
        filename = secure_filename(pdf_file.filename)
        upload_time = datetime.utcnow()
        
        document_data = {
            'document_id': unique_doc_id,
            'filename': filename,
            'original_filename': pdf_file.filename,
            'file_size': file_size,
            'text_content': extraction_result['text'],
            'page_count': extraction_result['page_count'],
            'word_count': extraction_result['word_count'],
            'upload_timestamp': upload_time,
            'content_type': 'application/pdf',
            'extraction_status': 'completed',
            'processing_time': datetime.utcnow(),
            'text_hash': hashlib.md5(extraction_result['text'].encode('utf-8')).hexdigest(),
            'metadata': {
                'language': 'auto-detect',
                'readability_score': None,
                'topics': [],
                'key_phrases': []
            },
            'lesson_ready': True,
            'quiz_ready': True,
            'status': 'processed'
        }
        
        # Store in MongoDB
        mongodb_id = None
        if pdf_documents is not None:
            try:
                result = pdf_documents.insert_one(document_data)
                mongodb_id = str(result.inserted_id)
                document_data['_id'] = mongodb_id
                
                logger.info(f"{Fore.GREEN}✅ Successfully stored PDF in MongoDB:{Style.RESET_ALL}")
                logger.info(f"   📄 Document ID: {unique_doc_id}")
                logger.info(f"   🗄️  MongoDB ID: {mongodb_id}")
                
                # Print beautiful PDF data to terminal
                print_pdf_data(document_data)
                
            except Exception as db_error:
                logger.error(f"{Fore.RED}❌ Failed to store PDF metadata: {db_error}{Style.RESET_ALL}")
        
        # Publish PDF uploaded event
        event_data = {
            'document_id': unique_doc_id,
            'mongodb_id': mongodb_id,
            'filename': filename,
            'page_count': extraction_result['page_count'],
            'word_count': extraction_result['word_count'],
            'file_size': file_size,
            'timestamp': upload_time.isoformat(),
            'status': 'ready_for_lessons'
        }
        publish_event('pdf.uploaded', event_data)
        
        # Log successful processing
        logger.info(f"{Fore.GREEN}🎉 PDF Processing Complete!{Style.RESET_ALL}")
        logger.info(f"   📄 File: {filename}")
        logger.info(f"   📊 Stats: {extraction_result['word_count']} words, {extraction_result['page_count']} pages")
        logger.info(f"   🆔 Document ID: {unique_doc_id}")
        logger.info(f"   ✅ Ready for lesson generation!")

        # Prepare comprehensive response
        response_data = {
            'success': True,
            'document_id': unique_doc_id,
            'mongodb_id': mongodb_id,
            'text': extraction_result['text'],
            'filename': filename,
            'page_count': extraction_result['page_count'],
            'word_count': extraction_result['word_count'],
            'file_size': file_size,
            'upload_timestamp': upload_time.isoformat(),
            'lesson_ready': True,
            'quiz_ready': True,
            'message': 'PDF processed successfully and ready for lesson generation'
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error processing PDF upload: {str(e)}")
        return jsonify({
            'error': f'An unexpected error occurred while processing the PDF: {str(e)}'
        }), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded PDF documents."""
    try:
        if pdf_documents is None:
            return jsonify({'documents': []})
        
        documents = []
        for doc in pdf_documents.find({}, {
            'filename': 1, 'upload_timestamp': 1, 'page_count': 1, 
            'word_count': 1, 'file_size': 1
        }).sort('upload_timestamp', -1).limit(100):
            doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        return jsonify({'documents': documents})
    
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        return jsonify({'error': 'Failed to fetch documents'}), 500

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get specific document details including extracted text."""
    try:
        if pdf_documents is None:
            return jsonify({'error': 'Database not available'}), 500
        
        # Validate ObjectId format
        try:
            doc_obj_id = ObjectId(document_id)
        except:
            return jsonify({'error': 'Invalid document ID'}), 400
        
        document = pdf_documents.find_one({'_id': doc_obj_id})
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        document['_id'] = str(document['_id'])
        return jsonify({'document': document})
    
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {e}")
        return jsonify({'error': 'Failed to fetch document'}), 500

@app.route('/api/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document from the database."""
    try:
        if not pdf_documents:
            return jsonify({'error': 'Database not available'}), 500
        
        # Validate ObjectId format
        try:
            doc_obj_id = ObjectId(document_id)
        except:
            return jsonify({'error': 'Invalid document ID'}), 400
        
        result = pdf_documents.delete_one({'_id': doc_obj_id})
        
        if result.deleted_count > 0:
            # Publish document deleted event
            publish_event('deleted', {'document_id': document_id})
            return jsonify({'success': True, 'message': 'Document deleted successfully'})
        else:
            return jsonify({'error': 'Document not found'}), 404
    
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500

@app.route('/ws/<path:path>')
def websocket_info(path):
    """Inform about WebSocket endpoint availability."""
    return jsonify({
        'error': 'WebSocket not supported',
        'message': 'This PDF service provides REST API endpoints only',
        'requested_path': f'/ws/{path}',
        'available_endpoints': [
            'GET /health - Service health check',
            'POST /api/upload - Upload PDF files',
            'GET /api/documents - List all documents',
            'GET /api/documents/<id> - Get specific document',
            'DELETE /api/documents/<id> - Delete document'
        ],
        'suggestion': 'Use HTTP REST endpoints for PDF processing'
    }), 404

if __name__ == '__main__':
    logger.info("🎨 Starting PDF Service with beautiful colored output on port 8001")
    app.run(host='0.0.0.0', port=8001, debug=True)