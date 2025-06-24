#!/usr/bin/env python3
"""
Script to start the FastAPI server with proper configuration
Includes virtual environment management with proper activation
"""

import subprocess
import sys
import os
import time
import platform

def get_venv_python_path():
    """Get the Python executable path in the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")

def get_venv_pip_path():
    """Get the pip executable path in the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip.exe")
    else:
        return os.path.join("venv", "bin", "pip")

def get_venv_activate_script():
    """Get the activation script path"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "activate.bat")
    else:
        return os.path.join("venv", "bin", "activate")

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        # Use the current Python interpreter to create venv
        result = subprocess.run([sys.executable, '-m', 'venv', 'venv'], 
                              capture_output=True, text=True, check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def check_venv_python():
    """Check if the virtual environment Python is working"""
    python_path = get_venv_python_path()
    
    if not os.path.exists(python_path):
        print(f"❌ Virtual environment Python not found at: {python_path}")
        return False
    
    try:
        result = subprocess.run([python_path, '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Virtual environment Python: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Virtual environment Python not working: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking virtual environment Python: {e}")
        return False

def upgrade_pip():
    """Upgrade pip in the virtual environment"""
    print("🔄 Upgrading pip in virtual environment...")
    python_path = get_venv_python_path()
    
    try:
        result = subprocess.run([python_path, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                              capture_output=True, text=True, check=True)
        print("✅ pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not upgrade pip: {e}")
        print(f"Error output: {e.stderr}")
        return True  # Continue anyway
    except Exception as e:
        print(f"⚠️  Warning: Error upgrading pip: {e}")
        return True  # Continue anyway

def install_dependencies():
    """Install dependencies in the virtual environment"""
    print("📦 Installing dependencies in virtual environment...")
    python_path = get_venv_python_path()
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Use python -m pip to ensure we're using the venv pip
        result = subprocess.run([python_path, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True, check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed in venv"""
    print("🔍 Checking dependencies in virtual environment...")
    python_path = get_venv_python_path()
    
    try:
        # Test import of key dependencies using the venv Python
        result = subprocess.run([
            python_path, '-c', 
            'import fastapi, uvicorn, twilio; print("All dependencies available")'
        ], capture_output=True, text=True, check=True)
        
        print("✅ All dependencies are available in virtual environment")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Some dependencies are missing from virtual environment")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False

def show_activation_instructions():
    """Show manual activation instructions"""
    print("\n💡 Manual Virtual Environment Activation:")
    print("=" * 50)
    
    if platform.system() == "Windows":
        print("Windows Command Prompt:")
        print("  venv\\Scripts\\activate")
        print("\nWindows PowerShell:")
        print("  venv\\Scripts\\Activate.ps1")
    else:
        print("macOS/Linux:")
        print("  source venv/bin/activate")
    
    print("\nAfter activation, you can run:")
    print("  python main.py")
    print("  # or")
    print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

def start_server():
    """Start the FastAPI server using the virtual environment Python directly"""
    print("\n🚀 Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    
    # Check if ngrok URL file exists
    if os.path.exists('ngrok_url.txt'):
        print("\n📱 ngrok URLs:")
        try:
            with open('ngrok_url.txt', 'r') as f:
                print(f.read().strip())
        except Exception as e:
            print(f"Could not read ngrok_url.txt: {e}")
    else:
        print("\n⚠️  ngrok not configured. Run 'python setup_ngrok.py' first for WhatsApp integration.")
    
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    python_path = get_venv_python_path()
    
    try:
        # Start the server using the virtual environment Python directly
        # This bypasses the need for activation scripts
        subprocess.run([
            python_path, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed")
        print("2. Check if port 8000 is available")
        print("3. Try running manually:")
        show_activation_instructions()
    except Exception as e:
        print(f"❌ Unexpected error starting server: {e}")

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
    
    # Check if venv Python is working
    if not check_venv_python():
        print("❌ Virtual environment Python is not working")
        print("Try deleting the 'venv' folder and running this script again.")
        return
    
    # Upgrade pip in the virtual environment
    upgrade_pip()
    
    # Install dependencies in the virtual environment
    if not install_dependencies():
        print("❌ Failed to install dependencies in virtual environment")
        print("Try deleting the 'venv' folder and running this script again.")
        return
    
    # Verify dependencies in the virtual environment
    if not check_dependencies():
        print("❌ Dependencies verification failed in virtual environment")
        print("Try running: python -m pip install -r requirements.txt")
        show_activation_instructions()
        return
    
    print("\n✅ Virtual environment setup complete!")
    print(f"✅ Using Python: {get_venv_python_path()}")
    
    # Start server using venv Python directly
    start_server()

if __name__ == "__main__":
    main()