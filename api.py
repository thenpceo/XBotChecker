from flask import Flask, request, jsonify, render_template, make_response
import time
import traceback
import os

from config import CONFIG
from scraper import Scraper 

api = Flask(__name__, static_folder='static')

# Print debug information about Flask configuration
print(f"Flask app configuration:")
print(f"  Template folder: {api.template_folder}")
print(f"  Static folder: {api.static_folder}")
print(f"  Template folder exists: {os.path.exists(api.template_folder)}")
print(f"  Templates in folder: {os.listdir(api.template_folder)}")

# Add a route to serve static files with no-cache headers
@api.route('/static/<path:filename>')
def serve_static(filename):
    response = api.send_static_file(filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['X-Cache-Bust'] = str(int(time.time()))
    return response

scraper = Scraper()

@api.route('/')
def index():
    tweet_id = request.args.get('id')
    analyze = request.args.get('analyze')
    
    if tweet_id and analyze:
        # API request
        try:
            # Check if using mock data for testing
            if tweet_id == 'mock':
                # Return mock data for testing
                return jsonify({
                    "score": 75,
                    "explanation": "This is a mock explanation for testing purposes. The tweet shows signs of potential bot activity based on the engagement patterns.",
                    "retweet_count": 1200,
                    "favorite_count": 3500,
                    "reply_count": 450,
                    "view_count": 25000,
                    "engagement_comparison": {
                        "avg_engagement": {
                            "avg_retweets": 800,
                            "avg_likes": 2500,
                            "avg_replies": 300,
                            "avg_views": 15000
                        }
                    }
                })
            
            scraper = Scraper()
            result = scraper.analyze(tweet_id)
            return jsonify(result)
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"Error analyzing tweet {tweet_id}: {str(e)}")
            print(error_traceback)
            
            # Return a more user-friendly error with default values
            return jsonify({
                "error": str(e),
                "score": 0,
                "retweet_count": 0,
                "favorite_count": 0,
                "reply_count": 0,
                "view_count": 0,
                "explanation": f"Error analyzing tweet: {str(e)}. Please try another tweet ID.",
                "engagement_comparison": {
                    "avg_engagement": {
                        "avg_retweets": 0,
                        "avg_likes": 0,
                        "avg_replies": 0,
                        "avg_views": 0
                    }
                }
            }), 200  # Return 200 instead of 500 to allow the UI to display the error
    else:
        # Web page request
        timestamp = int(time.time())  # Add timestamp for cache busting
        print(f"Serving new_x_template.html template with timestamp {timestamp}")
        response = make_response(render_template('new_x_template.html', timestamp=timestamp))
        # Add stronger cache control headers
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        response.headers['X-Cache-Bust'] = str(timestamp)
        
        # Add server ID header if environment variable is set
        server_id = os.environ.get('X_BOT_CHECKER_SERVER_ID')
        if server_id:
            response.headers['X-Server-ID'] = server_id
            
        return response

# Add a debug route to check if the template exists
@api.route('/debug')
def debug():
    import os
    template_path = os.path.join(api.template_folder, 'new_x_template.html')
    if os.path.exists(template_path):
        return f"Template exists at {template_path}"
    else:
        return f"Template does not exist at {template_path}"

# Add a debug route to check all templates
@api.route('/debug/templates')
def debug_templates():
    import os
    import glob
    
    result = []
    
    # Check which template folder is being used
    result.append(f"Template folder: {api.template_folder}")
    
    # List all template files
    template_files = glob.glob(os.path.join(api.template_folder, '*.html'))
    result.append(f"Found {len(template_files)} template files:")
    
    for template_file in template_files:
        # Check if this is the file we're trying to use
        is_target = os.path.basename(template_file) == 'new_x_template.html'
        
        # Check if the file contains our changes
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            has_changes = '<title>X Bot Checker</title>' in content
        
        result.append(f"- {template_file} {'(TARGET)' if is_target else ''} {'(UPDATED)' if has_changes else ''}")
    
    # Check which template is actually being rendered
    try:
        from flask import render_template_string
        test_template = render_template('new_x_template.html', timestamp=int(time.time()))
        has_changes = '<title>X Bot Checker</title>' in test_template
        result.append(f"\nRendered template {'contains' if has_changes else 'does NOT contain'} the changes")
    except Exception as e:
        result.append(f"\nError rendering template: {str(e)}")
    
    return "<br>".join(result)

# Add a route to force refresh
@api.route('/force-refresh')
def force_refresh():
    timestamp = int(time.time())
    return render_template('refresh.html', timestamp=timestamp)

# Add a direct route for force refresh that doesn't use templates
@api.route('/direct-refresh')
def direct_refresh():
    timestamp = int(time.time())
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Direct Refresh</title>
</head>
<body>
    <h1>Direct Refresh Page</h1>
    <p>Timestamp: {timestamp}</p>
    <script>
        setTimeout(function() {{
            window.location.href = "/?t={timestamp}";
        }}, 1500);
    </script>
</body>
</html>'''
    return html

if __name__ == '__main__':
    api.run(debug=CONFIG['DEBUG'], port=CONFIG['PORT'], host='0.0.0.0')