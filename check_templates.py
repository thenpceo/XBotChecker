import os

# Check templates directory
template_dir = 'templates'
print(f"Template directory: {template_dir}")
print(f"Template directory exists: {os.path.exists(template_dir)}")

if os.path.exists(template_dir):
    print("\nTemplates in directory:")
    for file in os.listdir(template_dir):
        file_path = os.path.join(template_dir, file)
        file_size = os.path.getsize(file_path)
        print(f"  - {file} ({file_size} bytes)")
        
        # Check if it's the force_refresh.html file
        if file == 'force_refresh.html':
            print(f"\nChecking force_refresh.html:")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"  File can be read successfully")
                    print(f"  File length: {len(content)} characters")
                    print(f"  First 100 characters: {content[:100]}")
            except Exception as e:
                print(f"  Error reading file: {str(e)}")

# Check Flask app configuration
try:
    from flask import Flask
    app = Flask(__name__)
    print(f"\nFlask app configuration:")
    print(f"  Default template folder: {app.template_folder}")
    print(f"  Template folder exists: {os.path.exists(app.template_folder)}")
    
    if os.path.exists(app.template_folder):
        print(f"  Templates in Flask template folder:")
        for file in os.listdir(app.template_folder):
            print(f"    - {file}")
except Exception as e:
    print(f"Error checking Flask configuration: {str(e)}")

print("\nDone checking templates.") 