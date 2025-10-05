@echo off
echo.
echo ===============================================
echo  FRONTEND RESTART - Apply API URL Fixes
echo ===============================================
echo.

echo Stopping current frontend processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 "') do taskkill /f /pid %%a >nul 2>&1

echo ✓ Frontend processes stopped
echo.

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo Starting Landing Page (Port 3000)...
cd /d "E:\Project\Gnyansetu_Updated_Architecture\virtual_teacher_project\UI\landing_page\landing_page"
start "Landing Page" cmd /k "npm start"
timeout /t 5 /nobreak >nul

echo Starting Dashboard (Port 3001)...
cd /d "E:\Project\Gnyansetu_Updated_Architecture\virtual_teacher_project\UI\Dashboard\Dashboard"
start "Dashboard" cmd /k "npm start"

echo.
echo ===============================================
echo  Frontend Services Restarted
echo ===============================================
echo Landing Page: http://localhost:3000
echo Dashboard:    http://localhost:3001
echo ===============================================
echo.
echo Frontend will now use correct API URLs:
echo - API Gateway: http://localhost:8000
echo - PDF Upload:  http://localhost:8000/api/generate-lesson/
echo - Chat:        http://localhost:8000/api/conversations/
echo - WebSocket:   ws://localhost:8004/ws/teaching/
echo.

pause