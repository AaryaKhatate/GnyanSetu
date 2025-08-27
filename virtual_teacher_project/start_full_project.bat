@echo off
echo ========================================
echo Starting GnyanSetu Full Project
echo ========================================

echo.
echo [1/4] Installing Python dependencies...
cd /d "d:\Virtual-Tutor\virtual_teacher_project"
C:/Python313/python.exe -m pip install -r requirements.txt

echo.
echo [2/4] Checking environment setup...
if not exist .env (
    echo GOOGLE_API_KEY=your_google_api_key_here > .env
    echo [WARNING] Please add your Google API key to the .env file!
    echo Location: d:\Virtual-Tutor\virtual_teacher_project\.env
    pause
)

echo.
echo [3/4] Starting Django Backend (Daphne ASGI Server)...
echo Backend will run at: http://localhost:8000
echo WebSocket will be at: ws://localhost:8000/ws/teacher/
start "GnyanSetu Backend" cmd /k "cd /d d:\Virtual-Tutor\virtual_teacher_project && C:/Python313/python.exe -m daphne -b 0.0.0.0 -p 8000 virtual_teacher_project.asgi:application"

echo.
echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo [4/4] Starting React Frontend...
echo Frontend will run at: http://localhost:3000
cd /d "d:\Virtual-Tutor\virtual_teacher_project\UI\Dashboard\Dashboard"
start "GnyanSetu Frontend" cmd /k "npm install && npm start"

echo.
echo ========================================
echo ✅ GnyanSetu is starting up!
echo ========================================
echo.
echo 🌐 Access Points:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   WebSocket: ws://localhost:8000/ws/teacher/
echo.
echo 📝 Note: Two terminal windows will open:
echo   1. Backend (Django + Daphne)
echo   2. Frontend (React Dev Server)
echo.
echo Press any key to close this window...
pause > nul
