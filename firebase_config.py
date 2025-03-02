import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import json
import traceback

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyD2bEwYLkSQ0WrecpVudZM4qfQM6YO37ps",
    "authDomain": "x-bot-checker.firebaseapp.com",
    "projectId": "x-bot-checker",
    "storageBucket": "x-bot-checker.firebasestorage.app",
    "messagingSenderId": "839602336222",
    "appId": "1:839602336222:web:e9781fb00b8e9a8f92ad4f",
    "measurementId": "G-D9K15Q04DW"
}

# Path to service account key file
SERVICE_ACCOUNT_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'firebase-key.json')

# Define follower ranges for average metrics
FOLLOWER_RANGES = [
    {"min": 0, "max": 2000, "id": "under_2k"},
    {"min": 2000, "max": 6000, "id": "2k_to_6k"},
    {"min": 6000, "max": 12000, "id": "6k_to_12k"},
    {"min": 12000, "max": 25000, "id": "12k_to_25k"},
    {"min": 25000, "max": 100000, "id": "25k_to_100k"},
    {"min": 100000, "max": 500000, "id": "100k_to_500k"},
    {"min": 500000, "max": 1e9, "id": "over_500k"}  # Use 1e9 instead of float('inf')
]

# Mock implementation for local testing
class MockFirestore:
    def __init__(self):
        self.data = {}
    
    def collection(self, collection_name):
        if collection_name not in self.data:
            self.data[collection_name] = {}
        return MockCollection(self.data[collection_name])

class MockCollection:
    def __init__(self, data):
        self.data = data
    
    def document(self, doc_id):
        return MockDocument(self.data, doc_id)
    
    def order_by(self, field, direction=None):
        # Simple implementation that doesn't actually sort
        return self
    
    def limit(self, limit_count):
        self.limit_count = limit_count
        return self
    
    def stream(self):
        # Return at most limit_count items
        count = 0
        for doc_id, doc_data in self.data.items():
            if hasattr(self, 'limit_count') and count >= self.limit_count:
                break
            yield MockDocumentSnapshot(doc_id, doc_data)
            count += 1

class MockDocument:
    def __init__(self, collection_data, doc_id):
        self.collection_data = collection_data
        self.doc_id = doc_id
    
    def set(self, data):
        self.collection_data[self.doc_id] = data
        return True
    
    def get(self):
        return MockDocumentSnapshot(self.doc_id, self.collection_data.get(self.doc_id, None))

class MockDocumentSnapshot:
    def __init__(self, doc_id, data):
        self.doc_id = doc_id
        self.data = data
    
    @property
    def exists(self):
        return self.data is not None
    
    def to_dict(self):
        return self.data
    
    @property
    def id(self):
        return self.doc_id

# Initialize Firebase or use mock implementation
try:
    # Check if Firebase is already initialized
    firebase_admin.get_app()
    db = firestore.client()
    print("Using existing Firebase connection")
except ValueError:
    try:
        # Check if service account key file exists
        if os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            # Initialize Firebase with service account credentials
            print(f"Initializing Firebase with service account key: {SERVICE_ACCOUNT_KEY_PATH}")
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        else:
            # Try to initialize with just the project ID
            print(f"Service account key not found, initializing Firebase with project ID: {FIREBASE_CONFIG['projectId']}")
            firebase_admin.initialize_app(options={
                'projectId': FIREBASE_CONFIG["projectId"]
            })
            db = firestore.client()
    except Exception as e:
        # Use mock implementation
        print(f"Error initializing Firebase: {str(e)}")
        print("Using mock Firestore implementation")
        db = MockFirestore()
        # Mock Query class for the mock implementation
        setattr(firestore, 'Query', type('MockQuery', (), {'DESCENDING': 'DESCENDING'}))

