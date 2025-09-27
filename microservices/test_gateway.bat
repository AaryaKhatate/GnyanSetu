@echo off
REM API Gateway Test Runner for GnyanSetu Microservices
REM This script tests the complete authentication flow through the API Gateway

echo.
echo 🧪 GnyanSetu API Gateway Test Suite
echo ====================================
echo.

REM Check if we're in the right directory
if not exist "api-gateway" (
    echo ❌ Error: This script must be run from the microservices directory
    echo    Expected to find: api-gateway, pdf-service, user-service folders
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "..\virtual_teacher_project\venv\Scripts\activate.bat" (
    echo 🐍 Activating Python virtual environment...
    call "..\virtual_teacher_project\venv\Scripts\activate.bat"
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  Virtual environment not found. Using system Python.
)

echo.
echo 📋 Pre-Test Checklist:
echo    1. Ensure all services are running (run start_project.bat first)
echo    2. API Gateway should be on port 8000
echo    3. User Service should be on port 8002
echo    4. PDF Service should be on port 8001
echo.

REM Wait for user confirmation
set /p confirm="🤔 Are all services running? (y/n): "
if /i not "%confirm%"=="y" (
    echo.
    echo 💡 Please start the services first using: start_project.bat
    echo    Then run this test script again.
    echo.
    pause
    exit /b 1
)

echo.
echo 🚀 Starting API Gateway Tests...
echo.

REM Install required packages for testing
echo 📦 Installing test dependencies...
pip install -q requests

echo.
echo 🔍 Running comprehensive API Gateway tests...
echo.

REM Run the test script
python test_api_gateway.py

echo.
echo 📝 Test completed. Check the results above.
echo.

REM Additional manual test suggestions
echo 💡 Manual Testing Suggestions:
echo    1. Open browser to http://localhost:3000 (Landing Page)
echo    2. Try to sign up with a new user
echo    3. Try to log in with the test user
echo    4. Open http://localhost:3001 (Dashboard)
echo    5. Check if authentication works across both frontends
echo.

pause