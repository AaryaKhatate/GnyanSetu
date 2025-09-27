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
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('✅ MongoDB is running')" 2>nul
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

REM Start PDF Service (Port 8001) - WATCH FOR BEAUTIFUL OUTPUT!
echo Starting PDF Service on port 8001...
start "PDF Service - WATCH FOR BEAUTIFUL OUTPUT!" cmd /k "cd /d "%BASE_DIR%\pdf-service" && echo 📄 PDF SERVICE - READY TO PROCESS PDFS! && echo ⚠️  WATCH THIS TERMINAL FOR COLORED PDF DATA OUTPUT! && echo 🎨 Beautiful PDF processing logs will appear here! && echo. && python app.py"
timeout /t 3 /nobreak >nul

REM Start User Management Service (Port 8002)
echo Starting User Management Service on port 8002...
start "User Service" cmd /k "cd /d "%BASE_DIR%\user-service" && echo Starting User Management Service... && python app.py"
timeout /t 2 /nobreak >nul

REM Start Landing Page (Port 3000)
echo Starting Landing Page on port 3000...
cd /d "%BASE_DIR%\..\virtual_teacher_project\UI\landing_page\landing_page"
if exist "package.json" (
    echo Installing landing page dependencies...
    call npm install >nul 2>&1
    echo Starting Landing Page...
    start "Landing Page" cmd /k "set BROWSER=none && npm start"
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
    set PORT=3001
    set BROWSER=none
    start "Dashboard - Port 3001" cmd /k "set PORT=3001 && set BROWSER=none && echo 🌐 Dashboard server running on http://localhost:3001 && echo 🔐 Accessible after login from Landing Page && echo ⚠️  Dashboard will NOT open in browser automatically && npm start"
) else (
    echo  Dashboard package.json not found!
    echo Please check the UI directory structure.
)

timeout /t 3 /nobreak >nul

echo.
echo All services are starting up!
echo.
echo Service URLs:
echo    API Gateway:      http://localhost:8000/health
echo    PDF Service:      http://localhost:8001/health
echo    User Service:     http://localhost:8002/health  
echo    Landing Page:     http://localhost:3000
echo    Dashboard:        http://localhost:3001 (after login)
echo.
echo Service Health Checks:
echo    API Gateway:      http://localhost:8000/health
echo    PDF Service:      http://localhost:8001/health
echo    User Service:     http://localhost:8002/health
echo.
echo Test Services:
echo    cd microservices\pdf-service ^&^& python test_service.py
echo    cd microservices\user-service ^&^& python test_service.py
echo.
echo Application Flow:
echo    1. Landing Page: http://localhost:3000 (Sign up/Login here)
echo    2. After login: Dashboard starts automatically (Upload PDFs)
echo    3. API Gateway: http://localhost:8000 (All API calls)
echo.
echo GnyanSetu Platform is now running!
echo.
echo  PDF Service: Watch the "PDF Service - BEAUTIFUL OUTPUT" window for colored PDF processing logs!
echo.
echo To stop all services, close all command windows or press Ctrl+C in each.
echo.
echo Press any key to continue...
pause >nul