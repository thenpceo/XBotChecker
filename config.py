import os

from dotenv import load_dotenv

load_dotenv()

CONFIG = {
  'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY"),
  'DEBUG': False,  # Set to False for production
  'PORT': int(os.getenv("PORT", 5000)),
  'BLOCK_RESOURCE_TYPES': [
    'beacon',
    'csp_report',
    'font',
    'image',
    'imageset',
    'media',
    'object',
    'texttrack',
  ],
  'BLOCK_RESOURCE_NAMES': [
    'adzerk',
    'analytics',
    'cdn.api.twitter',
    'doubleclick',
    'exelator',
    'facebook',
    'fontawesome',
    'google',
    'google-analytics',
    'googletagmanager',
  ]   
}

# Gunicorn configuration for production
workers = int(os.environ.get('GUNICORN_PROCESSES', '2'))
threads = int(os.environ.get('GUNICORN_THREADS', '4'))
bind = os.environ.get('GUNICORN_BIND', f'0.0.0.0:{CONFIG["PORT"]}')
forwarded_allow_ips = '*'
secure_scheme_headers = { 'X-Forwarded-Proto': 'https' }