@echo off
echo ========================================
echo Starting GnyanSetu (Quick Start)
echo ========================================

:: -------------------------------
:: Step 0 - Start MongoDB
:: -------------------------------
echo.
echo [0/3] Starting MongoDB...
cd /d "e:\Project\GnyanSetu\virtual_teacher_project"
start "MongoDB" cmd /k "mongod.exe --dbpath e:\Project\GnyanSetu\virtual_teacher_project\mongo_data"
timeout /t 5 > nul

:: -------------------------------
:: Step 1 - Start Django Backend
:: -------------------------------
echo.
echo [1/3] Starting Django Backend (ASGI Server)...
echo Backend will run at: http://localhost:8001
cd /d "e:\Project\GnyanSetu\virtual_teacher_project"
start "GnyanSetu Backend" powershell -ExecutionPolicy Bypass -File "e:\Project\GnyanSetu\virtual_teacher_project\start_asgi.ps1"

echo.
echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

:: -------------------------------
:: Step 2 - Start Dashboard (React on 3001)
:: -------------------------------
echo.
echo [2/3] Starting Dashboard...
echo Dashboard will run at: http://localhost:3001
cd /d "e:\Project\GnyanSetu\virtual_teacher_project\UI\dashboard\dashboard"
:: Set port to 3001 explicitly
set PORT=3001
set BROWSER=none
start "GnyanSetu Dashboard" cmd /k "npm start"

echo.
echo Waiting 3 seconds for dashboard to start...
timeout /t 3 /nobreak > nul

:: -------------------------------
:: Step 3 - Start Landing Page (React on 3000)
:: -------------------------------
echo.
echo [3/3] Starting Landing Page...
echo Landing Page will run at: http://localhost:3000
cd /d "e:\Project\GnyanSetu\virtual_teacher_project\UI\landing_page\landing_page"
:: Set port to 3000 explicitly
set PORT=3000
set BROWSER=none
start "GnyanSetu Landing" cmd /k "npm start"

echo.
echo Waiting 5 seconds for landing page to start...
timeout /t 5 /nobreak > nul

:: -------------------------------
:: Step 4 - Open Landing Page in Browser
:: -------------------------------
echo.
echo Opening Landing Page in browser...
start http://localhost:3000

:: -------------------------------
:: Step 5 - Summary
:: -------------------------------
echo.
echo ========================================
echo ✅ GnyanSetu is starting up!
echo ========================================
echo.
echo 🌐 Access Points:
echo   Landing Page: http://localhost:3000
echo   Dashboard:    http://localhost:3001
echo   Backend:      http://localhost:8001
echo.
echo 📝 Note: Three terminal windows will open
echo.
echo Press any key to close this window...
pause > nul
