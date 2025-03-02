import os
import sys
import traceback

try:
    # Check if running on Vercel
    if os.environ.get('VERCEL'):
        # Use the simplified scraper for Vercel
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from vercel_scraper import Scraper
        from api import api
        
        # Create templates directory if it doesn't exist
        if not os.path.exists('templates'):
            os.makedirs('templates')
            
        # Copy the fresh_template.html to index.html if it doesn't exist
        if os.path.exists('templates/fresh_template.html') and not os.path.exists('templates/index.html'):
            with open('templates/fresh_template.html', 'r', encoding='utf-8') as src:
                with open('templates/index.html', 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
        
        app = api
    else:
        # Use the regular scraper for local development
        from api import api as app
except Exception as e:
    print(f"Error in index.py: {str(e)}")
    traceback.print_exc()
    
    # Create a minimal Flask app as fallback
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({
            "error": f"Application initialization error: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

# This file is used by Vercel as an entry point
# The app variable is imported from api.py 