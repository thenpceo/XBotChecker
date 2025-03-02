@echo off
echo Setting up the environment and running the application...

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Run the Flask application
set FLASK_APP=api.py
set FLASK_ENV=development
set FLASK_DEBUG=1
python -m flask run --host=0.0.0.0 --port=5000

pause 