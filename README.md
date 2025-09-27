# 📘 GnyanSetu – AI-Powered Interactive Learning Platform

**GnyanSetu** is an AI-powered interactive learning platform that converts static educational content into dynamic, personalized lessons with real-time voice narration, whiteboard-style visualizations, and interactive diagrams.

The platform allows students to upload study materials (PDFs), generates AI-driven interactive lessons, and provides step-by-step teaching with quizzes and downloadable notes.

---

## ✨ Features

- **PDF Upload & Processing**: Upload educational PDFs and extract text content
- **AI-Powered Lesson Generation**: Uses Google's Gemini AI to create interactive lessons
- **Real-time Whiteboard**: Dynamic visualizations with shapes, text, and arrows
- **Interactive Quizzes**: Auto-generated quizzes based on lesson content
- **Notes Generation**: Automatic summary notes with downloadable PDFs
- **WebSocket Communication**: Real-time communication between frontend and backend
- **MongoDB Storage**: Store lessons, quizzes, student progress, and analytics
- **Responsive UI**: Modern React interface with Tailwind CSS

## 🛠️ Technical Stack

### Backend

- **Django 4.2**: Web framework with ASGI support
- **Channels & Daphne**: WebSocket support and ASGI server
- **Motor & PyMongo**: Async MongoDB integration
- **Google Generative AI**: AI lesson generation
- **PyMuPDF**: PDF text extraction
- **LangChain**: AI prompt management
- **Django CORS Headers**: Cross-origin resource sharing

### Frontend

- **React 18**: User interface framework
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **Lucide React**: Modern icon library
- **jsPDF**: Client-side PDF generation

### Database

- **MongoDB**: Document storage for lessons, quizzes, and analytics

## 📁 Project Structure

```
virtual_teacher_project/
├── teacher_app/                 # Django app
│   ├── views.py                # API endpoints and PDF handling
│   ├── consumers.py            # WebSocket consumer for real-time communication
│   ├── models.py              # Django models
│   ├── mongo.py               # MongoDB connection and document schemas
│   ├── mongo_collections.py   # MongoDB collections
│   ├── urls.py                # URL routing
│   └── routing.py             # WebSocket routing
├── virtual_teacher_project/    # Django project settings
│   ├── settings.py            # Configuration with CORS and MongoDB
│   ├── urls.py                # Main URL routing
│   └── asgi.py                # ASGI application for WebSocket support
├── UI/Dashboard/Dashboard/     # React frontend
│   ├── src/
│   │   ├── App.jsx            # Main application component
│   │   ├── components/        # React components
│   │   │   ├── UploadBox.jsx  # PDF upload with backend integration
│   │   │   ├── Whiteboard.jsx # Interactive lesson display with WebSocket
│   │   │   ├── Quiz.jsx       # Quiz component with backend API
│   │   │   ├── Notes.jsx      # Notes and downloads
│   │   │   └── SessionManager.jsx # Main session controller
│   │   └── index.js           # Entry point
│   └── package.json           # Node.js dependencies
├── requirements.txt           # Python dependencies
├── start_server.bat          # Backend startup script
└── start_frontend.bat        # Frontend startup script
```

## 🚀 Quick Start

### Option 1: One-Click Startup (Recommended)

**Windows:**

```bash
# Double-click or run:
start_full_project.bat
# OR
powershell -ExecutionPolicy Bypass -File start_full_project.ps1
```

**Linux/Mac:**

```bash
chmod +x start_dev.sh
./start_dev.sh
```

### Option 2: Manual Setup (for development)

### Prerequisites

