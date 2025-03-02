Write-Host "Starting Flask application..."

# Set environment variables
$env:FLASK_APP = "api.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Change to the project directory
Set-Location -Path "C:\CursorApps\BottingChecker\bottled-water"

# Run the Flask application
python api.py 