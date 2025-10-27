# Teaching Service - Quick Start Script
import os
import subprocess
import sys

def start_teaching_service():
    """Start the Teaching Service on port 8002"""
    print(" TEACHING SERVICE - REAL-TIME AI TEACHER")
    print("=" * 60)
    print(" Django Channels + WebSockets + Natural Voice")
    print(" Interactive Teaching with Konva.js Integration")
    print(" WebSocket URL: ws://localhost:8004/ws/teaching/")
    print("=" * 60)
    
    # Change to teaching service directory
    service_dir = r"E:\Project\Gnyansetu_Updated_Architecture\microservices\teaching-service"
    os.chdir(service_dir)
    
    # Start Django server
    try:
        subprocess.run([sys.executable, "manage.py", "runserver", "8004"], check=True)
    except KeyboardInterrupt:
        print("\n� Teaching Service stopped")
    except subprocess.CalledProcessError as e:
        print(f" Error starting service: {e}")

if __name__ == "__main__":
    start_teaching_service()