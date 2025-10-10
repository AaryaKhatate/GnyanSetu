@echo off
REM Django User Authentication Service Startup Helper
REM Called from main start_project.bat

echo ============================================
echo  DJANGO USER AUTHENTICATION SERVICE
echo  JWT Tokens + User Management + Email Verification  
echo  Django REST Framework + MongoDB Integration
echo ============================================
echo.

REM Set base paths
set "VENV_PATH=e:\Project\venv\Scripts\activate"
set "DJANGO_PATH=e:\Project\GnyanSetu\microservices\user-service-django"

REM Check if virtual environment exists
if not exist "%VENV_PATH%" (
    echo ERROR: Virtual environment not found at %VENV_PATH%
    pause
    exit /b 1
)

REM Check if Django directory exists
if not exist "%DJANGO_PATH%" (
    echo ERROR: Django directory not found at %DJANGO_PATH%
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "%VENV_PATH%"

REM Navigate to Django service directory
echo Changing to Django directory...
cd /d "%DJANGO_PATH%"

REM Check if manage.py exists
if not exist "manage.py" (
    echo ERROR: manage.py not found in %DJANGO_PATH%
    pause
    exit /b 1
)

REM Start Django development server
echo Starting Django server on port 8002...
echo Service will be available at: http://127.0.0.1:8002/
echo Health check: http://127.0.0.1:8002/api/v1/health/
echo Admin panel: http://127.0.0.1:8002/admin/
echo.
python manage.py runserver 8002