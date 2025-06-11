#!/usr/bin/env python3
"""
Script to start the FastAPI server with proper configuration
Includes virtual environment management
"""

import subprocess
import sys
import os
import time
import platform

def get_venv_path():
    """Get the virtual environment path based on OS"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python")
    else:
        return os.path.join("venv", "bin", "python")

def get_pip_path():
    """Get the pip path based on OS"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip")
    else:
        return os.path.join("venv", "bin", "pip")

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def upgrade_pip():
    """Upgrade pip in the virtual environment"""
    print("🔄 Upgrading pip...")
    pip_path = get_pip_path()
    
    try:
        subprocess.run([pip_path, 'install', '--upgrade', 'pip'], check=True)
        print("✅ pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not upgrade pip: {e}")
        return True  # Continue anyway
    except Exception as e:
        print(f"⚠️  Warning: Error upgrading pip: {e}")
        return True  # Continue anyway

def install_dependencies():
    """Install dependencies in the virtual environment"""
    print("📦 Installing dependencies...")
    pip_path = get_pip_path()
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed in venv"""
    print("🔍 Checking dependencies...")
    python_path = get_venv_path()
    
    try:
        # Test import of key dependencies
        result = subprocess.run([
            python_path, '-c', 
            'import fastapi, uvicorn, twilio; print("All dependencies available")'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All dependencies are available")
            return True
        else:
            print("❌ Some dependencies are missing")
            return False
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False

def start_server():
    """Start the FastAPI server using the virtual environment"""
    print("\n🚀 Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    
    # Check if ngrok URL file exists
    if os.path.exists('ngrok_url.txt'):
        print("\n📱 ngrok URLs:")
        with open('ngrok_url.txt', 'r') as f:
            print(f.read().strip())
    else:
        print("\n⚠️  ngrok not configured. Run 'python setup_ngrok.py' first for WhatsApp integration.")
    
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    python_path = get_venv_path()
    
    try:
        # Start the server using the virtual environment Python
        subprocess.run([
            python_path, '-m', 'uvicorn', 
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
    
    # Create virtual environment if needed
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        return
    
    # Upgrade pip
    upgrade_pip()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Verify dependencies
    if not check_dependencies():
        print("❌ Dependencies verification failed")
        return
    
    print("\n✅ Environment setup complete!")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()