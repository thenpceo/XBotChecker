import os

def find_templates(start_path):
    """Find all template directories and template files in the project"""
    print("=== Finding Template Directories and Files ===")
    print(f"Starting search from: {start_path}")
    
    template_dirs = []
    template_files = []
    
    for root, dirs, files in os.walk(start_path):
        # Find template directories
        if os.path.basename(root) == 'templates':
            template_dirs.append(root)
            
            # List all files in this template directory
            for file in files:
                if file.endswith('.html'):
                    full_path = os.path.join(root, file)
                    template_files.append(full_path)
    
    # Print results
    print(f"\nFound {len(template_dirs)} template directories:")
    for directory in template_dirs:
        print(f"- {directory}")
    
    print(f"\nFound {len(template_files)} template files:")
    for file in template_files:
        print(f"- {file}")
    
    # Check for new_x_template.html specifically
    target_files = [f for f in template_files if os.path.basename(f) == 'new_x_template.html']
    print(f"\nFound {len(target_files)} instances of new_x_template.html:")
    for file in target_files:
        print(f"- {file}")
        
        # Check if this file contains our changes
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '<title>X Bot Checker</title>' in content:
                print(f"  ✅ This file contains the updated title")
            else:
                print(f"  ❌ This file does NOT contain the updated title")

if __name__ == "__main__":
    # Start from the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    find_templates(current_dir) 