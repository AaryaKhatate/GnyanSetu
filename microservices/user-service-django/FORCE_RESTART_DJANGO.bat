@echo off
echo ============================================
echo  FORCE RESTART DJANGO WITH FRESH CODE
echo ============================================
echo.

echo Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo Clearing Python cache...
cd /d "E:\Project\GnyanSetu\microservices\user-service-django"
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1

echo.
echo Starting Django server...
call E:\Project\venv\Scripts\activate.bat
python manage.py runserver 8002

pause