# Helper function to sanitize data for Firebase
def sanitize_data(data):
    """
    Recursively sanitize data to ensure it can be properly serialized to JSON
    by replacing Infinity, -Infinity, and NaN values with appropriate numbers.
    
    Args:
        data: The data to sanitize (can be a dict, list, or primitive value)
        
    Returns:
        The sanitized data
    """
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, float):
        # Replace Infinity, -Infinity, and NaN with appropriate values
        if data == float('inf'):
            return 1e9
        elif data == float('-inf'):
            return -1e9
        elif data != data:  # Check for NaN
            return 0
        return data
    else:
        return data

def save_post_data(post_id, post_data):
    """
    Save X post data to Firestore
    
    Args:
        post_id (str): The X post ID
        post_data (dict): The post data including engagement metrics and bot score
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add timestamp
        post_data['timestamp'] = datetime.now().isoformat()
        
        print(f"Saving post data for {post_id}: {post_data}")
        print(f"Follower range comparison in data: {'follower_range_comparison' in post_data}")
        
        # Sanitize data for Firebase
        sanitized_post_data = sanitize_data(post_data)
        
        # Save to Firestore
        db.collection('x_posts').document(post_id).set(sanitized_post_data)
        
        # Update average metrics if the post has follower count and engagement metrics
        if 'followers' in post_data and 'retweet_count' in post_data and 'favorite_count' in post_data and 'reply_count' in post_data and 'view_count' in post_data:
            update_average_metrics_for_range(post_data)
            
        return True
    except Exception as e:
        print(f"Error saving post data to Firestore: {str(e)}")
        return False

def get_post_data(post_id):
    """
    Retrieve X post data from Firestore
    
    Args:
        post_id (str): The X post ID
    
    Returns:
        dict: The post data if found, None otherwise
    """
    try:
        doc_ref = db.collection('x_posts').document(post_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"Retrieved post data for {post_id}: {data}")
            print(f"Follower range comparison in data: {'follower_range_comparison' in data}")
            return data
        print(f"No post data found for {post_id}")
        return None
    except Exception as e:
        print(f"Error retrieving post data from Firestore: {str(e)}")
        return None

def get_all_posts(limit=100):
    """
    Retrieve all X posts from Firestore
    
    Args:
        limit (int): Maximum number of posts to retrieve
    
    Returns:
        list: List of post data dictionaries
    """
    try:
        posts_ref = db.collection('x_posts').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = posts_ref.stream()
        
        posts = []
        for doc in docs:
            try:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                
                # Ensure timestamp is properly formatted
                if 'timestamp' in post_data:
                    # Convert any complex timestamp objects to strings
                    if not isinstance(post_data['timestamp'], (str, int, float)):
                        try:
                            # Try to convert to ISO format if it's a datetime
                            if hasattr(post_data['timestamp'], 'isoformat'):
                                post_data['timestamp'] = post_data['timestamp'].isoformat()
                            # If it's a Firestore timestamp
                            elif hasattr(post_data['timestamp'], 'seconds'):
                                post_data['timestamp'] = datetime.fromtimestamp(post_data['timestamp'].seconds).isoformat()
                            else:
                                # Convert to string as a fallback
                                post_data['timestamp'] = str(post_data['timestamp'])
                        except Exception as ts_error:
                            print(f"Error converting timestamp for post {doc.id}: {str(ts_error)}")
                            # Use a safe default
                            post_data['timestamp'] = str(post_data['timestamp'])
                
                posts.append(post_data)
            except Exception as post_error:
                print(f"Error processing post {doc.id}: {str(post_error)}")
                # Skip this post if there's an error
                continue
            
        return posts
    except Exception as e:
        print(f"Error retrieving all posts from Firestore: {str(e)}")
        print(traceback.format_exc())
        return []

def get_follower_range(follower_count):
    """
    Determine which follower range a given follower count falls into
    
    Args:
        follower_count (int): Number of followers
        
    Returns:
        dict: The follower range information
    """
    for range_info in FOLLOWER_RANGES:
        if range_info["min"] <= follower_count < range_info["max"]:
            return range_info
    
    # Default to the highest range if something goes wrong
    return FOLLOWER_RANGES[-1]

def update_average_metrics_for_range(post_data):
    """
    Update average metrics for the follower range of the post
    
    Args:
        post_data (dict): The post data including engagement metrics and follower count
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get follower count
        followers = post_data.get('followers', 0)
        
        # Find the follower range
        follower_range = None
        for fr in FOLLOWER_RANGES:
            if fr['min'] <= followers < fr['max']:
                follower_range = fr
                break
        
        if not follower_range:
            print(f"Could not find follower range for {followers} followers")
            return False
        
        # Get the follower range ID
        range_id = follower_range['id']
        
        # Get current average metrics for this range
        range_doc_ref = db.collection('follower_ranges').document(range_id)
        range_doc = range_doc_ref.get()
        
        # Extract metrics from post data
        retweet_count = post_data.get('retweet_count', 0)
        favorite_count = post_data.get('favorite_count', 0)
        reply_count = post_data.get('reply_count', 0)
        quote_count = post_data.get('quote_count', 0)
        view_count = post_data.get('view_count', 0)
        
        if range_doc.exists:
            # Update existing metrics
            range_data = range_doc.to_dict()
            
            # Get current values
            current_post_count = range_data.get('post_count', 0)
            current_total_retweets = range_data.get('total_retweets', 0)
            current_total_likes = range_data.get('total_likes', 0)
            current_total_replies = range_data.get('total_replies', 0)
            current_total_quotes = range_data.get('total_quotes', 0)
            current_total_views = range_data.get('total_views', 0)
            
            # Update totals
            new_post_count = current_post_count + 1
            new_total_retweets = current_total_retweets + retweet_count
            new_total_likes = current_total_likes + favorite_count
            new_total_replies = current_total_replies + reply_count
            new_total_quotes = current_total_quotes + quote_count
            new_total_views = current_total_views + view_count
            
            # Calculate new averages
            new_avg_retweets = new_total_retweets / new_post_count if new_post_count > 0 else 0
            new_avg_likes = new_total_likes / new_post_count if new_post_count > 0 else 0
            new_avg_replies = new_total_replies / new_post_count if new_post_count > 0 else 0
            new_avg_quotes = new_total_quotes / new_post_count if new_post_count > 0 else 0
            new_avg_views = new_total_views / new_post_count if new_post_count > 0 else 0
            
            # Prepare updated data
            updated_data = {
                'follower_range': follower_range,
                'post_count': new_post_count,
                'total_retweets': new_total_retweets,
                'total_likes': new_total_likes,
                'total_replies': new_total_replies,
                'total_quotes': new_total_quotes,
                'total_views': new_total_views,
                'avg_retweets': new_avg_retweets,
                'avg_likes': new_avg_likes,
                'avg_replies': new_avg_replies,
                'avg_quotes': new_avg_quotes,
                'avg_views': new_avg_views,
                'last_updated': datetime.now().isoformat()
            }
            
            # Sanitize data before saving to Firebase
            sanitized_data = sanitize_data(updated_data)
            
            # Update the document
            range_doc_ref.set(sanitized_data)
        else:
            # Create new average metrics document
            initial_data = {
                'post_count': 1,
                'total_retweets': retweet_count,
                'total_likes': favorite_count,
                'total_replies': reply_count,
                'total_quotes': quote_count,
                'total_views': view_count,
                'follower_range': follower_range,
                'last_updated': datetime.now().isoformat()
            }
            
            # Sanitize data before saving to Firebase
            sanitized_data = sanitize_data(initial_data)
            
            # Update the document
            range_doc_ref.set(sanitized_data)
        
        return True
    except Exception as e:
        print(f"Error updating average metrics: {str(e)}")
        return False

