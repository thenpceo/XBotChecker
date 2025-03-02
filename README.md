# 💧 X Bot Checker

Analyze X (formerly Twitter) posts to detect botted engagement and activity.

## Overview

This application allows you to analyze X posts for signs of bot activity. It provides a score and detailed explanation based on engagement metrics and comparison with similar accounts.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Copy `example.env` to `.env`
   - Add your OpenAI API key to the `.env` file

## Firebase Setup

This application uses Firebase Firestore to store X post data. To set up Firebase:

1. Create a Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/)
2. Generate a service account key:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save the JSON file as `firebase-key.json` in the root directory of the project
3. The Firebase configuration is already set up in `firebase_config.py`

## Running the Application

### Development

```
python api.py
```

This will start a Flask development server at http://localhost:5000

### Production

```
gunicorn --config config.py api:api
```

## Project Structure

```
x-bot-checker/
├─ api.py - Main Flask application
├─ scraper.py - X scraper using Playwright
├─ firebase_config.py - Firebase database configuration
├─ config.py - Application configuration
├─ index.py - Vercel deployment entry point
├─ vercel_scraper.py - Simplified scraper for Vercel
├─ templates/ - HTML templates
│  ├─ new_x_template.html - Main UI template
│  ├─ index.html - Alternative UI template
│  ├─ posts.html - Admin view of analyzed posts
│  ├─ login.html - Admin login page
├─ static/ - Static assets
├─ cache/ - Local cache for scraped data
├─ .env - Environment variables
├─ requirements.txt - Python dependencies
```

## API Usage

Submit a GET request to analyze a post:
```
http://localhost:5000/?id={POST_ID}&analyze=true
```

Example response:
```json
{
  "score": 75,
  "explanation": "This post shows signs of potential bot activity based on the engagement patterns...",
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
  }
}
```
