import json
import os
import random
import time
from hashlib import md5

# Try to import OpenAI, but don't fail if it's not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import CONFIG

class Scraper:
    def __init__(self, cache_dir='./cache'):
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if OPENAI_AVAILABLE and CONFIG.get('OPENAI_API_KEY'):
            try:
                self.openai_client = openai.OpenAI(api_key=CONFIG['OPENAI_API_KEY'])
            except Exception as e:
                pass
        
        # Set up cache directory
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir)
            except Exception:
                # Use a temporary directory if we can't create the cache directory
                self.cache_dir = os.path.join('/tmp', 'cache')
                if not os.path.exists(self.cache_dir):
                    try:
                        os.makedirs(self.cache_dir)
                    except:
                        # If we still can't create a cache directory, disable caching
                        self.cache_dir = None

    def _get_cache_path(self, url, suffix=''):
        if not self.cache_dir:
            return None
        url_hash = md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}{suffix}.json")

    def _cache_exists(self, url, suffix=''):
        cache_path = self._get_cache_path(url, suffix)
        return cache_path and os.path.exists(cache_path)

    def _read_cache(self, url, suffix=''):
        cache_path = self._get_cache_path(url, suffix)
        if not cache_path:
            return None
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _write_cache(self, url, data, suffix=''):
        cache_path = self._get_cache_path(url, suffix)
        if not cache_path:
            return
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def analyze(self, url: str) -> dict:
        """
        Analyze a tweet URL using OpenAI
        
        For Vercel deployment, this is a simplified version that returns mock data
        since Playwright is difficult to run in a serverless environment.
        """
        # Check if we have cached results
        if self._cache_exists(url, '_analysis'):
            cached_data = self._read_cache(url, '_analysis')
            if cached_data:
                return cached_data
            
        try:
            # For Vercel deployment, return mock data
            # In a real implementation, you would use a different approach to get tweet data
            # such as using the Twitter API or a simpler HTTP client
            
            # Generate a random score between 10 and 90
            score = random.randint(10, 90)
            
            # Create an explanation based on the score
            if score < 30:
                explanation = "This account shows low signs of botting activity. The engagement patterns appear organic and consistent with human behavior."
            elif score < 70:
                explanation = "This account shows moderate signs of potential botting activity. There are some unusual engagement patterns that could indicate automated behavior."
            else:
                explanation = "This account shows strong signs of botting activity. The engagement patterns are highly unusual and consistent with automated behavior."
                
            # Create a result object
            result = {
                "score": score,
                "explanation": explanation,
                "retweet_count": random.randint(50, 5000),
                "favorite_count": random.randint(100, 10000),
                "reply_count": random.randint(10, 1000),
                "view_count": random.randint(1000, 100000),
                "user_info": {
                    "name": "Example User",
                    "screen_name": "exampleuser",
                    "profile_image_url": "https://abs.twimg.com/sticky/default_profile_images/default_profile_400x400.png"
                },
                "text": "This is an example tweet for demonstration purposes.",
                "engagement_comparison": {
                    "avg_engagement": {
                        "avg_retweets": random.randint(20, 2000),
                        "avg_likes": random.randint(50, 5000),
                        "avg_replies": random.randint(5, 500),
                        "avg_views": random.randint(500, 50000)
                    }
                }
            }
            
            # Cache the result
            self._write_cache(url, result, '_analysis')
            
            return result
        except Exception as e:
            return {
                "error": f"Error analyzing tweet: {str(e)}",
                "score": 0,
                "explanation": f"Error analyzing tweet: {str(e)}. Please try another tweet ID.",
                "retweet_count": 0,
                "favorite_count": 0,
                "reply_count": 0,
                "view_count": 0,
                "user_info": {
                    "name": "Error",
                    "screen_name": "error",
                    "profile_image_url": "https://abs.twimg.com/sticky/default_profile_images/default_profile_400x400.png"
                },
                "text": "Error analyzing tweet.",
                "engagement_comparison": {
                    "avg_engagement": {
                        "avg_retweets": 0,
                        "avg_likes": 0,
                        "avg_replies": 0,
                        "avg_views": 0
                    }
                }
            } 