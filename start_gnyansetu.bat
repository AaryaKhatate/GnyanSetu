@echo off
REM ============================================================================
REM GnyanSetu AI Virtual Teacher Platform - Production Startup Script
REM ============================================================================
REM This script starts all microservices and UI components for hosting
REM ============================================================================

echo.
echo ============================================================================
echo                   GNYANSETU AI VIRTUAL TEACHER PLATFORM
echo                         Production Startup Script
echo ============================================================================
echo.

REM Set the root directory
set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

echo [INFO] Root Directory: %ROOT_DIR%
echo.

REM ============================================================================
REM STEP 1: Check if MongoDB is running
REM ============================================================================
echo [STEP 1/4] Checking MongoDB...
echo ----------------------------------------------------------------------------
timeout /t 2 /nobreak >nul

tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MongoDB is running
) else (
    echo [WARNING] MongoDB is not running!
    echo [INFO] Please start MongoDB manually or ensure it's running as a service
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 goto :end
)
echo.

REM ============================================================================
REM STEP 2: Start All Microservices
REM ============================================================================
echo [STEP 2/4] Starting Microservices...
echo ----------------------------------------------------------------------------

cd /d "%ROOT_DIR%microservices"

REM Start API Gateway (Port 8000)
echo [1/7] Starting API Gateway (Port 8000)...
start "API Gateway - Port 8000" cmd /k "cd /d api-gateway && python app.py"
timeout /t 3 /nobreak >nul

REM Start User Service (Port 8002)
echo [2/7] Starting User Service (Port 8002)...
start "User Service - Port 8002" cmd /k "cd /d user-service-django && python manage.py runserver 8002"
timeout /t 3 /nobreak >nul

REM Start Lesson Service (Port 8003)
echo [3/7] Starting Lesson Service (Port 8003)...
start "Lesson Service - Port 8003" cmd /k "cd /d lesson-service && python manage.py runserver 8003"
timeout /t 3 /nobreak >nul

REM Start Teaching Service (Port 8004)
echo [4/7] Starting Teaching Service (Port 8004)...
start "Teaching Service - Port 8004" cmd /k "cd /d teaching-service && python app_fastapi.py"
timeout /t 3 /nobreak >nul

REM Start Quiz Notes Service (Port 8005)
echo [5/7] Starting Quiz Notes Service (Port 8005)...
start "Quiz Notes Service - Port 8005" cmd /k "cd /d quiz-notes-service && python main.py"
timeout /t 3 /nobreak >nul

REM Start Visualization Service (Port 8006)
echo [6/7] Starting Visualization Service (Port 8006)...
start "Visualization Service - Port 8006" cmd /k "cd /d visualization-service && python app.py"
timeout /t 3 /nobreak >nul

REM Start PDF Service (Port 8007)
echo [7/7] Starting PDF Service (Port 8007)...
start "PDF Service - Port 8007" cmd /k "cd /d pdf-service && python app.py"
timeout /t 3 /nobreak >nul

echo.
echo [OK] All microservices started!
echo.

REM ============================================================================
REM STEP 3: Start Frontend - Landing Page (Port 3000)
REM ============================================================================
echo [STEP 3/4] Starting Landing Page (Port 3000)...
echo ----------------------------------------------------------------------------

cd /d "%ROOT_DIR%UI\landing_page\landing_page"

if exist "node_modules\" (
    echo [OK] Dependencies found
) else (
    echo [INFO] Installing dependencies...
    call npm install
)

start "Landing Page - Port 3000" cmd /k "npm start"
timeout /t 5 /nobreak >nul

echo [OK] Landing Page started on http://localhost:3000
echo.

REM ============================================================================
REM STEP 4: Start Frontend - Dashboard (Port 3001)
REM ============================================================================
echo [STEP 4/4] Starting Dashboard (Port 3001)...
echo ----------------------------------------------------------------------------

cd /d "%ROOT_DIR%UI\Dashboard\Dashboard"

if exist "node_modules\" (
    echo [OK] Dependencies found
) else (
    echo [INFO] Installing dependencies...
    call npm install
)

start "Dashboard - Port 3001" cmd /k "set PORT=3001 && npm start"
timeout /t 5 /nobreak >nul

echo [OK] Dashboard started on http://localhost:3001
echo.

REM ============================================================================
REM Startup Complete
REM ============================================================================
echo ============================================================================
echo                         STARTUP COMPLETE!
echo ============================================================================
echo.
echo All services are now running:
echo.
echo MICROSERVICES:
echo   [1] API Gateway           : http://localhost:8000
echo   [2] User Service          : http://localhost:8002
echo   [3] Lesson Service        : http://localhost:8003
echo   [4] Teaching Service      : http://localhost:8004
echo   [5] Quiz Notes Service    : http://localhost:8005
echo   [6] Visualization Service : http://localhost:8006
echo   [7] PDF Service           : http://localhost:8007
echo.
echo FRONTEND:
echo   [8] Landing Page          : http://localhost:3000
echo   [9] Dashboard             : http://localhost:3001
echo.
echo ============================================================================
echo.
echo [INFO] To access the application:
echo   1. Landing Page: http://localhost:3000
echo   2. Dashboard:    http://localhost:3001
echo.
echo [INFO] To stop all services:
echo   - Close all command windows OR
echo   - Press Ctrl+C in each window
echo.
echo [INFO] MongoDB must be running for the services to work properly
echo.
echo ============================================================================

REM Keep this window open
echo.
echo Press any key to view service health status...
pause >nul

REM ============================================================================
REM Service Health Check
REM ============================================================================
echo.
echo ============================================================================
echo                      SERVICE HEALTH CHECK
echo ============================================================================
echo.
echo Checking if services are responding...
echo.

timeout /t 5 /nobreak >nul

curl -s http://localhost:8000 >nul 2>&1
if %errorlevel%==0 (echo [OK] API Gateway is responding) else (echo [WARNING] API Gateway not responding)

curl -s http://localhost:8002 >nul 2>&1
if %errorlevel%==0 (echo [OK] User Service is responding) else (echo [WARNING] User Service not responding)

curl -s http://localhost:8003 >nul 2>&1
if %errorlevel%==0 (echo [OK] Lesson Service is responding) else (echo [WARNING] Lesson Service not responding)

curl -s http://localhost:8004 >nul 2>&1
if %errorlevel%==0 (echo [OK] Teaching Service is responding) else (echo [WARNING] Teaching Service not responding)

curl -s http://localhost:8005 >nul 2>&1
if %errorlevel%==0 (echo [OK] Quiz Notes Service is responding) else (echo [WARNING] Quiz Notes Service not responding)

curl -s http://localhost:8006 >nul 2>&1
if %errorlevel%==0 (echo [OK] Visualization Service is responding) else (echo [WARNING] Visualization Service not responding)

curl -s http://localhost:8007 >nul 2>&1
if %errorlevel%==0 (echo [OK] PDF Service is responding) else (echo [WARNING] PDF Service not responding)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel%==0 (echo [OK] Landing Page is responding) else (echo [WARNING] Landing Page not responding)

curl -s http://localhost:3001 >nul 2>&1
if %errorlevel%==0 (echo [OK] Dashboard is responding) else (echo [WARNING] Dashboard not responding)

echo.
echo ============================================================================
echo Health check complete. All services should be running now.
echo ============================================================================
echo.

:end
echo Press any key to exit...
pause >nul
