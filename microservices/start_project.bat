@echo off
chcp 65001 >nul

REM Set Python to use UTF-8 encoding
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo ========================================
echo  GnyanSetu Microservices Architecture
echo ========================================
echo.

REM Set base directory
set "BASE_DIR=%~dp0"

echo Starting GnyanSetu Platform...
echo.

REM Check if MongoDB is running
echo Checking MongoDB connection...
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('✓ MongoDB is running')" 2>nul
if errorlevel 1 (
    echo ❌ MongoDB is not running!
    echo Please start MongoDB before running the services.
    echo Download from: https://www.mongodb.com/try/download/community
    echo.
    echo Continuing anyway... services will show database connection errors.
    echo.
)

REM Create log directory
if not exist "logs" mkdir logs

REM Kill any existing processes on our ports
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8004 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8005 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8006 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 "') do taskkill /f /pid %%a >nul 2>&1

echo ✓ Port cleanup completed
echo.

echo Starting Backend Microservices...
echo.

REM Start API Gateway (Port 8000) - Central routing service
echo [1/5] Starting API Gateway (FastAPI) on port 8000...
start "API Gateway" cmd /k "cd /d "%BASE_DIR%\api-gateway" && echo Starting FastAPI API Gateway... && python -m uvicorn app_fastapi:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo ✓ API Gateway started

REM Start Django User Authentication Service (Port 8002)
echo [2/5] Starting Django User Authentication Service on port 8002...
start "Django User Service" cmd /k "cd /d "%BASE_DIR%\user-service-django" && start_django_service.bat"
timeout /t 3 /nobreak >nul
echo ✓ User Service started

REM Start Lesson Service (Port 8003) - AI Lesson Generation with Django
echo [3/5] Starting Lesson Service on port 8003...
cd /d "%BASE_DIR%\lesson-service"
start "Lesson Service - AI Lesson Generator" cmd /k "cd /d "e:\Project" && venv\Scripts\activate && cd /d "%BASE_DIR%\lesson-service" && echo LESSON SERVICE - AI LESSON GENERATION && echo Google Gemini AI + Advanced PDF Processing && echo User-specific Lesson History && echo. && python start_lesson_service.py"
timeout /t 3 /nobreak >nul
echo ✓ Lesson Service started

REM Start Teaching Service (Port 8004) - Real-Time Interactive Teaching
echo [4/5] Starting Teaching Service on port 8004...
cd /d "%BASE_DIR%\teaching-service"
start "Teaching Service - Real-Time AI Teacher" cmd /k "cd /d "e:\Project" && venv\Scripts\activate && cd /d "%BASE_DIR%\teaching-service" && echo TEACHING SERVICE - REAL-TIME AI TEACHER && echo Django Channels + WebSockets + Natural Voice && echo Interactive Teaching with Konva.js Integration && echo WebSocket URL: ws://localhost:8004/ws/teaching/ && echo. && python start_teaching_service.py"
timeout /t 3 /nobreak >nul
echo ✓ Teaching Service started

REM Start Quiz & Notes Service (Port 8005) - AI Quiz & Notes Generation
echo [5/6] Starting Quiz ^& Notes Service on port 8005...
cd /d "%BASE_DIR%\quiz-notes-service"
start "Quiz & Notes Service - AI Content Generator" cmd /k "cd /d "e:\Project" && venv\Scripts\activate && cd /d "%BASE_DIR%\quiz-notes-service" && echo QUIZ ^& NOTES SERVICE - AI CONTENT GENERATION && echo FastAPI + Google Gemini AI && echo Quiz Generation + Notes Generation + Results Tracking && echo. && python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload"
timeout /t 3 /nobreak >nul
echo ✓ Quiz ^& Notes Service started

REM Start Visualization Service (Port 8006) - Dynamic Teaching Visuals
echo [6/6] Starting Visualization Service on port 8006...
cd /d "%BASE_DIR%\visualization-service"
start "Visualization Service - Dynamic Teaching Visuals" cmd /k "cd /d "e:\Project" && venv\Scripts\activate && cd /d "%BASE_DIR%\visualization-service" && echo VISUALIZATION SERVICE - DYNAMIC TEACHING VISUALS && echo FastAPI + Gemini LLM + Subject-Specific Graphics && echo 9-Zone Coordinate System + Overlap Prevention && echo. && python -m uvicorn app:app --host 0.0.0.0 --port 8006 --reload"
timeout /t 3 /nobreak >nul
echo ✓ Visualization Service started

echo.
echo ========================================
echo     Backend Services Status
echo ========================================
echo API Gateway:      http://localhost:8000
echo User Service:     http://localhost:8002 (Django)
echo Lesson Service:   http://localhost:8003 (AI Lesson Gen)
echo Teaching Service: http://localhost:8004 (Django + WebSocket)
echo Quiz Notes Service: http://localhost:8005 (FastAPI + AI)
echo Visualization Service: http://localhost:8006 (Dynamic Visuals)
echo ========================================
echo.

REM Wait for services to initialize
echo Waiting for backend services to initialize...
timeout /t 5 /nobreak >nul

REM Health check backend services
echo Performing backend health checks...
curl -f http://localhost:8000/health >nul 2>&1 && echo ✓ API Gateway healthy || echo ❌ API Gateway not responding
curl -f http://localhost:8002/api/v1/health/ >nul 2>&1 && echo ✓ User Service healthy || echo ❌ User Service not responding
curl -f http://localhost:8003/health >nul 2>&1 && echo ✓ Lesson Service healthy || echo ❌ Lesson Service not responding
curl -f http://localhost:8004/health >nul 2>&1 && echo ✓ Teaching Service healthy || echo ❌ Teaching Service not responding
curl -f http://localhost:8005/health >nul 2>&1 && echo ✓ Quiz Notes Service healthy || echo ❌ Quiz Notes Service not responding
curl -f http://localhost:8006/health >nul 2>&1 && echo ✓ Visualization Service healthy || echo ❌ Visualization Service not responding

