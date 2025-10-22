@echo off
echo.
echo 🔧 Quick Authentication Test Setup
echo ==================================
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

REM Kill existing services
echo 🧹 Stopping existing services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 "') do taskkill /f /pid %%a >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo 🚀 Starting required services for authentication test...
echo.

REM Start User Service
echo 👤 Starting User Service (port 8002)...
start "User Service" cmd /k "cd /d "%~dp0\user-service" && echo Starting User Service... && python app.py"
timeout /t 3 /nobreak >nul

REM Start API Gateway  
echo 🌐 Starting API Gateway (port 8000)...
start "API Gateway" cmd /k "cd /d "%~dp0\api-gateway" && echo Starting API Gateway... && python app.py"
timeout /t 3 /nobreak >nul

echo.
echo ⏳ Waiting for services to fully start...
timeout /t 5 /nobreak >nul

echo.
echo 🧪 Running authentication tests...
python test_user_auth.py

echo.
echo 📋 Service URLs:
echo    👤 User Service:  http://localhost:8002/health
echo    🌐 API Gateway:   http://localhost:8000/health
echo    🏠 Landing Page:  http://localhost:3000 (if running)
echo.

pause