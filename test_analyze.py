from scraper import Scraper
import json
import requests

def test_analyze():
    scraper = Scraper()
    
    # Test with a valid tweet ID
    tweet_id = "1878005965489906077"  # Replace with a valid tweet ID
    
    print(f"Testing analyze method with tweet ID: {tweet_id}")
    
    try:
        result = scraper.analyze(tweet_id)
        print(f"Analysis result: {json.dumps(result, indent=2)}")
        
        # Check if the result contains the expected fields
        expected_fields = ['score', 'explanation', 'retweet_count', 'favorite_count', 'reply_count', 'view_count']
        missing_fields = [field for field in expected_fields if field not in result]
        
        if missing_fields:
            print(f"Warning: Missing fields in result: {missing_fields}")
        else:
            print("All expected fields are present in the result.")
            
        return result
    except Exception as e:
        print(f"Error analyzing tweet: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_api():
    print("\n--- Testing API Endpoints ---")
    
    # Test the mock endpoint
    print("\nTesting mock endpoint...")
    try:
        response = requests.get("http://localhost:5000/?id=mock&analyze=true")
        if response.status_code == 200:
            data = response.json()
            print(f"Mock API response: {json.dumps(data, indent=2)}")
            
            # Check if the result contains the expected fields
            expected_fields = ['score', 'explanation', 'retweet_count', 'favorite_count', 'reply_count', 'view_count']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"Warning: Missing fields in result: {missing_fields}")
            else:
                print("All expected fields are present in the mock response.")
        else:
            print(f"Error: API returned status code {response.status_code}")
    except Exception as e:
        print(f"Error testing mock API: {str(e)}")
    
    # Test with a real tweet ID
    print("\nTesting API with real tweet ID...")
    tweet_id = "1878005965489906077"
    try:
        response = requests.get(f"http://localhost:5000/?id={tweet_id}&analyze=true")
        if response.status_code == 200:
            data = response.json()
            print(f"API response: {json.dumps(data, indent=2)}")
            
            # Check if the result contains the expected fields
            expected_fields = ['score', 'explanation', 'retweet_count', 'favorite_count', 'reply_count', 'view_count']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"Warning: Missing fields in result: {missing_fields}")
            else:
                print("All expected fields are present in the API response.")
        else:
            print(f"Error: API returned status code {response.status_code}")
    except Exception as e:
        print(f"Error testing API: {str(e)}")

if __name__ == "__main__":
    # Test the scraper directly
    test_analyze()
    
    # Test the API endpoints
    test_api() 