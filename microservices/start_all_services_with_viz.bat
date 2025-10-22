@echo off
echo ========================================
echo   GnyanSetu - Complete System Startup
echo   WITH VISUALIZATION SYSTEM
echo ========================================
echo.

echo Starting all microservices...
echo.

REM Check if MongoDB is running
echo Checking MongoDB...
sc query MongoDB | find "RUNNING" >nul
if errorlevel 1 (
    echo MongoDB is not running. Starting MongoDB...
    net start MongoDB
    timeout /t 3 >nul
) else (
    echo MongoDB is already running.
)
echo.

REM Start API Gateway
echo [1/6] Starting API Gateway (Port 8000)...
start "API Gateway" cmd /k "cd api-gateway && python app.py"
timeout /t 3 >nul

REM Start User Service
echo [2/6] Starting User Service (Port 8002)...
start "User Service" cmd /k "cd user-service && python manage.py runserver 0.0.0.0:8002"
timeout /t 3 >nul

REM Start Lesson Service
echo [3/6] Starting Lesson Service (Port 8003)...
start "Lesson Service" cmd /k "cd lesson-service && python manage.py runserver 0.0.0.0:8003"
timeout /t 3 >nul

REM Start Teaching Service (FastAPI)
echo [4/6] Starting Teaching Service (Port 8004)...
start "Teaching Service" cmd /k "cd teaching-service && python app_fastapi.py"
timeout /t 3 >nul

REM Start Quiz/Notes Service
echo [5/6] Starting Quiz/Notes Service (Port 8005)...
start "Quiz Service" cmd /k "cd quiz-service && python manage.py runserver 0.0.0.0:8005"
timeout /t 3 >nul

REM Start Visualization Orchestrator (NEW)
echo [6/6] Starting Visualization Orchestrator (Port 8006)...
start "Visualization Service" cmd /k "cd visualization-service && python app.py"
timeout /t 3 >nul

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo Service Status:
echo   API Gateway          : http://localhost:8000
echo   User Service         : http://localhost:8002
echo   Lesson Service       : http://localhost:8003
echo   Teaching Service     : http://localhost:8004
echo   Quiz/Notes Service   : http://localhost:8005
echo   Visualization Service: http://localhost:8006
echo.
echo Check health: 
echo   curl http://localhost:8000/health
echo   curl http://localhost:8006/health
echo.
echo View Visualization API docs:
echo   http://localhost:8006/docs
echo.
echo Press any key to check service status...
pause >nul

REM Check all services
echo.
echo Checking service health...
echo.

curl -s http://localhost:8000/health >nul && echo [OK] API Gateway || echo [FAIL] API Gateway
curl -s http://localhost:8002/health >nul && echo [OK] User Service || echo [FAIL] User Service
curl -s http://localhost:8003/health >nul && echo [OK] Lesson Service || echo [FAIL] Lesson Service
curl -s http://localhost:8004/health >nul && echo [OK] Teaching Service || echo [FAIL] Teaching Service
curl -s http://localhost:8005/health >nul && echo [OK] Quiz Service || echo [FAIL] Quiz Service
curl -s http://localhost:8006/health >nul && echo [OK] Visualization Service || echo [FAIL] Visualization Service

echo.
echo ========================================
echo   System Ready with Visualization!
echo ========================================
echo.
pause
