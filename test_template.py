import requests
import re

def check_template():
    response = requests.get('http://localhost:5000/')
    content = response.text
    
    # Check for specific elements in our updated template
    has_bot_likelihood = 'Bot Likelihood' in content
    has_engagement_comparison = 'Engagement Comparison' in content
    has_search_icon = 'fas fa-search me-2' in content
    has_chart_icon = 'fas fa-chart-bar me-2' in content
    has_info_icon = 'fas fa-info-circle me-2' in content
    
    print(f"Response status code: {response.status_code}")
    print(f"Content length: {len(content)} bytes")
    print(f"Contains 'Bot Likelihood': {has_bot_likelihood}")
    print(f"Contains 'Engagement Comparison': {has_engagement_comparison}")
    print(f"Contains search icon: {has_search_icon}")
    print(f"Contains chart icon: {has_chart_icon}")
    print(f"Contains info icon: {has_info_icon}")
    
    # Check if it's using the updated template
    if has_bot_likelihood and has_engagement_comparison and has_search_icon and has_chart_icon and has_info_icon:
        print("\nSUCCESS: The updated template is being served!")
    else:
        print("\nFAILURE: The updated template is NOT being served correctly.")

if __name__ == "__main__":
    check_template() 