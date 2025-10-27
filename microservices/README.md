# GnyanSetu Microservices

This folder contains all the microservices that power the GnyanSetu AI Virtual Teacher platform.

## Services Overview

### 1. API Gateway (Port 8000)
- **Purpose**: Central routing hub for all microservices
- **Location**: `api-gateway/`
- **Tech Stack**: FastAPI, Python
- **Key Features**: Request routing, CORS handling, service health checks

### 2. User Service (Port 8002)
- **Purpose**: User authentication, registration, and profile management
- **Location**: `user-service-django/`
- **Tech Stack**: Django, MongoDB, JWT
- **Key Features**: 
  - User registration and login
  - Google OAuth integration
  - OTP-based password reset
  - Profile management

### 3. Lesson Service (Port 8003)
- **Purpose**: AI-powered lesson generation using Google Gemini
- **Location**: `lesson-service/`
- **Tech Stack**: Django, Google Gemini AI, MongoDB
- **Key Features**:
  - PDF to lesson conversion
  - Multimodal content generation (text + images)
  - Subject-specific teaching strategies
  - Visualization data extraction
  - Quiz and notes generation

### 4. Teaching Service (Port 8004)
- **Purpose**: Real-time teaching sessions with WebSocket support
- **Location**: `teaching-service/`
- **Tech Stack**: FastAPI, WebSockets, MongoDB
- **Key Features**:
  - Real-time teaching sessions
  - Interactive whiteboard state management
  - Conversation history tracking
  - Session management

### 5. Quiz & Notes Service (Port 8005)
- **Purpose**: Automatic quiz and notes generation from lessons
- **Location**: `quiz-notes-service/`
- **Tech Stack**: FastAPI, MongoDB
- **Key Features**:
  - AI-powered quiz generation
  - Structured notes creation
  - MongoDB integration

### 6. Visualization Service (Port 8006)
- **Purpose**: Konva.js visualization generation for whiteboard teaching
- **Location**: `visualization-service/`
- **Tech Stack**: FastAPI, Google Gemini AI, Konva.js
- **Key Features**:
  - Dynamic whiteboard command generation
  - Subject-specific visualizations
  - Animation sequence creation
  - Coordinate management

### 7. PDF Service (Port 8007)
- **Purpose**: PDF processing, text extraction, and OCR
- **Location**: `pdf-service/`
- **Tech Stack**: FastAPI, PyPDF2, Tesseract OCR
- **Key Features**:
  - PDF text extraction
  - Image extraction from PDFs
  - OCR for scanned documents

## Quick Start

### Prerequisites
- Python 3.8 or higher
- MongoDB running on localhost:27017
- Google Gemini API Key
- Node.js (for frontend)

### Environment Setup

Create a `.env` file in the root directory with:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_URI=mongodb://localhost:27017/
SECRET_KEY=your_secret_key_here
```

### Starting Services

**Option 1: Start All Services (Recommended for Production)**
```bash
cd E:\Project\GnyanSetu
start_gnyansetu.bat
```

**Option 2: Start Services from Microservices Folder**
```bash
cd microservices
start_all_services_with_viz.bat
```

**Option 3: Start Individual Service**
Navigate to the service folder and run its startup script.

## Service Architecture

```
                        CLIENT REQUEST
                              |
                              v
                    ┌─────────────────┐
                    │  API Gateway    │
                    │   Port 8000     │
                    └────────┬────────┘
                             |
        ┌────────────────────┼────────────────────┐
        |                    |                    |
        v                    v                    v
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ User Service  │   │Lesson Service │   │Teaching Service│
│   Port 8002   │   │   Port 8003   │   │   Port 8004   │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            |
                ┌───────────┼───────────┐
                v           v           v
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │Quiz/Notes│  │   Viz    │  │   PDF    │
        │Port 8005 │  │Port 8006 │  │Port 8007 │
        └──────────┘  └──────────┘  └──────────┘
```

## API Endpoints

All services are accessible through the API Gateway at `http://localhost:8000`

### Common Endpoints
- Health Check: `GET /health`
- Service Status: `GET /status`

### Service-Specific Endpoints
Refer to individual service README files for detailed API documentation.

## Database Schema

All services use MongoDB with separate collections:
- `gnyansetu_users` - User authentication and profiles
- `gnyansetu_lessons` - Generated lessons
- `gnyansetu_teaching` - Teaching sessions
- `gnyansetu_visualizations` - Visualization data
- `gnyansetu_quiz` - Quiz data
- `gnyansetu_notes` - Notes data

## Development

### Installing Dependencies
```bash
cd microservices
pip install -r requirements.txt
```

### Running Tests
```bash
# Test individual service
cd lesson-service
python manage.py test

# Test API Gateway
cd api-gateway
pytest
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running: `net start MongoDB`
   - Check connection string in `.env` file

2. **Port Already in Use**
   - Check if services are already running
   - Kill existing processes: `taskkill /F /IM python.exe`

3. **GEMINI_API_KEY Not Found**
   - Create `.env` file with your API key
   - Restart the service

4. **Import Errors**
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python version (requires 3.8+)

## Performance Optimization

- Lesson generation: ~30-60 seconds
- Quiz/Notes generation: ~10-15 seconds (async)
- Visualization generation: ~5-10 seconds
- API response time: <100ms (average)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See LICENSE file in the root directory.

## Support

For issues and questions:
- Create an issue on GitHub
- Contact: [Your Contact Information]
