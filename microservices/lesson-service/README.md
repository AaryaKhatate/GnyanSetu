#  GnyanSetu Lesson Service

**Advanced AI-Powered Lesson Generation Service**

Port: `8003`  
Framework: Django + PyMongo  
AI Engine: Google Gemini  
Database: MongoDB

## � Features

### � Advanced PDF Processing
- **Text Extraction**: High-quality text extraction from PDFs
- **Image Processing**: Extract and process images from PDFs
- **OCR Technology**: Convert scanned PDFs and images to text using Tesseract
- **Multi-format Support**: Handle various PDF formats and layouts
- **User-specific Storage**: All PDF data linked to user accounts

###  AI Lesson Generation
- **Google Gemini Integration**: Powered by state-of-the-art AI
- **Multiple Lesson Types**:
  - � **Interactive**: Engaging lessons with activities
  -  **Quiz**: Test-based learning with Q&A
  - � **Summary**: Concise key points extraction
  - � **Detailed**: Comprehensive deep-dive lessons
- **Smart Title Generation**: AI creates appropriate lesson titles
- **Fallback System**: Graceful degradation when AI is unavailable

### � User Management
- **User-specific Data**: All content tied to authenticated users
- **Lesson History**: Track all generated lessons
- **Activity Tracking**: Monitor user interactions
- **Personal Dashboard**: User-specific lesson library

### � Technical Features
- **RESTful API**: Clean, documented endpoints
- **MongoDB Integration**: Scalable document storage
- **Health Monitoring**: Service status and diagnostics
- **Error Handling**: Comprehensive error management
- **Beautiful Logging**: Colored terminal output

## � API Endpoints

### Health & Status
```http
GET /health/
```
**Response**: Service status, database connection, AI model info

### Lesson Generation
```http
POST /api/generate-lesson/
Content-Type: multipart/form-data

pdf_file: [PDF FILE]
user_id: string
lesson_type: interactive|quiz|summary|detailed (optional, default: interactive)
```

**Response**: Complete lesson with title, content, and metadata

### User Lessons
```http
GET /api/users/{user_id}/lessons/
```
**Response**: All lessons for a specific user

### User History
```http
GET /api/users/{user_id}/history/
```
**Response**: User's lesson generation history

### Lesson Details
```http
GET /api/lessons/{lesson_id}/
```
**Response**: Detailed lesson information

### Regenerate Lesson
```http
POST /api/lessons/{lesson_id}/regenerate/
Content-Type: application/json

{
  "lesson_type": "quiz"
}
```

## � Setup & Installation

### Prerequisites
- Python 3.8+
- MongoDB running on localhost:27017
- Google Gemini API key
- Tesseract OCR installed (optional, for enhanced OCR)

### Environment Variables
Create `.env` file:
```env
# AI Configuration
GEMINI_API_KEY=your_google_gemini_api_key_here

# Database
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_NAME=Gnyansetu_Lessons

# Optional OCR
TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
```

### Installation
```bash
# Activate virtual environment
cd e:\Project
.\venv\Scripts\Activate.ps1

# Navigate to lesson service
cd Gnyansetu_Updated_Architecture\microservices\lesson-service

# Install dependencies (already done in venv)
pip install -r requirements.txt

# Start the service
python start_lesson_service.py
```

## � Usage Examples

### Generate Interactive Lesson
```bash
curl -X POST http://localhost:8003/api/generate-lesson/ \
  -F "pdf_file=@educational_document.pdf" \
  -F "user_id=user123" \
  -F "lesson_type=interactive"
```

### Get User's Lessons
```bash
curl http://localhost:8003/api/users/user123/lessons/
```

### Health Check
```bash
curl http://localhost:8003/health/
```

## � Database Schema

### PDF Data Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  filename: String,
  text_content: String,
  images_data: [
    {
      page_number: Number,
      image_index: Number,
      image_data: String (base64),
      ocr_text: String,
      image_format: String,
      image_size: [width, height]
    }
  ],
  metadata: Object,
  created_at: DateTime,
  updated_at: DateTime,
  status: String
}
```

### Lessons Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  pdf_id: ObjectId,
  lesson_title: String,
  lesson_content: String,
  lesson_type: String,
  metadata: Object,
  created_at: DateTime,
  updated_at: DateTime,
  status: String
}
```

### User Histories Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  pdf_id: ObjectId,
  lesson_id: ObjectId,
  action: String,
  timestamp: DateTime
}
```

## � Configuration

### AI Settings
- **Model**: `gemini-1.5-flash` (default)
- **Max Tokens**: 8000
- **Temperature**: 0.7
- **Fallback**: Enabled for graceful degradation

### PDF Processing
- **Max File Size**: 50MB
- **Supported Formats**: PDF only
- **OCR**: Enabled with Tesseract
- **Image Extraction**: Enabled

##  Integration with Other Services

### API Gateway
- All lesson service endpoints are routed through the API Gateway
- Authentication handled by User Service
- PDF processing can collaborate with PDF Service

### User Service
- User authentication and authorization
- User-specific data isolation
- Session management

### Dashboard
- Frontend integration for lesson display
- User lesson library interface
- History and progress tracking

## � Service Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Dashboard     │───▶│ API Gateway  │───▶│ Lesson Service  │
│  (Frontend)     │    │  (Port 8000) │    │  (Port 8003)    │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                     │
                                           ┌─────────▼─────────┐
                                           │    MongoDB        │
                                           │ Gnyansetu_Lessons │
                                           └───────────────────┘
                                                     │
                                           ┌─────────▼─────────┐
                                           │  Google Gemini    │
                                           │   AI Service      │
                                           └───────────────────┘
```

##  Sample Lesson Output

**Title**: "Understanding Photosynthesis in Plants"

**Content**: 
```markdown
# Understanding Photosynthesis in Plants

## Introduction
Photosynthesis is the remarkable process by which plants convert sunlight into energy...

## Learning Objectives
- Understand the chemical equation of photosynthesis
- Identify the key components required for photosynthesis
- Explain the two main stages: light and dark reactions
- Recognize the importance of photosynthesis in ecosystems

## Main Content

### What is Photosynthesis?
[Detailed explanation with diagrams extracted from PDF]

### The Process
[Step-by-step breakdown]

## Interactive Elements
** Think About It**: How would life on Earth be different without photosynthesis?

**� Activity**: Design an experiment to test factors affecting photosynthesis rate

## Key Takeaways
- Photosynthesis converts CO₂ + H₂O + sunlight → glucose + O₂
- Occurs in chloroplasts of plant cells
- Essential for all life on Earth
- Two main stages: light-dependent and light-independent reactions

## Practice Questions
1. What are the raw materials needed for photosynthesis?
2. Where exactly in the plant cell does photosynthesis occur?
3. How does photosynthesis contribute to the oxygen cycle?

## Further Exploration
- Research different types of photosynthesis (C3, C4, CAM)
- Investigate how climate change affects photosynthesis rates
- Explore artificial photosynthesis technologies
```

##  Ready to Generate Amazing Lessons!

Your Django-based Lesson Service is now ready to transform PDFs into engaging educational content using the power of AI! �