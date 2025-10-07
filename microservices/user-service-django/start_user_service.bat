@echo off
REM GnyanSetu User Authentication Service Startup Script
REM Port: 8002
REM Purpose: Complete Django authentication service with JWT, REST API, and user management

echo ============================================
echo  GnyanSetu User Authentication Service
echo  Starting Django Server on Port 8002
echo ============================================

REM Activate virtual environment
echo Activating virtual environment...
cd /d "e:\Project"
call venv\Scripts\activate

REM Navigate to user service directory
echo Navigating to user service...
cd "Gnyansetu_Updated_Architecture\microservices\user-service-django"

REM Check for migrations
echo Checking database migrations...
python manage.py makemigrations
python manage.py migrate

REM Start Django development server
echo Starting Django user authentication service...
echo.
echo Service will be available at:
echo   - API Root: http://localhost:8002/
echo   - Health Check: http://localhost:8002/api/v1/health/
echo   - Authentication: http://localhost:8002/api/v1/auth/
echo   - Admin Panel: http://localhost:8002/admin/
echo.
echo Press Ctrl+C to stop the server
echo ============================================

python manage.py runserver 8002

pause