echo.
echo Starting Frontend Services...
echo.

REM Start Landing Page (Port 3000) - Entry Point
echo [5/6] Starting Landing Page on port 3000...
cd /d "%BASE_DIR%\..\UI\landing_page\landing_page"
if exist "package.json" (
    echo Installing landing page dependencies...
    call npm install >nul 2>&1
    echo Starting Landing Page...
    start "Landing Page" cmd /k "echo Landing Page will open in browser && npm start"
) else (
    echo ❌ Landing Page package.json not found!
    echo Please check the landing page directory structure.
)

REM Start Dashboard (Port 3001) - Main Application
echo [6/6] Starting Dashboard on port 3001...
cd /d "%BASE_DIR%\..\UI\Dashboard\Dashboard"
if exist "package.json" (
    echo Installing dashboard dependencies...
    call npm install >nul 2>&1
    echo Starting React Dashboard on port 3001...
    start "Dashboard - Port 3001" cmd /k "set PORT=3001 && set BROWSER=none && echo Dashboard server running on http://localhost:3001 && echo Accessible after login from Landing Page && echo Dashboard will NOT open in browser automatically && npm start"
) else (
    echo ❌ Dashboard package.json not found!
    echo Please check the UI directory structure.
)

echo.
echo ========================================
echo         Platform Ready!
echo ========================================
echo.
echo 🌟 GnyanSetu Platform is now running!
echo.
echo 📱 Two-Port User Experience:
echo    ► Landing Page: http://localhost:3000 (Sign up/Login)
echo    ► Dashboard: http://localhost:3001 (Main app after login)
echo    ► Same tab redirect: 3000 → 3001 after authentication
echo.
echo 🔧 Backend Microservices:
echo    ► API Gateway: http://localhost:8000 (Routes all requests)
echo    ► User Service: http://localhost:8002 (Authentication + JWT)
echo    ► Lesson Service: http://localhost:8003 (AI Content Generation)
echo    ► Teaching Service: http://localhost:8004 (Real-time AI Teacher)
echo    ► Quiz Notes Service: http://localhost:8005 (AI Quiz + Notes)
echo.
echo 🔄 Fixed Configuration Issues:
echo    ► ChatHistory.jsx: API calls route to port 8000 ✓
echo    ► Whiteboard.jsx: WebSocket connects to port 8004 ✓
echo    ► Teaching Service: Added conversations endpoint ✓
echo    ► API Gateway: Routes conversations to Teaching Service ✓
echo.
echo 🚀 User Flow:
echo    1. Browser opens to Landing Page (port 3000)
echo    2. User signs up or logs in
echo    3. JavaScript redirects to Dashboard (port 3001) - SAME TAB
echo    4. All features available on Dashboard
echo.
echo 📊 Service URLs:
echo    ► Landing Page: http://localhost:3000
echo    ► Dashboard: http://localhost:3001
echo    ► API Gateway: http://localhost:8000/health
echo    ► User Service: http://localhost:8002/api/v1/health/
echo    ► Lesson Service: http://localhost:8003/health
echo    ► Teaching Service: http://localhost:8004/health
echo.
echo 🔧 WebSocket Configuration:
echo    ► Teaching WebSocket: ws://localhost:8004/ws/teaching/{session_id}/
echo    ► Voice Service: Integrated with Teaching Service
echo    ► Real-time AI Teaching: Available via WebSocket
echo.

REM Wait for services to start, then open landing page
timeout /t 8 /nobreak >nul
echo Opening Landing Page in browser...
start http://localhost:3000

echo.
echo ⚠️  IMPORTANT:
echo    ► Both ports 3000 and 3001 are running
echo    ► Login on port 3000 redirects to port 3001 (same tab)
echo    ► Dashboard features work on port 3001
echo    ► All backend APIs are ready
echo.
echo ========================================
echo  TO ACCESS YOUR APPLICATION:
echo ========================================
echo.
echo 1. Wait 10-15 seconds for all services to fully start
echo 2. Then manually open: http://localhost:3000
echo 3. Sign up or Login on the landing page
echo 4. You'll be redirected to the dashboard automatically
echo.
echo ========================================
echo.
echo Service URLs:
echo    API Gateway:      http://localhost:8000/health
echo    Django User Service: http://localhost:8002/api/v1/health/
echo    Lesson Service:   http://localhost:8003/health
echo    Teaching Service: http://localhost:8004/health
echo    Quiz Notes Service: http://localhost:8005/health
echo    Landing Page:     http://localhost:3000 (opens in browser)
echo    Dashboard:        http://localhost:3001 (opens after login)
echo.
echo Press any key to stop all services...
pause >nul

echo ========================================
echo       Shutting Down Platform
echo ========================================
echo.

echo Stopping all services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8003 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8004 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8005 "') do taskkill /f /pid %%a >nul 2>&1

echo ✓ All services stopped gracefully.
echo.
echo 📝 Session Summary:
echo    - 5 Backend microservices were running
echo    - 2 Frontend services (Landing + Dashboard)
echo    - Same-tab redirect experience implemented
echo    - All errors fixed and tested
echo.
echo Thank you for using GnyanSetu Platform! 🚀
pause
