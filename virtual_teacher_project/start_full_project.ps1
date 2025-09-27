# GnyanSetu Full Project Startup Script
# PowerShell version for better error handling

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting GnyanSetu Full Project" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Set base directory
$ProjectRoot = "d:\Virtual-Tutor\virtual_teacher_project"
$FrontendPath = "$ProjectRoot\UI\Dashboard\Dashboard"

Write-Host ""
Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $ProjectRoot
& "C:/Python313/python.exe" -m pip install -r requirements.txt

Write-Host ""
Write-Host "[2/4] Checking environment setup..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    "GOOGLE_API_KEY=your_google_api_key_here" | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "[WARNING] Please add your Google API key to the .env file!" -ForegroundColor Red
    Write-Host "Location: $ProjectRoot\.env" -ForegroundColor Red
    Read-Host "Press Enter to continue"
}

Write-Host ""
Write-Host "[3/4] Starting Django Backend (Daphne ASGI Server)..." -ForegroundColor Yellow
Write-Host "Backend will run at: http://localhost:8000" -ForegroundColor Green
Write-Host "WebSocket will be at: ws://localhost:8000/ws/teacher/" -ForegroundColor Green

# Start backend in new window
$BackendScript = @"
Set-Location '$ProjectRoot'
Write-Host 'Starting GnyanSetu Backend...' -ForegroundColor Green
& 'C:/Python313/python.exe' -m daphne -b 0.0.0.0 -p 8000 virtual_teacher_project.asgi:application
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendScript -WindowStyle Normal

Write-Host ""
Write-Host "Waiting 5 seconds for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "[4/4] Starting React Frontend..." -ForegroundColor Yellow
Write-Host "Frontend will run at: http://localhost:3000" -ForegroundColor Green

# Start frontend in new window
$FrontendScript = @"
Set-Location '$FrontendPath'
Write-Host 'Installing Node.js dependencies...' -ForegroundColor Green
npm install
Write-Host 'Starting React development server...' -ForegroundColor Green
npm start
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendScript -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ GnyanSetu is starting up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   WebSocket: ws://localhost:8000/ws/teacher/" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Note: Two terminal windows will open:" -ForegroundColor White
Write-Host "   1. Backend (Django + Daphne)" -ForegroundColor Yellow
Write-Host "   2. Frontend (React Dev Server)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to close this window..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
