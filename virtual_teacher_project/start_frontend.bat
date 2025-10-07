@echo off
cd /d e:\Project\GnyanSetu\virtual_teacher_project
echo Starting GnyanSetu React Frontend...

cd "UI\Dashboard\Dashboard"

echo.
echo [1/2] Installing Node.js dependencies...
call npm install

echo.
echo [2/2] Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo Make sure the Django backend is running at: http://localhost:8000
echo.

call npm start
