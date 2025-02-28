import json
import os
import re
import openai
import random
import time

from dotenv import load_dotenv
from hashlib import md5
from playwright.sync_api import sync_playwright, PlaywrightContextManager
from urllib.parse import urljoin, urlparse, urlunparse

from config import CONFIG

class Scraper:
    def __init__(self, cache_dir='./cache'):
        self.client = openai.OpenAI(api_key=CONFIG['OPENAI_API_KEY'])
        self.xhr_calls = {}
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_path(self, url, suffix=''):
        return os.path.join(self.cache_dir, md5((url + suffix).encode()).hexdigest() + '.json')

    def _cache_exists(self, url, suffix=''):
        return os.path.exists(self._get_cache_path(url, suffix))

    def _read_cache(self, url, suffix=''):
        with open(self._get_cache_path(url, suffix), 'r') as f:
            return json.load(f)

    def _write_cache(self, url, data, suffix=''):
        with open(self._get_cache_path(url, suffix), 'w') as f:
            json.dump(data, f)

    def intercept_route(self, route):
        """intercept all requests and abort blocked ones"""
        if route.request.resource_type in CONFIG['BLOCK_RESOURCE_TYPES']:
            return route.abort()
        if any(key in route.request.url for key in CONFIG['BLOCK_RESOURCE_NAMES']):
            return route.abort()
        return route.continue_()

    def intercept_response(self, response):
        """capture all background requests and save them"""
        if response.request.resource_type == "xhr":
            base_url = response.request.url
            self.xhr_calls[base_url] = response
        return response

    def get_relative_xhr_calls(self, base_url):
        """Get XHR calls relative to the given base URL"""
        relative_calls = {}
        for url, response in self.xhr_calls.items():
            relative_url = url.replace(base_url, '')
            relative_calls[relative_url] = response
        return relative_calls

    def get_url(self, url: str) -> str:
        """
        Format a potentially malformed Twitter URL into the proper format.
        """
        tweet_id_pattern = r'^(\d{10,25})$'
        username_pattern = r'^@?(\w{1,15})$'

        tweet_id_match = re.match(tweet_id_pattern, url)
        if tweet_id_match:
            return f"https://x.com/i/web/status/{tweet_id_match.group(1)}"

        username_match = re.match(username_pattern, url)
        if username_match:
            return f"https://x.com/{username_match.group(1)}"

        parsed_url = urlparse(url)

        if not parsed_url.scheme:
            parsed_url = parsed_url._replace(scheme="https")

        if not parsed_url.netloc or parsed_url.netloc not in ['x.com', 'twitter.com']:
            parsed_url = parsed_url._replace(netloc="x.com")

        if parsed_url.path.startswith('/twitter.com/'):
            parsed_url = parsed_url._replace(path=parsed_url.path.replace('/twitter.com', '', 1))

        if not parsed_url.path.startswith('/'):
            parsed_url = parsed_url._replace(path='/' + parsed_url.path)

        formatted_url = urlunparse(parsed_url)

        return formatted_url

    def get_selector(
        self, 
        pw: PlaywrightContextManager, 
        url: str,
        selector: str
    ):
        """Get the selector from the page using Playwright"""
        # Use non-headless mode to show the browser window
        browser = pw.chromium.launch(headless=False)
        
        # Create a context with more realistic browser settings
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        page = context.new_page()
        page.route("**/*", self.intercept_route)
        page.on("response", self.intercept_response)
        
        # Add a small delay before navigating to avoid detection
        time.sleep(random.uniform(1, 3))
        
        # Go to URL
        page.goto(url)
        
        # Wait for selector with a longer timeout
        page.wait_for_selector(selector, timeout=30000)
        
        # Add a small delay to ensure all XHR requests complete
        time.sleep(random.uniform(2, 4))

    def tweet(self, url: str) -> dict:
        """
        Scrape a single tweet page for Tweet thread e.g.:
        https://x.com/nftchance/status/1823923769183772993
        Return parent tweet, reply tweets and recommended tweets
        """
        try:
            print(f"Starting tweet scraping for URL: {url}")
            scrape_url = self.get_url(url)
            print(f"Formatted URL for scraping: {scrape_url}")
            
            if self._cache_exists(scrape_url):
                print(f"Using cached data for {scrape_url}")
                return self._read_cache(scrape_url)
            
            print(f"No cache found, scraping tweet data from {scrape_url}")
            with sync_playwright() as pw:
                try:
                    print(f"Waiting for tweet selector")
                    # Use non-headless mode to show the browser window
                    browser = pw.chromium.launch(headless=False)
                    
                    # Create a context with more realistic browser settings
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        locale="en-US",
                        timezone_id="America/New_York"
                    )
                    
                    page = context.new_page()
                    page.route("**/*", self.intercept_route)
                    page.on("response", self.intercept_response)
                    
                    # Add a small delay before navigating to avoid detection
                    time.sleep(random.uniform(1, 3))
                    
                    # Go to tweet URL
                    page.goto(scrape_url)
                    
                    # Wait for tweet to load with a longer timeout
                    page.wait_for_selector('[data-testid="tweet"]', timeout=30000)
                    
                    # Add a small delay to ensure all XHR requests complete
                    time.sleep(random.uniform(2, 4))
                    
                    print(f"Tweet selector found, checking XHR calls")
                    
                    tweet_calls = [f for f in self.get_relative_xhr_calls(scrape_url).values() if "TweetResultByRestId" in f.url]
                    print(f"Found {len(tweet_calls)} matching XHR calls")
                    
                    if not tweet_calls:
                        print(f"No matching XHR calls found for {scrape_url}")
                        return None
                        
                    for xhr in tweet_calls:
                        try:
                            data = xhr.json()
                            if 'data' not in data or 'tweetResult' not in data['data'] or 'result' not in data['data']['tweetResult']:
                                print(f"Unexpected JSON structure in XHR response: {data.keys()}")
                                continue
                                
                            result = data['data']['tweetResult']['result']
                            self._write_cache(scrape_url, result)
                            print(f"Successfully scraped and cached tweet data for {scrape_url}")
                            return result
                        except Exception as e:
                            print(f"Error processing XHR response: {str(e)}")
                            continue
                            
                    print(f"No valid tweet data found in any XHR calls for {scrape_url}")
                    return None
                except Exception as e:
                    print(f"Error during Playwright scraping: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
        except Exception as e:
            print(f"Error in tweet method: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def profile(self, url: str) -> dict:
        """
        Scrape a single profile page for profile info e.g.:
        https://x.com/nftchance
        Return profile info
        """
        try:
            print(f"Starting profile scraping for URL: {url}")
            scrape_url = self.get_url(url)
            print(f"Formatted URL for scraping: {scrape_url}")
            
            if self._cache_exists(scrape_url):
                print(f"Using cached data for {scrape_url}")
                return self._read_cache(scrape_url)
            
            print(f"No cache found, scraping profile data from {scrape_url}")
            with sync_playwright() as pw:
                try:
                    # Use non-headless mode to show the browser window
                    browser = pw.chromium.launch(headless=False)
                    
                    # Create a context with more realistic browser settings
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        locale="en-US",
                        timezone_id="America/New_York"
                    )
                    
                    page = context.new_page()
                    page.route("**/*", self.intercept_route)
                    page.on("response", self.intercept_response)
                    
                    # Add a small delay before navigating to avoid detection
                    time.sleep(random.uniform(1, 3))
                    
                    # Go to profile URL
                    page.goto(scrape_url)
                    
                    # Wait for profile to load with a longer timeout
                    page.wait_for_selector('[data-testid="primaryColumn"]', timeout=30000)
                    
                    # Add a small delay to ensure all XHR requests complete
                    time.sleep(random.uniform(2, 4))
                    
                    print(f"Profile selector found, checking XHR calls")
                    
                    tweet_calls = [f for f in self.get_relative_xhr_calls(scrape_url).values() if "UserByScreenName" in f.url]
                    print(f"Found {len(tweet_calls)} matching XHR calls")
                    
                    if not tweet_calls:
                        print(f"No matching XHR calls found for {scrape_url}")
                        return None
                        
                    for xhr in tweet_calls:
                        try:
                            data = xhr.json()
                            if 'data' not in data or 'user' not in data['data'] or 'result' not in data['data']['user']:
                                print(f"Unexpected JSON structure in XHR response: {data.keys()}")
                                continue
                                
                            result = data['data']['user']['result']
                            self._write_cache(scrape_url, result)
                            print(f"Successfully scraped and cached profile data for {scrape_url}")
                            return result
                        except Exception as e:
                            print(f"Error processing XHR response: {str(e)}")
                            continue
                            
                    print(f"No valid profile data found in any XHR calls for {scrape_url}")
                    return None
                except Exception as e:
                    print(f"Error during Playwright scraping: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
        except Exception as e:
            print(f"Error in profile method: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def call(self, url: str) -> dict:
        """
        Determine if the URL is a tweet or profile and call the appropriate function
        """
        scrape_url = self.get_url(url)
        
        if self._cache_exists(scrape_url):
            print(f"Using cached data for {scrape_url}")
            return self._read_cache(scrape_url)
        
        if scrape_url.startswith('https://x.com/i/web/status/'):
            return self.tweet(scrape_url)
        elif scrape_url.startswith('https://x.com/'):
            return self.profile(scrape_url)
        else:
            raise ValueError(f"Invalid URL: {scrape_url}")


    def _extract(self, data: dict) -> dict:
        """
        Extract tweet data from the scraped page
        """
        try:
            print(f"Starting data extraction")
            extracted = {}
            
            if not data:
                print("No data provided for extraction")
                return {}
                
            print(f"Data keys: {data.keys()}")
            
            # Helper function to safely convert values to int
            def safe_int(value, default=0):
                try:
                    if value is None:
                        return default
                    return int(value)
                except (ValueError, TypeError):
                    # If the value is a string like "1.2K", try to parse it
                    if isinstance(value, str):
                        value = value.strip().upper()
                        if value.endswith('K'):
                            try:
                                return int(float(value[:-1]) * 1000)
                            except (ValueError, TypeError):
                                pass
                        elif value.endswith('M'):
                            try:
                                return int(float(value[:-1]) * 1000000)
                            except (ValueError, TypeError):
                                pass
                    print(f"Could not convert {value} to int, using default {default}")
                    return default
            
            # Extract tweet data
            if 'legacy' in data:
                print("Extracting legacy tweet data")
                extracted = {
                    'text': data['legacy'].get('full_text', ''),
                    'created_at': data['legacy'].get('created_at', ''),
                    'retweet_count': safe_int(data['legacy'].get('retweet_count', 0)),
                    'favorite_count': safe_int(data['legacy'].get('favorite_count', 0)),
                    'reply_count': safe_int(data['legacy'].get('reply_count', 0)),
                    'quote_count': safe_int(data['legacy'].get('quote_count', 0)),
                }
                
                # Try to extract view count (impressions) with more detailed debugging
                view_count = 0
                view_count_source = None
                
                # Check all possible locations for view count
                if 'views' in data:
                    print(f"Found view count in 'views': {data['views']}")
                    if isinstance(data['views'], dict) and 'count' in data['views']:
                        view_count = safe_int(data['views'].get('count', 0))
                        view_count_source = 'views.count'
                    elif isinstance(data['views'], (int, str)):
                        view_count = safe_int(data['views'])
                        view_count_source = 'views (direct)'
                
                if view_count == 0 and 'ext' in data:
                    print(f"Checking 'ext' for view count. Keys in ext: {list(data['ext'].keys())}")
                    if 'viewCount' in data['ext']:
                        print(f"Found view count in 'ext.viewCount': {data['ext']['viewCount']}")
                        if isinstance(data['ext']['viewCount'], dict):
                            if 'r' in data['ext']['viewCount'] and 'ok' in data['ext']['viewCount']['r']:
                                view_count = safe_int(data['ext']['viewCount']['r']['ok'].get('viewCount', 0))
                                view_count_source = 'ext.viewCount.r.ok.viewCount'
                        elif isinstance(data['ext']['viewCount'], (int, str)):
                            view_count = safe_int(data['ext']['viewCount'])
                            view_count_source = 'ext.viewCount (direct)'
                
                if view_count == 0 and 'legacy' in data:
                    print(f"Checking 'legacy' for view count. Keys in legacy: {list(data['legacy'].keys())}")
                    if 'ext_views' in data['legacy']:
                        print(f"Found view count in 'legacy.ext_views': {data['legacy']['ext_views']}")
                        if isinstance(data['legacy']['ext_views'], dict) and 'count' in data['legacy']['ext_views']:
                            view_count = safe_int(data['legacy']['ext_views'].get('count', 0))
                            view_count_source = 'legacy.ext_views.count'
                        elif isinstance(data['legacy']['ext_views'], (int, str)):
                            view_count = safe_int(data['legacy']['ext_views'])
                            view_count_source = 'legacy.ext_views (direct)'
                
                if view_count == 0 and 'view_count' in data:
                    print(f"Found direct view_count: {data['view_count']}")
                    view_count = safe_int(data['view_count'])
                    view_count_source = 'view_count'
                
                if view_count == 0 and 'impression_count' in data:
                    print(f"Found impression_count: {data['impression_count']}")
                    view_count = safe_int(data['impression_count'])
                    view_count_source = 'impression_count'
                
                # Check for view count in metrics
                if view_count == 0 and 'metrics' in data:
                    print(f"Checking 'metrics' for view count. Keys in metrics: {list(data['metrics'].keys()) if isinstance(data['metrics'], dict) else 'metrics is not a dict'}")
                    if isinstance(data['metrics'], dict):
                        if 'impressions' in data['metrics']:
                            view_count = safe_int(data['metrics'].get('impressions', 0))
                            view_count_source = 'metrics.impressions'
                        elif 'views' in data['metrics']:
                            view_count = safe_int(data['metrics'].get('views', 0))
                            view_count_source = 'metrics.views'
                
                # Check for view count in stats
                if view_count == 0 and 'stats' in data:
                    print(f"Checking 'stats' for view count. Keys in stats: {list(data['stats'].keys()) if isinstance(data['stats'], dict) else 'stats is not a dict'}")
                    if isinstance(data['stats'], dict):
                        if 'impressions' in data['stats']:
                            view_count = safe_int(data['stats'].get('impressions', 0))
                            view_count_source = 'stats.impressions'
                        elif 'views' in data['stats']:
                            view_count = safe_int(data['stats'].get('views', 0))
                            view_count_source = 'stats.views'
                
                if view_count > 0:
                    print(f"Successfully extracted view count: {view_count} from source: {view_count_source}")
                    extracted['view_count'] = view_count
                else:
                    # Log that we couldn't find view count
                    print("View count not found in tweet data after checking all possible locations")
                    print("Available keys in data:", list(data.keys()))
                    if 'ext' in data:
                        print("Available keys in data['ext']:", list(data['ext'].keys()))
                    if 'legacy' in data:
                        print("Available keys in data['legacy']:", list(data['legacy'].keys()))
                    # Set a default value
                    extracted['view_count'] = 0
            else:
                print("No legacy data found in tweet")
                
            # Extract user data
            if 'core' in data and 'user_results' in data['core'] and 'result' in data['core']['user_results']:
                print("Extracting user data")
                user_data = data['core']['user_results']['result']
                
                # Check for various verification indicators
                is_verified = False
                is_blue_verified = False
                verification_info = {}
                
                if 'is_blue_verified' in user_data:
                    is_blue_verified = user_data['is_blue_verified']
                    verification_info['is_blue_verified'] = is_blue_verified
                
                if 'legacy' in user_data:
                    legacy_verified = user_data['legacy'].get('verified', False)
                    verification_info['legacy_verified'] = legacy_verified
                    is_verified = is_verified or legacy_verified
                
                if 'verification_info' in user_data:
                    verification_info['details'] = user_data['verification_info']
                    is_verified = True
                
                # Check for blue checkmark in the user data
                if 'has_nft_avatar' in user_data:
                    verification_info['has_nft_avatar'] = user_data.get('has_nft_avatar', False)
                
                # Add professional category if available
                if 'professional' in user_data:
                    verification_info['professional_category'] = user_data['professional'].get('category', '')
                
                if 'legacy' in user_data:
                    screen_name = user_data['legacy'].get('screen_name', '')
                    
                    # Special case for well-known accounts
                    well_known_accounts = {
                        'elonmusk': {
                            'is_verified': True,
                            'is_well_known': True,
                            'real_name': 'Elon Musk',
                            'description': 'CEO of Tesla, SpaceX, X, and other companies'
                        },
                        'BillGates': {
                            'is_verified': True,
                            'is_well_known': True,
                            'real_name': 'Bill Gates',
                            'description': 'Co-founder of Microsoft'
                        },
                        'BarackObama': {
                            'is_verified': True,
                            'is_well_known': True,
                            'real_name': 'Barack Obama',
                            'description': 'Former President of the United States'
                        }
                    }
                    
                    # Check if this is a well-known account
                    if screen_name.lower() in well_known_accounts:
                        print(f"Detected well-known account: {screen_name}")
                        account_info = well_known_accounts[screen_name.lower()]
                        is_verified = account_info['is_verified']
                        verification_info['is_well_known'] = account_info['is_well_known']
                        verification_info['real_name'] = account_info['real_name']
                    
                    extracted.update({
                        'followers': user_data['legacy'].get('followers_count', 0),
                        'following': user_data['legacy'].get('friends_count', 0),
                        'tweets': user_data['legacy'].get('statuses_count', 0),
                        'verified': is_verified,
                        'verification_info': verification_info,
                        'name': user_data['legacy'].get('name', ''),
                        'screen_name': screen_name,
                        'description': user_data['legacy'].get('description', ''),
                        'created_at': user_data['legacy'].get('created_at', ''),
                    })
                else:
                    print("No legacy data found in user data")
            else:
                print("No user data found in tweet")
                
            print(f"Extracted data: {extracted}")
            return extracted
        except Exception as e:
            print(f"Error in _extract method: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}

    def analyze(self, url: str) -> dict:
        """
        Analyze the provided data using OpenAI
        """
        try:
            print(f"Starting analysis for URL: {url}")
            scrape_url = self.get_url(url)
            print(f"Formatted URL: {scrape_url}")
            analysis_cache_suffix = '_analysis'

            if self._cache_exists(scrape_url, analysis_cache_suffix):
                print(f"Using cached analysis for {scrape_url}")
                return self._read_cache(scrape_url, analysis_cache_suffix)

            print(f"Fetching tweet data for {scrape_url}")
            tweet_data = self.tweet(scrape_url)
            
            if not tweet_data:
                print(f"No tweet data found for {scrape_url}")
                return {"error": "No tweet data found"}
                
            print(f"Extracting data from tweet")
            extracted_data = self._extract(tweet_data)
            
            if not extracted_data:
                print(f"Failed to extract data from tweet {scrape_url}")
                return {"error": "Failed to extract data from tweet"}
            
            # Get user's screen name
            screen_name = extracted_data.get('screen_name', '')
            
            # Get user's timeline and calculate average engagement
            engagement_comparison = {}
            if screen_name:
                print(f"Getting timeline data for user: {screen_name}")
                timeline_data = self.get_user_timeline(screen_name)
                
                if timeline_data:
                    avg_engagement = self.calculate_average_engagement(timeline_data)
                    
                    if avg_engagement:
                        # Calculate engagement ratios
                        current_retweets = extracted_data.get('retweet_count', 0)
                        current_likes = extracted_data.get('favorite_count', 0)
                        current_replies = extracted_data.get('reply_count', 0)
                        current_quotes = extracted_data.get('quote_count', 0)
                        current_views = extracted_data.get('view_count', 0)
                        
                        avg_retweets = avg_engagement.get('avg_retweets', 0)
                        avg_likes = avg_engagement.get('avg_likes', 0)
                        avg_replies = avg_engagement.get('avg_replies', 0)
                        avg_quotes = avg_engagement.get('avg_quotes', 0)
                        avg_views = avg_engagement.get('avg_views', 0)
                        
                        # Avoid division by zero
                        retweet_ratio = current_retweets / avg_retweets if avg_retweets > 0 else 0
                        like_ratio = current_likes / avg_likes if avg_likes > 0 else 0
                        reply_ratio = current_replies / avg_replies if avg_replies > 0 else 0
                        quote_ratio = current_quotes / avg_quotes if avg_quotes > 0 else 0
                        view_ratio = current_views / avg_views if avg_views > 0 else 0
                        
                        # Calculate retweet-to-reply ratio (a high value can indicate botting)
                        retweet_to_reply_ratio = current_retweets / current_replies if current_replies > 0 else 0
                        
                        # Calculate view-to-follower ratio (a high value can indicate botting)
                        followers = extracted_data.get('followers', 1)  # Default to 1 to avoid division by zero
                        view_to_follower_ratio = current_views / followers if followers > 0 else 0
                        
                        engagement_comparison = {
                            'avg_engagement': avg_engagement,
                            'engagement_ratios': {
                                'retweet_ratio': retweet_ratio,
                                'like_ratio': like_ratio,
                                'reply_ratio': reply_ratio,
                                'quote_ratio': quote_ratio,
                                'view_ratio': view_ratio,
                                'retweet_to_reply_ratio': retweet_to_reply_ratio,
                                'view_to_follower_ratio': view_to_follower_ratio
                            }
                        }
                        
                        # Add engagement comparison to extracted data
                        extracted_data['engagement_comparison'] = engagement_comparison
                        
                        print(f"Added engagement comparison: {engagement_comparison}")

            try:
                print(f"Sending data to OpenAI for analysis")
                message = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are analyzing Twitter/X metrics to determine if a tweet's engagement appears to be botted. Provide a score out of 100 (100 being definitely botted) and a short explanation.\n\nImportant context:\n1. Twitter/X changed its verification system in 2023. The 'verified' field in the data may not be reliable as many legitimate accounts (including Elon Musk's) might show as 'unverified' in the API. We should still check if an account has the new blue verified checkmark, as unverified accounts are more likely botting.\n2. For well-known accounts like Elon Musk (@elonmusk), high follower counts are expected and not indicative of bot activity.\n3. The MOST IMPORTANT ratio to check is the engagement-to-views ratio. Botted posts typically have very high view counts with disproportionately low engagement (likes, retweets, replies). A post with 50,000 views but only 10 likes is highly suspicious.\n4. IMPORTANT: Low engagement relative to views or followers is NOT an indicator of botting. We're ONLY looking for disproportionately HIGH view counts compared to engagement. For example, a post with 2 comments and 20 likes should have around 1,000 views. If it has 15,000+ views, it's likely botted. But if it has fewer views than expected, that's completely normal and NOT botted.\n5. Expected view ranges based on follower count: Accounts with ~500 followers typically get around 200-1,500 views. Accounts with ~20,000 followers typically get around 3,000-10,000 views. Viral outliers are exceptions.\n6. If available, compare the current tweet's engagement with the user's average engagement. A sudden spike in engagement compared to the user's typical metrics is a strong indicator of potential bot activity.\n7. Pay special attention to the retweet-to-like ratio - normal posts typically have fewer retweets than likes, while botted posts often have as many or more retweets than likes. A high retweet-to-like ratio is a strong indicator of bot activity.\n8. Consider the account's history (tweet count) and follower-to-following ratio as secondary factors.\n9. Keep in mind the date the account was made. Often accounts that are botting have been made within a month.\n\nYour response should be in the format: 'Score: X/100\\n\\nExplanation: Your explanation here'"},
                        {"role": "user", "content": json.dumps(extracted_data, indent=2)}
                    ],
                    max_tokens=1000,
                    temperature=0.5
                )

                text = message.choices[0].message.content
                print(f"Received response from OpenAI: {text}")
                
                score_match = re.search(r'Score: (\d+)/100', text)
                score = int(score_match.group(1)) if score_match else 0  # Default to 0 if no score found
                explanation = text.split("Explanation:", 1)[-1].strip() if "Explanation:" in text else text

                analysis_result = {
                    "score": score,
                    "explanation": explanation
                }
                
                # Add engagement comparison to the result
                if engagement_comparison:
                    analysis_result['engagement_comparison'] = engagement_comparison
                
                # Add tweet metrics to the result
                analysis_result['retweet_count'] = extracted_data.get('retweet_count', 0)
                analysis_result['favorite_count'] = extracted_data.get('favorite_count', 0)
                analysis_result['reply_count'] = extracted_data.get('reply_count', 0)
                analysis_result['quote_count'] = extracted_data.get('quote_count', 0)
                analysis_result['view_count'] = extracted_data.get('view_count', 0)
                
                print(f"Final analysis result with metrics: {analysis_result}")
                print(f"View count in analysis result: {analysis_result.get('view_count', 'NOT FOUND')}")

                self._write_cache(scrape_url, analysis_result, analysis_cache_suffix)
                print(f"Analysis complete and cached for {scrape_url}")

                return analysis_result
            except Exception as e:
                print(f"OpenAI API error: {str(e)}")
                return {"error": f"OpenAI API error: {str(e)}"}
        except Exception as e:
            print(f"An error occurred during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def get_user_timeline(self, screen_name: str) -> list:
        """
        Fetch a user's recent tweets to calculate average engagement
        """
        try:
            print(f"Fetching timeline for user: {screen_name}")
            user_url = f"https://x.com/{screen_name}"
            timeline_cache_suffix = '_timeline'
            
            if self._cache_exists(user_url, timeline_cache_suffix):
                print(f"Using cached timeline for {screen_name}")
                return self._read_cache(user_url, timeline_cache_suffix)
            
            print(f"No cache found, scraping timeline data for {screen_name}")
            with sync_playwright() as pw:
                try:
                    # Use non-headless mode to show the browser window
                    browser = pw.chromium.launch(headless=False)
                    
                    # Create a context with more realistic browser settings
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        locale="en-US",
                        timezone_id="America/New_York"
                    )
                    
                    page = context.new_page()
                    page.route("**/*", self.intercept_route)
                    page.on("response", self.intercept_response)
                    
                    # Add a small delay before navigating to avoid detection
                    time.sleep(random.uniform(1, 3))
                    
                    # Go to user profile
                    page.goto(user_url)
                    
                    # Wait for tweets to load with a longer timeout
                    print(f"Waiting for timeline to load")
                    page.wait_for_selector('[data-testid="tweet"]', timeout=30000)
                    
                    # Add a small delay to ensure all XHR requests complete
                    time.sleep(random.uniform(2, 4))
                    
                    # Check for timeline API calls
                    print(f"Checking for timeline API calls")
                    timeline_calls = [f for f in self.get_relative_xhr_calls(user_url).values() 
                                     if "UserTweets" in f.url or "UserMedia" in f.url]
                    
                    print(f"Found {len(timeline_calls)} timeline API calls")
                    
                    if not timeline_calls:
                        print(f"No timeline data found for {screen_name}")
                        return []
                    
                    timeline_data = []
                    for xhr in timeline_calls:
                        try:
                            data = xhr.json()
                            if 'data' in data and 'user' in data['data'] and 'result' in data['data']['user']:
                                user_data = data['data']['user']['result']
                                if 'timeline_v2' in user_data and 'timeline' in user_data['timeline_v2']:
                                    timeline = user_data['timeline_v2']['timeline']
                                    if 'instructions' in timeline:
                                        for instruction in timeline['instructions']:
                                            if 'entries' in instruction:
                                                for entry in instruction['entries']:
                                                    if 'content' in entry and 'itemContent' in entry['content']:
                                                        if 'tweet_results' in entry['content']['itemContent']:
                                                            tweet_result = entry['content']['itemContent']['tweet_results']
                                                            if 'result' in tweet_result:
                                                                timeline_data.append(tweet_result['result'])
                        except Exception as e:
                            print(f"Error processing timeline XHR response: {str(e)}")
                            continue
                    
                    if timeline_data:
                        self._write_cache(user_url, timeline_data, timeline_cache_suffix)
                        print(f"Successfully scraped and cached timeline data for {screen_name}")
                    
                    return timeline_data
                except Exception as e:
                    print(f"Error during timeline scraping: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return []
        except Exception as e:
            print(f"Error in get_user_timeline method: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def calculate_average_engagement(self, timeline_data: list) -> dict:
        """
        Calculate average engagement metrics from timeline data
        """
        try:
            print(f"Calculating average engagement from {len(timeline_data)} tweets")
            
            if not timeline_data:
                print("No timeline data provided for engagement calculation")
                return {}
            
            # Helper function to safely convert values to int
            def safe_int(value, default=0):
                try:
                    if value is None:
                        return default
                    return int(value)
                except (ValueError, TypeError):
                    # If the value is a string like "1.2K", try to parse it
                    if isinstance(value, str):
                        value = value.strip().upper()
                        if value.endswith('K'):
                            try:
                                return int(float(value[:-1]) * 1000)
                            except (ValueError, TypeError):
                                pass
                        elif value.endswith('M'):
                            try:
                                return int(float(value[:-1]) * 1000000)
                            except (ValueError, TypeError):
                                pass
                    print(f"Could not convert {value} to int, using default {default}")
                    return default
            
            # Initialize counters
            total_tweets = 0
            total_retweets = 0
            total_likes = 0
            total_replies = 0
            total_quotes = 0
            total_views = 0
            
            # Process each tweet
            for tweet in timeline_data:
                if 'legacy' in tweet:
                    total_tweets += 1
                    total_retweets += safe_int(tweet['legacy'].get('retweet_count', 0))
                    total_likes += safe_int(tweet['legacy'].get('favorite_count', 0))
                    total_replies += safe_int(tweet['legacy'].get('reply_count', 0))
                    total_quotes += safe_int(tweet['legacy'].get('quote_count', 0))
                    
                    # Try to extract view count from different possible locations
                    tweet_views = 0
                    if 'views' in tweet:
                        if isinstance(tweet['views'], dict) and 'count' in tweet['views']:
                            tweet_views = safe_int(tweet['views'].get('count', 0))
                        elif isinstance(tweet['views'], (int, str)):
                            tweet_views = safe_int(tweet['views'])
                    elif 'ext' in tweet and 'viewCount' in tweet['ext']:
                        if isinstance(tweet['ext']['viewCount'], dict):
                            if 'r' in tweet['ext']['viewCount'] and 'ok' in tweet['ext']['viewCount']['r']:
                                tweet_views = safe_int(tweet['ext']['viewCount']['r']['ok'].get('viewCount', 0))
                        elif isinstance(tweet['ext']['viewCount'], (int, str)):
                            tweet_views = safe_int(tweet['ext']['viewCount'])
                    elif 'ext_views' in tweet['legacy']:
                        if isinstance(tweet['legacy']['ext_views'], dict) and 'count' in tweet['legacy']['ext_views']:
                            tweet_views = safe_int(tweet['legacy']['ext_views'].get('count', 0))
                        elif isinstance(tweet['legacy']['ext_views'], (int, str)):
                            tweet_views = safe_int(tweet['legacy']['ext_views'])
                    
                    total_views += tweet_views
            
            # Calculate averages
            if total_tweets > 0:
                avg_engagement = {
                    'avg_retweets': total_retweets / total_tweets,
                    'avg_likes': total_likes / total_tweets,
                    'avg_replies': total_replies / total_tweets,
                    'avg_quotes': total_quotes / total_tweets,
                    'avg_views': total_views / total_tweets,
                    'total_tweets_analyzed': total_tweets
                }
                print(f"Average engagement metrics: {avg_engagement}")
                return avg_engagement
            else:
                print("No valid tweets found for engagement calculation")
                return {}
        except Exception as e:
            print(f"Error in calculate_average_engagement method: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}