1. **Python 3.8+** installed
2. **Node.js 16+** and npm installed
3. **MongoDB** installed and running on localhost:27017
4. **Google API Key** for Gemini AI ([Get it here](https://makersuite.google.com/app/apikey))

#### Backend Setup

1. **Navigate to the project directory:**

   ```bash
   cd virtual_teacher_project
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:

   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. **Start MongoDB:**
   Make sure MongoDB is running on `mongodb://localhost:27017`

5. **Run database migrations:**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Start the Django server with Daphne:**

   ```bash
   daphne -b 0.0.0.0 -p 8000 virtual_teacher_project.asgi:application
   ```

   Or use the provided script:

   ```bash
   start_server.bat
   ```

### Frontend Setup

1. **Navigate to the React app directory:**

   ```bash
   cd UI/Dashboard/Dashboard
   ```

2. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

3. **Start the React development server:**

   ```bash
   npm start
   ```

   Or use the provided script from the project root:

   ```bash
   start_frontend.bat
   ```

### 🌐 Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws/teacher/

## 📡 API Endpoints

### File Upload

- `POST /upload_pdf/` - Upload and process PDF files

### Student Management

- `GET /api/students/` - List all students
- `POST /api/students/` - Create new student

### Lesson Management

- `GET /api/lessons/` - List all lessons
- `POST /api/lessons/` - Create new lesson

### Quiz Management

- `GET /api/quizzes/` - List all quizzes
- `POST /api/quizzes/` - Submit quiz results

### Progress Tracking

- `GET /api/progress/` - Get student progress
- `POST /api/progress/` - Update progress

## 🔌 WebSocket Communication

The WebSocket connection at `ws://localhost:8000/ws/teacher/` handles real-time communication for:

- **Lesson Generation**: AI creates lessons step-by-step
- **Whiteboard Commands**: Dynamic visualization updates
- **Interactive Learning**: Progressive content delivery
- **Quiz & Notes Generation**: End-of-lesson content creation

### Message Flow

**Client → Server:**

```json
{
  "topic": "lesson_topic",
  "pdf_text": "extracted_pdf_content"
}
```

**Server → Client:**

```json
{
  "type": "lesson_step",
  "data": {
    "text_explanation": "Step explanation for students",
    "tts_text": "Text optimized for voice synthesis",
    "whiteboard_commands": [
      {
        "action": "write_text",
        "text": "Hello World",
        "x_percent": 50,
        "y_percent": 30,
        "font_size": 24,
        "color": "black"
      }
    ]
  }
}
```

## 📋 Usage Flow

1. **Upload PDF**: Students upload educational PDFs through the drag-and-drop interface
2. **PDF Processing**: Backend extracts text content and prepares for AI processing
3. **AI Lesson Generation**: Google Gemini AI creates interactive step-by-step lessons
4. **Real-time Learning**: Students follow along with dynamic whiteboard visualizations
5. **Interactive Quizzes**: AI generates relevant quizzes based on lesson content
6. **Notes & Downloads**: Students can download lesson slides and notes as PDFs

## 🗄️ Database Schema

### MongoDB Collections

**Students Collection:**

```json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string",
  "password_hash": "string",
  "created_at": "datetime"
}
```

**Lessons Collection:**

```json
{
  "_id": "ObjectId",
  "student_id": "string",
  "pdf_data": "object",
  "llm_output": "object",
  "topic": "string",
  "created_at": "datetime"
}
```

**Quizzes Collection:**

```json
{
  "_id": "ObjectId",
  "student_id": "string",
  "lesson_id": "string",
  "questions": "array",
  "score": "number",
  "time_taken": "string",
  "attempted_at": "datetime"
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**

   - Ensure Daphne server is running on port 8000
   - Check firewall settings
   - Verify WebSocket URL in frontend code

2. **PDF Upload Issues**

   - Check file size (max 50MB)
   - Ensure file is valid PDF format
   - Verify CORS settings in Django

3. **MongoDB Connection Issues**

   - Ensure MongoDB service is running
   - Check connection string in settings.py
   - Verify database permissions

4. **AI Generation Issues**
   - Verify Google API key is valid and active
   - Check API quota and rate limits
   - Ensure stable internet connectivity

## 🧪 Development & Testing

### Backend Testing

```bash
python manage.py test
```

### Frontend Testing

```bash
cd UI/Dashboard/Dashboard
npm test
```

### Development Tips

- Use browser DevTools to monitor WebSocket messages
- Check Django console for backend errors
- Monitor MongoDB logs for database issues
- Use React DevTools for component debugging

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🎓 AI Virtual Teacher

- Interactive topic explanations in simple language
- Whiteboard-style teaching with **voice + diagrams**
- Step-by-step breakdown of concepts

### 📚 Study Material Support

- Upload PDFs or notes
- AI extracts and explains content
- Summarization + Q&A on uploaded materials

### 🔎 Smart Q&A

- Ask questions on any topic
- AI searches within uploaded materials + knowledge base
- Retrieval-Augmented Generation (RAG) for accurate answers

### 👥 User Management

- Secure login system
- Personalized learning environment

---

🛠 **Technology Stack**

- **Frontend:** React + TailwindCSS
- **Backend:** Django + Django Channels (for real-time interaction), Daphene server
- **Database:** MongoDB
- **AI Models:** OpenAI/Generative AI APIs, LangChain
- **Architecture:** Modular + Microservices-ready

---

⚙️ **Installation & Setup**

### Prerequisites

- Python 3.10+
- React
- Django
- Daphne (`pip install daphne`)
- MongoDB

### Steps

```bash
# Clone repository
git clone https://github.com/yourusername/Daphene-Server.git
cd Daphene-Server

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Daphne server
daphne -b 0.0.0.0 -p 8000 yourproject.asgi:application
```

## 👥 Contributors

- [**Aarya Khatate**](https://github.com/aaryaKhatate)
- [**Vinay Gone**](https://github.com/VinayGone2006)
- [**Yashraj Patil**](https://github.com/Yashrajpatil22)

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
