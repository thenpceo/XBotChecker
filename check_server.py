import os
import requests
import time
import subprocess
import sys

def check_server():
    """Check if the server is running from the correct directory"""
    print("=== X Bot Checker Server Check ===")
    
    # Get the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"Current directory: {current_dir}")
    
    # Check if the template file exists in the current directory
    template_path = os.path.join(current_dir, 'templates', 'new_x_template.html')
    if os.path.exists(template_path):
        print(f"✅ Template file exists at: {template_path}")
    else:
        print(f"❌ Template file does NOT exist at: {template_path}")
        return
    
    # Check if the server is running
    try:
        response = requests.get('http://localhost:5000/debug')
        if response.status_code == 200:
            print(f"✅ Server is running and returned: {response.text}")
        else:
            print(f"❌ Server returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error connecting to server: {str(e)}")
    
    # Check what directory the server is using
    try:
        # Kill any existing Python processes running api.py
        print("\nStopping any existing Flask servers...")
        if sys.platform == 'win32':
            # Windows
            os.system('taskkill /f /im python.exe')
        else:
            # Linux/Mac
            os.system('pkill -f "python api.py"')
        
        print("Starting server from the current directory...")
        # Start the server with a specific environment variable to identify it
        env = os.environ.copy()
        env['X_BOT_CHECKER_SERVER_ID'] = 'correct_server'
        
        # Start the server in a new process
        server_process = subprocess.Popen(
            ['python', 'api.py'],
            env=env,
            cwd=current_dir
        )
        
        # Wait for the server to start
        print("Waiting for server to start...")
        time.sleep(3)
        
        # Check if the server is running with our environment variable
        try:
            response = requests.get('http://localhost:5000/')
            if 'X-Server-ID' in response.headers and response.headers['X-Server-ID'] == 'correct_server':
                print("✅ Server is running from the correct directory")
            else:
                print("❌ Server is NOT running from the correct directory")
                print(f"Headers: {response.headers}")
        except Exception as e:
            print(f"❌ Error connecting to server: {str(e)}")
        
        # Kill the server process
        server_process.terminate()
        
    except Exception as e:
        print(f"❌ Error checking server directory: {str(e)}")
    
    print("\nRecommendation:")
    print("1. Make sure you're running the server from the correct directory")
    print("2. Try running the server with the full path:")
    print(f"   cd {current_dir} && python api.py")
    print("3. Or use the restart.ps1 script to restart the server")

if __name__ == "__main__":
    check_server() 