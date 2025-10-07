@echo off
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
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('MongoDB is running')" 2>nul
if errorlevel 1 (
    echo  MongoDB is not running!
    echo Please start MongoDB before running the services.
    echo Download from: https://www.mongodb.com/try/download/community
    echo.
    echo Continuing anyway... services will show database connection errors.
    echo.
)

REM Create log directory
if not exist "logs" mkdir logs

REM Kill any existing processes on our ports (optional)
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 "') do taskkill /f /pid %%a >nul 2>&1

echo.
echo Starting Microservices...
echo.

REM Start API Gateway (Port 8000) - Central routing service
echo Starting API Gateway on port 8000...
start "API Gateway" cmd /k "cd /d "%BASE_DIR%\api-gateway" && echo Starting API Gateway... && python app.py"
timeout /t 3 /nobreak >nul

REM Start Django User Authentication Service (Port 8002)
echo Starting Django User Authentication Service on port 8002...
if not exist "%BASE_DIR%\user-service-django\logs" mkdir "%BASE_DIR%\user-service-django\logs"
start "Django User Service" cmd /k "cd /d "%BASE_DIR%\user-service-django" && echo ============================================ && echo  DJANGO USER AUTHENTICATION SERVICE && echo  JWT Tokens + User Management + Email Verification && echo  Django REST Framework + MongoDB Integration && echo ============================================ && python manage.py runserver 0.0.0.0:8002"
timeout /t 3 /nobreak >nul

REM Start Lesson Service (Port 8003) - AI Lesson Generation with Django
echo Starting Lesson Service on port 8003...
cd /d "%BASE_DIR%\lesson-service"
start "Lesson Service - AI Lesson Generator" cmd /k "cd /d "%BASE_DIR%\lesson-service" && echo LESSON SERVICE - AI LESSON GENERATION && echo Google Gemini AI + Advanced PDF Processing && echo User-specific Lesson History && echo. && python start_lesson_service.py"
timeout /t 3 /nobreak >nul

REM Start Teaching Service (Port 8004) - Real-Time Interactive Teaching
echo Starting Teaching Service on port 8004...
cd /d "%BASE_DIR%\teaching-service"
start "Teaching Service - Real-Time AI Teacher" cmd /k "cd /d "%BASE_DIR%\teaching-service" && echo TEACHING SERVICE - REAL-TIME AI TEACHER && echo Django Channels + WebSockets + Natural Voice && echo Interactive Teaching with Konva.js Integration && echo. && python start_teaching_service.py"
timeout /t 3 /nobreak >nul

REM Start Landing Page (Port 3000) - OPENS IN BROWSER
echo Starting Landing Page on port 3000...
cd /d "%BASE_DIR%\..\virtual_teacher_project\UI\landing_page\landing_page"
if exist "package.json" (
    echo Installing landing page dependencies...
    call npm install >nul 2>&1
    echo Starting Landing Page...
    echo BROWSER=none > .env
    start "Landing Page" cmd /k "echo Landing Page server running on http://localhost:3000 && echo Browser opening disabled - manual access required && npm start"
) else (
    echo Landing Page package.json not found!
    echo Please check the landing page directory structure.
)

timeout /t 3 /nobreak >nul

REM Start Dashboard (Port 3001) - Available after authentication
echo Starting Dashboard on port 3001...
cd /d "%BASE_DIR%\..\virtual_teacher_project\UI\Dashboard\Dashboard"
if exist "package.json" (
    echo Installing dashboard dependencies...
    call npm install >nul 2>&1
    echo Starting React Dashboard on port 3001...
    echo PORT=3001 > .env
    echo BROWSER=none >> .env
    start "Dashboard - Port 3001" cmd /k "echo Dashboard server running on http://localhost:3001 && echo Accessible after login from Landing Page && echo Dashboard will NOT open in browser automatically && npm start"
) else (
    echo  Dashboard package.json not found!
    echo Please check the UI directory structure.
)

timeout /t 3 /nobreak >nul

REM Wait for services to start, then open landing page
timeout /t 8 /nobreak >nul
echo Opening Landing Page in browser...
start http://localhost:3000

echo.
echo All services are starting up!
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
echo    Landing Page:     http://localhost:3000 (opens in browser)
echo    Dashboard:        http://localhost:3001 (opens after login)
echo.
echo Service Health Checks:
echo    API Gateway:      http://localhost:8000/health
echo    Django User Service: http://localhost:8002/api/v1/health/
echo    Lesson Service:   http://localhost:8003/health
echo    Teaching Service: http://localhost:8004/health
echo.
echo Test Services:
echo    Django User Service:  http://localhost:8002/api/v1/auth/
echo    User Admin Panel:     http://localhost:8002/admin/
echo    cd microservices\lesson-service ^&^& python start_lesson_service.py
echo.
echo Application Flow:
echo    1. Landing Page: http://localhost:3000 (Sign up/Login here)
echo    2. After login: Dashboard starts automatically (Upload PDFs)
echo    3. API Gateway: http://localhost:8000 (All API calls)
echo.
echo GnyanSetu Platform is now running!
echo.
echo  Django User Service: Complete authentication with JWT tokens, user management, and email verification!
echo  Lesson Service: Watch the "Lesson Service - AI Lesson Generator" window for AI lesson generation!
echo.
echo Django User Service Features:
echo  - JWT Authentication: http://localhost:8002/api/v1/auth/login/
echo  - User Registration: http://localhost:8002/api/v1/auth/register/
echo  - Admin Panel: http://localhost:8002/admin/
echo.
echo To stop all services, close all command windows or press Ctrl+C in each.
echo.
echo Press any key to continue...
pause >nul