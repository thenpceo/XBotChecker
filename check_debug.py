import requests
import time

def check_debug():
    """Check the debug route to see what templates are being used"""
    print("=== Checking Debug Route ===")
    
    # Add cache-busting parameter
    timestamp = int(time.time())
    
    try:
        # Check the templates debug route
        response = requests.get(f'http://localhost:5000/debug/templates?cachebust={timestamp}', 
                               headers={
                                   'Cache-Control': 'no-cache, no-store, must-revalidate',
                                   'Pragma': 'no-cache',
                                   'Expires': '0'
                               })
        
        if response.status_code == 200:
            print(response.text.replace('<br>', '\n'))
        else:
            print(f"Error: Server returned status code {response.status_code}")
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")

if __name__ == "__main__":
    check_debug() 