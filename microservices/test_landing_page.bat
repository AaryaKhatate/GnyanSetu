@echo off
REM Quick Landing Page Startup Test

echo.
echo 🏠 Testing Landing Page Startup...
echo ================================
echo.

REM Navigate to landing page directory
cd /d "e:\Project\Gnyansetu_Updated_Architecture\virtual_teacher_project\UI\landing_page\landing_page"

if not exist "package.json" (
    echo ❌ Error: package.json not found in current directory
    echo Current directory: %cd%
    pause
    exit /b 1
)

echo ✅ Found package.json
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm install
) else (
    echo ✅ Dependencies already installed
)

echo.
echo 🚀 Starting Landing Page on port 3000...
echo 💡 The landing page should show the original GnyanSetu design
echo 🎨 Look for the gradient background, logo, and navigation
echo.
echo Press Ctrl+C to stop the server
echo.

REM Set environment to avoid port conflicts
set PORT=3000

npm start