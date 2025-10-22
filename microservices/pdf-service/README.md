# PDF Service

A microservice responsible for handling PDF upload, validation, text extraction, and storage in the GnyanSetu platform.

## 🎯 **Service Responsibilities**

- **PDF Upload & Validation**: Accept PDF files, validate format and size
- **Text Extraction**: Extract text content from PDF documents using PyMuPDF
- **Metadata Storage**: Store document metadata and extracted text in MongoDB
- **Event Publishing**: Publish events to RabbitMQ for other services to consume
- **Document Management**: CRUD operations for PDF documents

## 📊 **Database Schema**

### MongoDB Collection: `pdf_documents`

```javascript
{
  "_id": ObjectId("..."),
  "filename": "document.pdf",
  "original_filename": "My Document.pdf", 
  "file_size": 1024000,
  "text_content": "Extracted text content...",
  "page_count": 10,
  "word_count": 2500,
  "upload_timestamp": ISODate("2024-01-01T10:00:00Z"),
  "content_type": "application/pdf",
  "extraction_status": "completed"
}
```

## 🚀 **API Endpoints**

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "service": "pdf-service",
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "mongodb_connected": true,
  "rabbitmq_connected": true
}
```

### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data

Body: pdf_file (file)
```

**Response:**
```json
{
  "success": true,
  "document_id": "64f1234567890abcdef12345",
  "text": "Extracted text content...",
  "filename": "document.pdf",
  "page_count": 10,
  "word_count": 2500,
  "file_size": 1024000
}
```

### Get Documents List
```http
GET /api/documents
```

**Response:**
```json
{
  "documents": [
    {
      "_id": "64f1234567890abcdef12345",
      "filename": "document.pdf",
      "upload_timestamp": "2024-01-01T10:00:00Z",
      "page_count": 10,
      "word_count": 2500,
      "file_size": 1024000
    }
  ]
}
```

### Get Specific Document
```http
GET /api/documents/{document_id}
```

**Response:**
```json
{
  "document": {
    "_id": "64f1234567890abcdef12345",
    "filename": "document.pdf",
    "text_content": "Full extracted text...",
    "page_count": 10,
    "word_count": 2500,
    "upload_timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Delete Document
```http
DELETE /api/documents/{document_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

## 📡 **Event Publishing**

The service publishes events to RabbitMQ exchange `pdf_events`:

### PDF Uploaded Event
```json
{
  "event_type": "uploaded",
  "timestamp": "2024-01-01T10:00:00Z",
  "service": "pdf-service",
  "data": {
    "document_id": "64f1234567890abcdef12345",
    "filename": "document.pdf",
    "page_count": 10,
    "word_count": 2500,
    "file_size": 1024000
  }
}
```

### PDF Deleted Event
```json
{
  "event_type": "deleted",
  "timestamp": "2024-01-01T10:00:00Z",
  "service": "pdf-service",
  "data": {
    "document_id": "64f1234567890abcdef12345"
  }
}
```

## 🔧 **Setup & Installation**

### Prerequisites
- Python 3.10+
- MongoDB (running on localhost:27017)
- RabbitMQ (optional, for event publishing)

### Installation Steps

1. **Navigate to service directory:**
   ```bash
   cd microservices/pdf-service
   ```

2. **Run the startup script:**
   ```powershell
   .\start_service.ps1
   ```

   Or manually:

3. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env  # Edit as needed
   ```

6. **Start the service:**
   ```bash
   python app.py
   ```

## 🧪 **Testing**

Run the test script to verify service functionality:

```bash
python test_service.py
```

Test endpoints manually:

```bash
# Health check
curl http://localhost:8001/health

# Upload PDF (replace with actual PDF file)
curl -X POST -F "pdf_file=@document.pdf" http://localhost:8001/api/upload

# Get documents
curl http://localhost:8001/api/documents
```

## 🐳 **Docker Deployment**

### Build Image
```bash
docker build -t gnyansetu-pdf-service .
```

### Run Container
```bash
docker run -p 8001:8001 -e MONGO_URI=mongodb://host.docker.internal:27017/ gnyansetu-pdf-service
```

## ⚙️ **Configuration**

Environment variables in `.env`:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=Gnyansetu_PDFs

# RabbitMQ Configuration  
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# Service Configuration
SERVICE_PORT=8001
SERVICE_HOST=0.0.0.0
DEBUG=true

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_FOLDER=uploads

# CORS Configuration
CORS_ORIGINS=http://localhost:3001,http://localhost:8000
```

## 📈 **Monitoring & Logging**

- **Health Check**: `GET /health` for service monitoring
- **Logging**: Structured logging with configurable levels
- **Metrics**: Track upload counts, processing times, and error rates

## 🔄 **Integration with Other Services**

### AI Lesson Service
- Consumes `pdf.uploaded` events to trigger lesson generation
- Fetches document text via GET `/api/documents/{id}`

### Analytics Service  
- Tracks PDF upload statistics
- Monitors processing performance

### Frontend Integration
- Upload PDFs via form submission
- Display upload progress and results
- Browse and manage uploaded documents

## 🚨 **Error Handling**

The service handles various error scenarios:

- **Invalid file format**: Returns 400 with descriptive message
- **File too large**: Returns 400 with size limit information  
- **Extraction failure**: Returns 400 with extraction error details
- **Database errors**: Returns 500 with generic error message
- **Missing files**: Returns 400 for empty uploads

## 📋 **Next Steps**

1. **Test the PDF Service** by running the startup script
2. **Verify health check** at http://localhost:8001/health
3. **Test PDF upload** using the test script or manual upload
4. **Check MongoDB** to confirm document storage
5. **Proceed to AI Lesson Service** creation

---

**Port**: 8001  
**Database**: MongoDB Collection `pdf_documents`  
**Events**: RabbitMQ exchange `pdf_events`