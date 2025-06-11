#!/usr/bin/env python3
"""
Script to help set up ngrok for the WhatsApp bot
"""

import subprocess
import sys
import time
import json
import os

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

def start_ngrok_tunnel():
    """Start ngrok tunnel for port 8000"""
    print("\n🚀 Starting ngrok tunnel...")
    print("This will create a public URL for your local server on port 8000")
    
    try:
        # Start ngrok in background
        process = subprocess.Popen(['ngrok', 'http', '8000', '--log=stdout'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print("⏳ Starting ngrok tunnel... (this may take a few seconds)")
        time.sleep(3)  # Give ngrok time to start
        
        # Get the public URL
        try:
            api_result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                      capture_output=True, text=True)
            if api_result.returncode == 0:
                data = json.loads(api_result.stdout)
                tunnels = data.get('tunnels', [])
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print(f"✅ ngrok tunnel started successfully!")
                    print(f"🌐 Public URL: {public_url}")
                    print(f"📱 WhatsApp webhook URL: {public_url}/webhook/whatsapp")
                    
                    # Save URL to file for reference
                    with open('ngrok_url.txt', 'w') as f:
                        f.write(f"Public URL: {public_url}\n")
                        f.write(f"Webhook URL: {public_url}/webhook/whatsapp\n")
                    
                    return public_url
                else:
                    print("❌ No tunnels found")
            else:
                print("❌ Could not get tunnel information")
        except Exception as e:
            print(f"⚠️  Could not get public URL automatically: {e}")
            print("Check the ngrok web interface at http://localhost:4040")
        
        return None
        
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None

def main():
    print("🤖 WhatsApp Bot - ngrok Setup")
    print("=" * 40)
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        print("\n📦 Installing ngrok...")
        print("Please run the installation commands first, then run this script again.")
        return
    
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
        print("3. Start your FastAPI server in another terminal")
        print("4. Test your WhatsApp bot!")
        print("\nNote: Keep this terminal open to maintain the tunnel")
    else:
        print("❌ Failed to start ngrok tunnel")

if __name__ == "__main__":
    main()