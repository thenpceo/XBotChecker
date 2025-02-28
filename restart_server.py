import os
import shutil
import subprocess
import time

def clear_cache():
    """Clear the Flask cache directory if it exists"""
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    if os.path.exists(cache_dir):
        print(f"Clearing cache directory: {cache_dir}")
        try:
            # Remove all files in the cache directory
            for filename in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print("Cache cleared successfully")
        except Exception as e:
            print(f"Error clearing cache: {e}")
    else:
        print("No cache directory found")

def clear_flask_cache():
    """Clear Flask's __pycache__ directory"""
    pycache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '__pycache__')
    if os.path.exists(pycache_dir):
        print(f"Clearing Flask __pycache__ directory: {pycache_dir}")
        try:
            shutil.rmtree(pycache_dir)
            print("Flask cache cleared successfully")
        except Exception as e:
            print(f"Error clearing Flask cache: {e}")
    else:
        print("No Flask __pycache__ directory found")

def restart_server():
    """Restart the Flask server"""
    print("Restarting Flask server...")
    try:
        # Run the Flask application
        subprocess.Popen(["python", "api.py"], 
                        cwd=os.path.dirname(os.path.abspath(__file__)))
        print("Server restarted successfully")
    except Exception as e:
        print(f"Error restarting server: {e}")

if __name__ == "__main__":
    print("=== X Bot Checker Server Restart Utility ===")
    clear_cache()
    clear_flask_cache()
    restart_server()
    print("\nServer has been restarted with a clean cache.")
    print("Please also clear your browser cache or use incognito mode to see the changes.")
    print("The server is now running at http://127.0.0.1:5000") 