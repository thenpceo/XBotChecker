import requests
import re
import os
import time

def check_template_content():
    """Check if the template being served contains the expected changes"""
    print("=== X Bot Checker Template Verification ===")
    
    # Get the current template file content
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'new_x_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Check if the template file contains the expected changes
    expected_changes = [
        '<title>X Bot Checker</title>',
        'X Bot Checker Logo',
        'X BOT CHECKER',
        'type: \'logarithmic\''
    ]
    
    print("\nChecking local template file:")
    for change in expected_changes:
        if change in template_content:
            print(f"✅ Found: {change}")
        else:
            print(f"❌ Missing: {change}")
    
    # Now check what's being served by the server
    print("\nChecking what's being served by the server:")
    try:
        # Add cache-busting parameter
        timestamp = int(time.time())
        response = requests.get(f'http://localhost:5000/?cachebust={timestamp}', 
                               headers={
                                   'Cache-Control': 'no-cache, no-store, must-revalidate',
                                   'Pragma': 'no-cache',
                                   'Expires': '0'
                               })
        
        if response.status_code == 200:
            served_content = response.text
            
            for change in expected_changes:
                if change in served_content:
                    print(f"✅ Server is serving: {change}")
                else:
                    print(f"❌ Server is NOT serving: {change}")
            
            # Check if the server is using the correct template
            print("\nServer response headers:")
            for header, value in response.headers.items():
                print(f"{header}: {value}")
            
            # Check for cache-busting timestamp
            if 'X-Cache-Bust' in response.headers:
                print(f"\n✅ Server is using cache-busting with timestamp: {response.headers['X-Cache-Bust']}")
            else:
                print("\n❌ Server is NOT using cache-busting headers")
        else:
            print(f"❌ Server returned status code: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error connecting to server: {str(e)}")
    
    print("\nIf the server is not serving the expected content, try:")
    print("1. Restart the server using the restart.ps1 script")
    print("2. Clear your browser cache or use incognito mode")
    print("3. Open the test_browser.html file in your browser")

if __name__ == "__main__":
    check_template_content() 