def get_average_metrics_for_follower_count(follower_count):
    """
    Get the average metrics for a given follower count
    
    Args:
        follower_count (int): Number of followers
        
    Returns:
        dict: Average metrics for the follower range
    """
    try:
        range_info = get_follower_range(follower_count)
        range_id = range_info["id"]
        
        avg_metrics_ref = db.collection('average_metrics').document(range_id)
        avg_metrics_doc = avg_metrics_ref.get()
        
        if avg_metrics_doc.exists:
            return avg_metrics_doc.to_dict()
        else:
            # Return default values if no metrics exist yet
            print(f"No metrics found for follower range {range_id}, using default values")
            
            # Set default avg_views based on follower range
            default_avg_views = 1000  # Default fallback
            if range_id == "under_2k":
                default_avg_views = 500
            elif range_id == "2k_to_6k":
                default_avg_views = 1500
            elif range_id == "6k_to_12k":
                default_avg_views = 4000
            elif range_id == "12k_to_25k":
                default_avg_views = 12000
            elif range_id == "25k_to_100k":
                default_avg_views = 40000
            elif range_id == "100k_to_500k":
                default_avg_views = 200000
            elif range_id == "over_500k":
                default_avg_views = 500000
            
            return {
                'post_count': 1,  # Changed from 0 to 1 to ensure ratios are calculated
                'avg_retweets': 10,
                'avg_likes': 50,
                'avg_replies': 5,
                'avg_quotes': 1,
                'avg_views': default_avg_views,
                'follower_range': range_info,
                'last_updated': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error getting average metrics: {str(e)}")
        # Return default values even when there's an error
        range_info = get_follower_range(follower_count)
        range_id = range_info["id"]
        print(f"Using fallback default values for follower range {range_id}")
        
        # Set default avg_views based on follower range
        default_avg_views = 1000  # Default fallback
        if range_id == "under_2k":
            default_avg_views = 500
        elif range_id == "2k_to_6k":
            default_avg_views = 1500
        elif range_id == "6k_to_12k":
            default_avg_views = 4000
        elif range_id == "12k_to_25k":
            default_avg_views = 12000
        elif range_id == "25k_to_100k":
            default_avg_views = 40000
        elif range_id == "100k_to_500k":
            default_avg_views = 200000
        elif range_id == "over_500k":
            default_avg_views = 500000
        
        return {
            'post_count': 1,
            'avg_retweets': 10,
            'avg_likes': 50,
            'avg_replies': 5,
            'avg_quotes': 1,
            'avg_views': default_avg_views,
            'follower_range': range_info,
            'last_updated': datetime.now().isoformat()
        }

def get_all_average_metrics():
    """
    Get all average metrics for all follower ranges
    
    Returns:
        dict: Dictionary of average metrics by follower range ID
    """
    try:
        avg_metrics_ref = db.collection('average_metrics')
        docs = avg_metrics_ref.stream()
        
        metrics = {}
        for doc in docs:
            metrics[doc.id] = doc.to_dict()
        
        # If we got no metrics, return default values
        if not metrics:
            print("No metrics found in database, using default values for all ranges")
            return get_default_metrics_for_all_ranges()
            
        return metrics
    except Exception as e:
        print(f"Error retrieving all average metrics: {str(e)}")
        print("Using default metrics for all follower ranges")
        return get_default_metrics_for_all_ranges()

def get_default_metrics_for_all_ranges():
    """
    Generate default metrics for all follower ranges
    
    Returns:
        dict: Dictionary of default metrics by follower range ID
    """
    default_metrics = {}
    for range_info in FOLLOWER_RANGES:
        range_id = range_info["id"]
        
        # Set default avg_views based on follower range
        default_avg_views = 1000  # Default fallback
        if range_id == "under_2k":
            default_avg_views = 500
        elif range_id == "2k_to_6k":
            default_avg_views = 1500
        elif range_id == "6k_to_12k":
            default_avg_views = 4000
        elif range_id == "12k_to_25k":
            default_avg_views = 12000
        elif range_id == "25k_to_100k":
            default_avg_views = 40000
        elif range_id == "100k_to_500k":
            default_avg_views = 200000
        elif range_id == "over_500k":
            default_avg_views = 500000
        
        default_metrics[range_id] = {
            'post_count': 1,
            'avg_retweets': 10,
            'avg_likes': 50,
            'avg_replies': 5,
            'avg_quotes': 1,
            'avg_views': default_avg_views,
            'follower_range': range_info,
            'last_updated': datetime.now().isoformat()
        }
    return default_metrics 