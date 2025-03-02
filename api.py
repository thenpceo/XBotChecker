from flask import Flask, request, jsonify, render_template, make_response, send_from_directory, redirect, session, url_for
import time
import traceback
import os
import json
import secrets

from config import CONFIG
from scraper import Scraper 
from firebase_config import save_post_data, get_post_data, get_all_posts, db

# Custom JSON encoder to handle special values like Infinity and NaN
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float) and (obj == float('inf') or obj == float('-inf') or obj != obj):  # Check for inf, -inf, and NaN
            return 1e9 if obj > 0 else -1e9 if obj < 0 else 0  # Convert inf to 1e9, -inf to -1e9, and NaN to 0
        return super().default(obj)

api = Flask(__name__, static_folder='static')
api.secret_key = secrets.token_hex(16)  # Generate a random secret key for session
api.json_encoder = CustomJSONEncoder  # Use our custom JSON encoder

# Password for accessing protected pages
ADMIN_PASSWORD = "admin1234"

# Add a route to serve favicon.ico from the root
@api.route('/favicon.ico')
def favicon():
    return send_from_directory(api.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

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
                mock_data = {
                    "score": 75,
                    "explanation": "This is a mock explanation for testing purposes. The tweet shows signs of potential bot activity based on the engagement patterns.",
                    "retweet_count": 1200,
                    "favorite_count": 3500,
                    "reply_count": 450,
                    "view_count": 25000,
                    "followers": 5000,
                    "engagement_comparison": {
                        "avg_engagement": {
                            "avg_retweets": 800,
                            "avg_likes": 2500,
                            "avg_replies": 300,
                            "avg_views": 15000
                        }
                    },
                    "follower_range_comparison": {
                        "follower_range": {
                            "min": 2000,
                            "max": 6000,
                            "id": "2k_to_6k"
                        },
                        "avg_metrics": {
                            "avg_retweets": 600,
                            "avg_likes": 2000,
                            "avg_replies": 250,
                            "avg_views": 12000,
                            "post_count": 150
                        }
                    },
                    "timestamp": time.time()
                }
                # Save mock data to Firebase
                print("Mock data before saving to Firebase:", mock_data)
                print("Follower range comparison in mock data:", 'follower_range_comparison' in mock_data)
                save_post_data(tweet_id, mock_data)
                
                # Get the data from Firebase to verify it was saved correctly
                saved_data = get_post_data(tweet_id)
                print("Data retrieved from Firebase:", saved_data)
                print("Follower range comparison in saved data:", 'follower_range_comparison' in saved_data if saved_data else "No saved data")
                
                # Return the mock data directly
                print("Returning mock data:", mock_data)
                return jsonify(mock_data)
            
            # Check if we already have this post in the database
            cached_data = get_post_data(tweet_id)
            if cached_data:
                return jsonify(cached_data)
            
            # If not in database, analyze the post
            scraper = Scraper()
            result = scraper.analyze(tweet_id)
            
            # Save the result to Firebase
            save_post_data(tweet_id, result)
            
            return jsonify(result)
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"Error analyzing tweet {tweet_id}: {str(e)}")
            
            # Return a more user-friendly error with default values
            error_response = {
                "error": str(e),
                "score": 0,
                "retweet_count": 0,
                "favorite_count": 0,
                "reply_count": 0,
                "view_count": 0,
                "followers": 0,
                "explanation": f"Error analyzing tweet: {str(e)}. Please try another tweet ID.",
                "engagement_comparison": {
                    "avg_engagement": {
                        "avg_retweets": 0,
                        "avg_likes": 0,
                        "avg_replies": 0,
                        "avg_views": 0
                    }
                },
                "follower_range_comparison": {
                    "follower_range": {
                        "min": 0,
                        "max": 0,
                        "id": "unknown"
                    },
                    "avg_metrics": {
                        "avg_retweets": 0,
                        "avg_likes": 0,
                        "avg_replies": 0,
                        "avg_views": 0,
                        "post_count": 0
                    }
                }
            }
            
            # Save error to Firebase for tracking
            save_post_data(f"error_{tweet_id}", error_response)
            
            return jsonify(error_response), 200  # Return 200 instead of 500 to allow the UI to display the error
    else:
        # Web page request
        timestamp = int(time.time())  # Add timestamp for cache busting
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

