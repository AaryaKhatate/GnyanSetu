#!/bin/bash
# GnyanSetu Development Startup Script (Linux/Mac)

echo "========================================"
echo "Starting GnyanSetu Full Project"
echo "========================================"

# Set project root
PROJECT_ROOT="$(pwd)"
FRONTEND_PATH="$PROJECT_ROOT/UI/Dashboard/Dashboard"

echo ""
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "[2/4] Checking environment setup..."
if [ ! -f ".env" ]; then
    echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
    echo "[WARNING] Please add your Google API key to the .env file!"
    echo "Location: $PROJECT_ROOT/.env"
    read -p "Press Enter to continue..."
fi

echo ""
echo "[3/4] Installing Node.js dependencies..."
cd "$FRONTEND_PATH"
npm install

echo ""
echo "[4/4] Starting both servers..."
echo "Backend will run at: http://localhost:8000"
echo "Frontend will run at: http://localhost:3000"

# Go back to project root
cd "$PROJECT_ROOT"

# Install concurrently if not present
npm install -g concurrently 2>/dev/null || echo "Note: Install concurrently globally for better experience: npm install -g concurrently"

# Start both servers concurrently
echo ""
echo "🚀 Starting GnyanSetu..."
echo ""

# Option 1: Using concurrently (if available)
if command -v concurrently &> /dev/null; then
    concurrently \
        --names "Backend,Frontend" \
        --prefix-colors "cyan,yellow" \
        "python -m daphne -b 0.0.0.0 -p 8000 virtual_teacher_project.asgi:application" \
        "cd UI/Dashboard/Dashboard && npm start"
else
    # Option 2: Using background processes
    echo "Starting backend in background..."
    python -m daphne -b 0.0.0.0 -p 8000 virtual_teacher_project.asgi:application &
    BACKEND_PID=$!
    
    echo "Waiting 3 seconds for backend to start..."
    sleep 3
    
    echo "Starting frontend..."
    cd "$FRONTEND_PATH"
    npm start
    
    # Cleanup on exit
    trap "kill $BACKEND_PID" EXIT
fi
