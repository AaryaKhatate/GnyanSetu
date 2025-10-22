@echo off
cls
echo ============================================
echo  STARTING DJANGO WITH FRESH CODE
echo  MongoDB Session Storage Enabled
echo ============================================
echo.

cd /d "E:\Project\GnyanSetu\microservices\user-service-django"

echo Activating virtual environment...
call E:\Project\venv\Scripts\activate.bat

echo.
echo Starting Django on port 8002...
echo Press CTRL+C to stop
echo.

python manage.py runserver 8002

pause
