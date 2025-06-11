#!/usr/bin/env python3
"""
Script to start the FastAPI server with proper configuration
"""

import subprocess
import sys
import os
import time

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import twilio
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing dependencies...")
        
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    print("🤖 WhatsApp Bot - Server Startup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ main.py not found. Make sure you're in the project directory.")
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()