# Add a login route
@api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('view_posts'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

# Add a logout route
@api.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

# Add a route to view all analyzed posts
@api.route('/posts')
def view_posts():
    # Check if user is authenticated
    if not session.get('authenticated'):
        return redirect(url_for('login'))
        
    try:
        limit = request.args.get('limit', default=100, type=int)
        print(f"Fetching posts with limit: {limit}")
        
        posts = get_all_posts(limit=limit)
        print(f"Retrieved {len(posts)} posts from database")
        
        # Filter out error posts
        valid_posts = []
        for post in posts:
            # Skip posts that have an error field or are missing essential fields
            if 'error' in post:
                print(f"Skipping error post: {post.get('id', 'unknown')}")
                continue
                
            # Check for required fields
            required_fields = ['score', 'explanation', 'retweet_count', 'favorite_count', 'reply_count', 'view_count']
            missing_fields = [field for field in required_fields if field not in post]
            
            if missing_fields:
                print(f"Skipping post {post.get('id', 'unknown')} due to missing fields: {missing_fields}")
                continue
            
            # Add the post to valid posts
            valid_posts.append(post)
        
        print(f"Filtered to {len(valid_posts)} valid posts")
        
        # Process the valid posts
        for i, post in enumerate(valid_posts):
            try:
                # Ensure engagement_comparison exists
                if 'engagement_comparison' not in post or not post['engagement_comparison']:
                    print(f"Adding missing 'engagement_comparison' to post {i} (ID: {post.get('id', 'unknown')})")
                    post['engagement_comparison'] = {
                        'avg_engagement': {
                            'avg_retweets': 0,
                            'avg_likes': 0,
                            'avg_replies': 0,
                            'avg_views': 0
                        }
                    }
                elif 'avg_engagement' not in post['engagement_comparison'] or not post['engagement_comparison']['avg_engagement']:
                    print(f"Adding missing 'avg_engagement' to post {i} (ID: {post.get('id', 'unknown')})")
                    post['engagement_comparison']['avg_engagement'] = {
                        'avg_retweets': 0,
                        'avg_likes': 0,
                        'avg_replies': 0,
                        'avg_views': 0
                    }
                
                # Debug timestamp handling
                if 'timestamp' in post:
                    print(f"Post {i} timestamp type: {type(post['timestamp'])}, value: {post['timestamp']}")
            except Exception as post_error:
                print(f"Error processing post {i}: {str(post_error)}")
                print(traceback.format_exc())
        
        print("Rendering posts.html template")
        timestamp = int(time.time())
        response = make_response(render_template('posts.html', posts=valid_posts, timestamp=timestamp))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        
        return response
    except Exception as e:
        print(f"Error in view_posts route: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        # Return a friendly error page
        timestamp = int(time.time())
        return render_template('posts.html', posts=[], error=str(e), timestamp=timestamp), 200

@api.route('/reanalyze')
def reanalyze_post():
    """
    Clear the cache and re-analyze a post
    """
    try:
        tweet_id = request.args.get('id')
        redirect_to = request.args.get('redirect_to', 'posts')  # Default redirect to posts page
        
        if not tweet_id:
            return jsonify({"error": "No tweet ID provided"}), 400
            
        # Format the URL
        scraper = Scraper()
        scrape_url = scraper.get_url(tweet_id)
        
        # Clear the cache
        scraper.clear_cache(scrape_url, '_analysis')
        
        # Re-analyze the post
        result = scraper.analyze(tweet_id)
        
        # Save the result to Firebase
        save_post_data(tweet_id, result)
        
        # Check if we should redirect or return JSON
        if redirect_to == 'json':
            return jsonify(result)
        elif redirect_to == 'home':
            return redirect(f'/?id={tweet_id}&analyze=true')
        else:
            # Default to posts page
            return redirect('/posts')
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Error re-analyzing tweet {tweet_id}: {str(e)}")
        print(f"Traceback: {error_traceback}")
        
        return jsonify({"error": str(e)}), 500

@api.route('/fix-scores')
def fix_scores():
    try:
        # Get all posts
        posts = get_all_posts(limit=1000)
        
        # Filter posts with zero scores
        zero_score_posts = []
        for post in posts:
            if 'score' not in post or post['score'] == 0:
                zero_score_posts.append(post)
        
        # Render the template
        timestamp = int(time.time())
        response = make_response(render_template('fixed_scores.html', posts=zero_score_posts, timestamp=timestamp))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        
        return response
    except Exception as e:
        print(f"Error in fix_scores route: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        # Return a friendly error page
        timestamp = int(time.time())
        return render_template('fixed_scores.html', posts=[], error=str(e), timestamp=timestamp), 200

@api.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """
    Handle user feedback on post analysis (too high/too low)
    """
    try:
        # Get the request data
        data = request.json
        post_id = data.get('post_id')
        feedback_type = data.get('feedback_type')
        
        if not post_id or not feedback_type:
            return jsonify({'success': False, 'error': 'Missing post_id or feedback_type'}), 400
        
        # Get the post data
        post_data = get_post_data(post_id)
        if not post_data:
            return jsonify({'success': False, 'error': 'Post not found'}), 404
        
        # Initialize user_feedback if it doesn't exist
        if 'user_feedback' not in post_data:
            post_data['user_feedback'] = {}
        
        # Update the feedback - map new feedback types to existing database structure
        if feedback_type == 'too_low':
            # Map 'too_low' to existing 'thumbs_up' in database for backward compatibility
            post_data['user_feedback']['thumbs_up'] = True
            post_data['user_feedback']['thumbs_down'] = False
            # Add new field for clarity
            post_data['user_feedback']['too_low'] = True
            post_data['user_feedback']['too_high'] = False
        elif feedback_type == 'too_high':
            # Map 'too_high' to existing 'thumbs_down' in database for backward compatibility
            post_data['user_feedback']['thumbs_up'] = False
            post_data['user_feedback']['thumbs_down'] = True
            # Add new field for clarity
            post_data['user_feedback']['too_low'] = False
            post_data['user_feedback']['too_high'] = True
        # Keep backward compatibility with old feedback types
        elif feedback_type == 'thumbs_up':
            post_data['user_feedback']['thumbs_up'] = True
            post_data['user_feedback']['thumbs_down'] = False
            post_data['user_feedback']['too_low'] = True
            post_data['user_feedback']['too_high'] = False
        elif feedback_type == 'thumbs_down':
            post_data['user_feedback']['thumbs_up'] = False
            post_data['user_feedback']['thumbs_down'] = True
            post_data['user_feedback']['too_low'] = False
            post_data['user_feedback']['too_high'] = True
        else:
            return jsonify({'success': False, 'error': 'Invalid feedback_type'}), 400
        
        # Save the updated post data
        save_post_data(post_id, post_data)
        
        # If too_high (thumbs_down), remove this post's metrics from the follower range averages
        if feedback_type in ['too_high', 'thumbs_down']:
            # This will be handled by the update_average_metrics_for_range function
            # which checks for thumbs_down feedback
            pass
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in submit_feedback route: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    api.run(debug=CONFIG['DEBUG'], port=CONFIG['PORT'], host='0.0.0.0')