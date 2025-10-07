@echo off
cd /d e:\Project\GnyanSetu\virtual_teacher_project
echo Starting GnyanSetu Virtual Teacher Platform...

echo.
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Setting up environment...
if not exist .env (
    echo Creating .env file...
    echo GOOGLE_API_KEY=your_google_api_key_here > .env
    echo Please add your Google API key to the .env file before running.
    pause
)

echo.
echo [3/3] Starting Django with Daphne ASGI server...
echo Server will be available at: http://localhost:8000
echo WebSocket will be available at: ws://localhost:8000/ws/teacher/
echo.

daphne -b 0.0.0.0 -p 8000 virtual_teacher_project.asgi:application
