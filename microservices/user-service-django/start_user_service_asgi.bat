@echo off
REM GnyanSetu User Authentication Service - Production ASGI Server
REM Port: 8002
REM Server: Daphne ASGI Server

echo ============================================
echo  GnyanSetu User Authentication Service
echo  Production ASGI Server (Daphne) - Port 8002  
echo ============================================

REM Activate virtual environment
echo Activating virtual environment...
cd /d "e:\Project"
call venv\Scripts\activate

REM Navigate to user service directory
echo Navigating to user service...
cd "Gnyansetu_Updated_Architecture\microservices\user-service-django"

REM Enable Daphne in settings
echo Enabling ASGI configuration...
python -c "
import os
settings_path = 'user_service/settings.py'
with open(settings_path, 'r') as f:
    content = f.read()
content = content.replace(\"# 'daphne',  # ASGI server for production - commented for initial testing\", \"'daphne',  # ASGI server for production\")
with open(settings_path, 'w') as f:
    f.write(content)
print('ASGI configuration enabled')
"

REM Check for migrations
echo Checking database migrations...
python manage.py makemigrations
python manage.py migrate

REM Start Daphne ASGI server
echo Starting Daphne ASGI server...
echo.
echo Service will be available at:
echo   - API Root: http://localhost:8002/
echo   - Health Check: http://localhost:8002/api/v1/health/
echo   - Authentication: http://localhost:8002/api/v1/auth/
echo   - Admin Panel: http://localhost:8002/admin/
echo.
echo Press Ctrl+C to stop the server
echo ============================================

daphne -b 0.0.0.0 -p 8002 user_service.asgi:application

pause