@echo off
cd /d e:\Project\GnyanSetu\virtual_teacher_project
echo ================================
echo  GyanSetu - Complete Development Setup
echo ================================
echo.
echo This script will start:
echo 1. Django Backend (Port 8000)
echo 2. Dashboard Frontend (Port 3001)  
echo 3. Landing Page Frontend (Port 3000)
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo Starting Django Backend...
start "Django Backend" cmd /k "python manage.py runserver 8000"

echo Waiting for backend to start...
timeout /t 3 >nul

echo.
echo Starting Dashboard Frontend...
start "Dashboard Frontend" cmd /k "cd UI\Dashboard\Dashboard && set BROWSER=none && set PORT=3001 && npm start"

echo Waiting for dashboard to start...
timeout /t 3 >nul

echo.
echo Starting Landing Page Frontend...
start "Landing Page Frontend" cmd /k "cd \"UI\landing_page\landing_page\" && set BROWSER=none && npm start"

echo.
echo Waiting 5 seconds for all services to start...
timeout /t 5 >nul

echo.
echo Opening Landing Page in browser...
start http://localhost:3000

echo.
echo ================================
echo  All services starting...
echo ================================
echo.
echo URLs:
echo - Backend API: http://localhost:8000
echo - Dashboard: http://localhost:3001
echo - Landing Page: http://localhost:3000
echo.
echo Press any key to exit this window...
pause >nul
