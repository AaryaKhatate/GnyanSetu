@echo off
echo ============================================================
echo Starting Lesson Service on port 8003
echo ============================================================
cd /d "%~dp0"
python manage.py runserver 0.0.0.0:8003
pause
