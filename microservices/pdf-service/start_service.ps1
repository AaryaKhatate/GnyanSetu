# PDF Service Startup Script
echo "Starting PDF Service..."
echo "=========================="

# Check if Python is installed
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

# Check if virtual environment exists, create if not
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..."
pip install -r requirements.txt

# Check if MongoDB is running
Write-Host "Checking MongoDB connection..."
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('MongoDB is accessible')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "MongoDB is not running. Please start MongoDB before running the service."
    Write-Host "You can install MongoDB Community Edition from: https://www.mongodb.com/try/download/community"
}

# Check if RabbitMQ is running (optional)
Write-Host "Checking RabbitMQ connection..."
python -c "import pika; connection = pika.BlockingConnection(pika.ConnectionParameters('localhost')); print('RabbitMQ is accessible')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "RabbitMQ is not running. Event publishing will be disabled."
    Write-Host "You can install RabbitMQ from: https://www.rabbitmq.com/download.html"
}

# Create uploads directory
if (!(Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads"
    Write-Host "Created uploads directory"
}

Write-Host ""
Write-Host "🚀 Starting PDF Service on port 8001..."
Write-Host "📋 Health check: http://localhost:8001/health"
Write-Host "📄 Upload endpoint: http://localhost:8001/api/upload"
Write-Host ""
Write-Host "Press Ctrl+C to stop the service"
Write-Host ""

# Start the service
python app.py