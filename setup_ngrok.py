#!/usr/bin/env python3
"""
Script to help set up ngrok for the WhatsApp bot
"""

import subprocess
import sys
import time
import json
import os
import requests

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok is installed")
            print(f"Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok is not installed or not working")
            return False
    except FileNotFoundError:
        print("❌ ngrok is not installed")
        return False

def check_existing_auth():
    """Check if ngrok auth token is already configured"""
    try:
        # Try to get ngrok config
        result = subprocess.run(['ngrok', 'config', 'check'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok auth token is already configured")
            return True
        else:
            # Check if there's a config file
            config_paths = [
                os.path.expanduser("~/.ngrok2/ngrok.yml"),
                os.path.expanduser("~/Library/Application Support/ngrok/ngrok.yml"),  # macOS
                os.path.expanduser("~/AppData/Local/ngrok/ngrok.yml")  # Windows
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            content = f.read()
                            if 'authtoken:' in content and len(content.split('authtoken:')[1].strip().split()[0]) > 10:
                                print("✅ ngrok auth token found in config file")
                                return True
                    except Exception:
                        continue
            
            print("⚠️  ngrok auth token not found")
            return False
    except Exception as e:
        print(f"⚠️  Could not check auth status: {e}")
        return False

def setup_ngrok_auth():
    """Guide user through ngrok authentication"""
    print("\n🔐 Setting up ngrok authentication...")
    print("1. Go to https://dashboard.ngrok.com/get-started/your-authtoken")
    print("2. Sign up or log in to get your authtoken")
    print("3. Copy your authtoken")
    
    authtoken = input("\nPaste your ngrok authtoken here: ").strip()
    
    if not authtoken:
        print("❌ No authtoken provided")
        return False
    
    if len(authtoken) < 20:  # Basic validation
        print("❌ Authtoken seems too short. Please check and try again.")
        return False
    
    try:
        result = subprocess.run(['ngrok', 'config', 'add-authtoken', authtoken], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok authtoken configured successfully")
            return True
        else:
            print(f"❌ Failed to configure authtoken: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error configuring authtoken: {e}")
        return False

def wait_for_ngrok_api():
    """Wait for ngrok API to be available on port 4040"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
            if response.status_code == 200:
                print("✅ ngrok API is available")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"⏳ Waiting for ngrok API... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(2)
    
    print("❌ ngrok API did not become available on port 4040")
    return False

def get_tunnel_info():
    """Get tunnel information from ngrok API (port 4040) for tunnels pointing to port 8000"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            print(f"📊 Found {len(tunnels)} active tunnel(s)")
            
            # Look for HTTP tunnel pointing to port 8000
            for tunnel in tunnels:
                config = tunnel.get('config', {})
                addr = config.get('addr', '')
                public_url = tunnel.get('public_url', '')
                
                print(f"🔍 Checking tunnel: {public_url} -> {addr}")
                
                # Check if this tunnel points to our FastAPI server (port 8000)
                if 'localhost:8000' in addr or ':8000' in addr:
                    if public_url.startswith('https://'):
                        print(f"✅ Found HTTPS tunnel for port 8000: {public_url}")
                        return public_url
            
            # If no port 8000 tunnel found, return the first HTTPS tunnel
            for tunnel in tunnels:
                public_url = tunnel.get('public_url', '')
                if public_url.startswith('https://'):
                    print(f"⚠️  Using first available HTTPS tunnel: {public_url}")
                    return public_url
            
            print("❌ No HTTPS tunnels found")
            return None
        else:
            print(f"❌ ngrok API returned status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to ngrok API on port 4040: {e}")
        return None
    except Exception as e:
        print(f"❌ Error getting tunnel info: {e}")
        return None

def check_existing_tunnel():
    """Check if ngrok is already running with a tunnel to port 8000"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            data = response.json()
            existing_tunnels = data.get('tunnels', [])
            
            # Check if we already have a tunnel for port 8000
            for tunnel in existing_tunnels:
                config = tunnel.get('config', {})
                addr = config.get('addr', '')
                if 'localhost:8000' in addr or ':8000' in addr:
                    public_url = tunnel.get('public_url', '')
                    if public_url.startswith('https://'):
                        return public_url
            return None
    except:
        return None

def start_ngrok_tunnel():
    """Start ngrok tunnel for port 8000"""
    print("\n🚀 Starting ngrok tunnel...")
    print("This will create a public URL that forwards to your local server on port 8000")
    
    # Check if ngrok is already running with our tunnel
    existing_url = check_existing_tunnel()
    if existing_url:
        print("✅ ngrok tunnel already running!")
        print(f"🌐 Public URL: {existing_url}")
        print(f"📱 WhatsApp webhook URL: {existing_url}/webhook/whatsapp")
        
        # Save URL to file
        with open('ngrok_url.txt', 'w') as f:
            f.write(f"Public URL: {existing_url}\n")
            f.write(f"Webhook URL: {existing_url}/webhook/whatsapp\n")
        
        return existing_url
    
    try:
        # Start ngrok tunnel pointing to port 8000
        print("⏳ Starting ngrok tunnel to localhost:8000...")
        process = subprocess.Popen(['ngrok', 'http', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for ngrok API to be available on port 4040
        if not wait_for_ngrok_api():
            print("❌ ngrok API did not become available")
            print("💡 Try checking manually at http://localhost:4040")
            return None
        
        # Get tunnel information from API
        public_url = get_tunnel_info()
        
        if public_url:
            print("✅ ngrok tunnel started successfully!")
            print(f"🌐 Public URL: {public_url}")
            print(f"📱 WhatsApp webhook URL: {public_url}/webhook/whatsapp")
            print(f"🔧 ngrok web interface: http://localhost:4040")
            
            # Save URL to file for reference
            with open('ngrok_url.txt', 'w') as f:
                f.write(f"Public URL: {public_url}\n")
                f.write(f"Webhook URL: {public_url}/webhook/whatsapp\n")
                f.write(f"ngrok Web Interface: http://localhost:4040\n")
            
            return public_url
        else:
            print("❌ Could not get tunnel URL from API")
            print("💡 Try checking the ngrok web interface at http://localhost:4040")
            return None
        
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None

def install_ngrok_instructions():
    """Show installation instructions for ngrok"""
    print("\n📦 ngrok Installation Instructions:")
    print("=" * 40)
    
    system = sys.platform.lower()
    
    if system.startswith('win'):
        print("Windows:")
        print("1. Download ngrok from: https://ngrok.com/download")
        print("2. Extract the zip file")
        print("3. Add ngrok.exe to your PATH or run from the extracted folder")
    elif system.startswith('darwin'):
        print("macOS:")
        print("Option 1 - Homebrew (recommended):")
        print("  brew install ngrok/ngrok/ngrok")
        print("\nOption 2 - Direct download:")
        print("  Download from: https://ngrok.com/download")
    else:
        print("Linux:")
        print("Option 1 - Snap:")
        print("  sudo snap install ngrok")
        print("\nOption 2 - Direct download:")
        print("  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null")
        print("  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list")
        print("  sudo apt update && sudo apt install ngrok")
    
    print("\nAfter installation, run this script again!")

def main():
    print("🤖 WhatsApp Bot - ngrok Setup")
    print("=" * 40)
    print("📋 Port Configuration:")
    print("   • FastAPI Server: localhost:8000 (your app)")
    print("   • ngrok API: localhost:4040 (management)")
    print("   • ngrok tunnel: public URL -> localhost:8000")
    print()
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        install_ngrok_instructions()
        return
    
    # Check if auth token is already configured
    auth_configured = check_existing_auth()
    
    if not auth_configured:
        # Setup authentication
        if not setup_ngrok_auth():
            print("❌ Failed to setup ngrok authentication")
            return
    
    # Start tunnel
    public_url = start_ngrok_tunnel()
    
    if public_url:
        print("\n" + "=" * 50)
        print("🎉 Setup Complete!")
        print("=" * 50)
        print(f"Your public URL: {public_url}")
        print(f"Webhook URL: {public_url}/webhook/whatsapp")
        print("\nNext steps:")
        print("1. Copy the webhook URL above")
        print("2. Configure it in your Twilio WhatsApp sandbox")
        print("3. Start your FastAPI server: python start_server.py")
        print("4. Test your WhatsApp bot!")
        print("\n💡 Tips:")
        print("- Keep this terminal open to maintain the tunnel")
        print("- ngrok web interface: http://localhost:4040")
        print("- URL saved to: ngrok_url.txt")
        print("- Your FastAPI server should run on port 8000")
    else:
        print("❌ Failed to start ngrok tunnel")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your authtoken is correct")
        print("2. Check if port 4040 is available (ngrok web interface)")
        print("3. Try restarting ngrok manually: ngrok http 8000")
        print("4. Check ngrok web interface: http://localhost:4040")
        print("5. Make sure no other ngrok processes are running")

if __name__ == "__main__":
    main()