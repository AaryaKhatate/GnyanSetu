@echo off
REM ASGI startup script for Lesson Service with Daphne (Windows)
REM Production-grade Django ASGI server

echo Starting Lesson Service with Daphne ASGI...
echo Port: 8003
echo Environment: Production-ready with ASGI

REM Start Daphne ASGI server
daphne -b 0.0.0.0 -p 8003 lesson_service.asgi:application --verbosity 2