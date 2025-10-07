@echo off
echo.
echo ========================================
echo  GnyanSetu Dashboard Launcher
echo ========================================
echo.

REM Set base directory
set "BASE_DIR=%~dp0"

REM Check if port 3001 is already in use
netstat -an | find "3001" | find "LISTENING" >nul
if %errorlevel%==0 (
    echo ✅ Dashboard is already running on port 3001
    echo 🌐 Dashboard URL: http://localhost:3001
    echo.
    echo Opening Dashboard in browser...
    start "" http://localhost:3001
    exit /b 0
)

echo 🔐 Starting authenticated Dashboard on port 3001...
cd /d "%BASE_DIR%\..\virtual_teacher_project\UI\Dashboard\Dashboard"

if exist "package.json" (
    echo Installing dashboard dependencies...
    call npm install >nul 2>&1
    echo Starting React Dashboard on port 3001...
    set PORT=3001
    echo.
    echo ✅ Dashboard starting on port 3001...
    echo 🌐 Dashboard URL: http://localhost:3001
    echo 🔐 Dashboard accessible after login from Landing Page
    echo.
    echo ⚠️  Keep this window open to keep the dashboard running!
    echo.
    timeout /t 2 /nobreak >nul
    echo Opening Dashboard in browser...
    start "" http://localhost:3001
    npm start
) else (
    echo ⚠️  Dashboard package.json not found!
    echo Please check the UI directory structure.
    echo.
    echo Press any key to continue...
    pause >nul
)