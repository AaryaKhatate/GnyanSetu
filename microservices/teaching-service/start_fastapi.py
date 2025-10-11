"""
Start Teaching Service (FastAPI)
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('PORT', 8004))
    
    print("=" * 60)
    print(f"Starting Teaching Service (FastAPI) on port {port}")
    print("=" * 60)
    
    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
