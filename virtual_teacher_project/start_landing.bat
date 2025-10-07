@echo off
cd /d e:\Project\GnyanSetu\virtual_teacher_project
echo Starting GyanSetu Landing Page...
echo.
echo This will start the React landing page on http://localhost:3000
echo Make sure the Django backend is running on http://localhost:8000
echo.
cd "UI\landing_page\landing_page"
npm start
