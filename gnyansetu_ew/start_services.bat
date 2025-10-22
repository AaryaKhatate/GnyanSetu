@echo off
REM Start all services in separate terminals (Windows PowerShell)
start powershell -NoExit -Command "cd '%~dp0' ; uvicorn gnyansetu_ew.gateway:app --host 0.0.0.0 --port 8080 --reload"
start powershell -NoExit -Command "cd '%~dp0' ; uvicorn gnyansetu_ew.lesson_service:app --host 0.0.0.0 --port 8081 --reload"
start powershell -NoExit -Command "cd '%~dp0' ; uvicorn gnyansetu_ew.visualization_service:app --host 0.0.0.0 --port 8082 --reload"
start powershell -NoExit -Command "cd '%~dp0' ; uvicorn gnyansetu_ew.quiz_service:app --host 0.0.0.0 --port 8083 --reload"
start powershell -NoExit -Command "cd '%~dp0' ; echo UI is static in ui/index.html; pause"
echo Started all services on ports 8080-8083
pause
