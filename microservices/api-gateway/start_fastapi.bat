@echo off
REM Start FastAPI API Gateway on port 8000
echo Starting FastAPI API Gateway on port 8000...

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "..\..\venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run from the main project venv
    pause
    exit /b 1
)

REM Activate virtual environment
call "..\..\venv\Scripts\activate.bat"

REM Install FastAPI requirements if needed
pip install -q -r requirements_fastapi.txt

REM Start FastAPI with uvicorn
echo.
echo ========================================
echo   FastAPI API Gateway Starting
echo ========================================
echo   Port: 8000
echo   Docs: http://localhost:8000/docs
echo   Health: http://localhost:8000/health
echo ========================================
echo.

python -m uvicorn app_fastapi:app --host 0.0.0.0 --port 8000 --reload

pause
