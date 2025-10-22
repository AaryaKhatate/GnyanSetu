@echo off
echo.
echo 🚀 GnyanSetu Complete Flow Test
echo ===============================
echo.

REM Check if MongoDB is running
echo 🔍 Checking MongoDB...
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('✅ MongoDB is running')" 2>nul
if errorlevel 1 (
    echo ❌ MongoDB is not running!
    echo Please start MongoDB first.
    pause
    exit /b 1
)

cd /d "%~dp0"

REM Stop existing services
echo 🧹 Stopping existing services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 "') do taskkill /f /pid %%a >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo 🚀 Starting services for complete flow test...
echo.

REM Start PDF Service
echo 📄 Starting PDF Service (port 8001)...
start "PDF Service - Watch Terminal!" cmd /k "cd /d "%~dp0\pdf-service" && echo 📄 PDF SERVICE STARTING... && echo ⚠️  WATCH THIS TERMINAL FOR BEAUTIFUL PDF DATA OUTPUT! && echo. && python app.py"
timeout /t 3 /nobreak >nul

REM Start User Service
echo 👤 Starting User Service (port 8002)...
start "User Service" cmd /k "cd /d "%~dp0\user-service" && echo 👤 USER SERVICE STARTING... && python app.py"
timeout /t 3 /nobreak >nul

REM Start Landing Page
echo 🏠 Starting Landing Page (port 3000)...
cd /d "%~dp0\..\virtual_teacher_project\UI\landing_page\landing_page"
if exist "package.json" (
    start "Landing Page" cmd /k "echo 🏠 LANDING PAGE STARTING... && npm start"
) else (
    echo ⚠️  Landing page not found
)
timeout /t 3 /nobreak >nul

REM Start Dashboard
echo 🌐 Starting Dashboard (port 3001)...
cd /d "%~dp0\..\virtual_teacher_project\UI\Dashboard\Dashboard"
if exist "package.json" (
    start "Dashboard" cmd /k "echo 🌐 DASHBOARD STARTING... && npm start"
) else (
    echo ⚠️  Dashboard not found
)
timeout /t 5 /nobreak >nul

cd /d "%~dp0"

echo.
echo ⏳ Waiting for all services to fully start...
timeout /t 10 /nobreak >nul

echo.
echo 🧪 Running automated tests...
python test_complete_flow.py

echo.
echo 📋 Service URLs:
echo    🏠 Landing Page:  http://localhost:3000 (Sign up here)
echo    🌐 Dashboard:     http://localhost:3001 (Upload PDFs here)
echo    👤 User Service:  http://localhost:8002/health
echo    📄 PDF Service:   http://localhost:8001/health
echo.

echo 💡 Manual Testing Flow:
echo    1. Open http://localhost:3000 in browser
echo    2. Sign up with new account or log in
echo    3. You'll be redirected to Dashboard (port 3001)
echo    4. Upload a PDF file using the upload box
echo    5. Watch the PDF Service terminal for beautiful colored output!
echo    6. The PDF data will be stored with unique ID for lesson generation
echo.

echo 🎯 IMPORTANT: Watch the PDF Service terminal window!
echo    It will show beautiful colored output when PDFs are processed.
echo.

pause