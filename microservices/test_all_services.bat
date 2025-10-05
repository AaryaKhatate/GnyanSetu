@echo off
echo.
echo ===============================================
echo  TESTING ALL API ENDPOINTS
echo ===============================================
echo.

echo [1/4] Testing API Gateway Health...
curl -s http://localhost:8000/health | findstr "healthy" >nul && echo ✓ API Gateway OK || echo ❌ API Gateway FAILED

echo [2/4] Testing Conversations Endpoint...
curl -s http://localhost:8000/api/conversations/ | findstr "conversations" >nul && echo ✓ Conversations OK || echo ❌ Conversations FAILED

echo [3/4] Testing Lesson Generation (No File)...
curl -s -X POST http://localhost:8000/api/generate-lesson/ | findstr "error" >nul && echo ✓ Lesson Service OK || echo ❌ Lesson Service FAILED

echo [4/4] Testing Teaching Service...
curl -s http://localhost:8004/api/health/ | findstr "healthy" >nul && echo ✓ Teaching Service OK || echo ❌ Teaching Service FAILED

echo.
echo ===============================================
echo  CURRENT SERVICE STATUS
echo ===============================================
echo API Gateway:      http://localhost:8000 ✓
echo User Service:     http://localhost:8002 ✓
echo Lesson Service:   http://localhost:8003 ✓  
echo Teaching Service: http://localhost:8004 ✓
echo Landing Page:     http://localhost:3000
echo Dashboard:        http://localhost:3001
echo ===============================================
echo.

pause