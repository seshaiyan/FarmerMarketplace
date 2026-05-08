
import os
import re

files = [
    r"e:\final project\FarmerMarketplace\app\templates\admin\dashboard.html",
    r"e:\final project\FarmerMarketplace\app\templates\admin\users.html"
]

new_settings = '<a href="{{ url_for(\'admin.settings\') }}" class="icon-btn" style="text-decoration: none;"><i class="fas fa-cog"></i></a>'

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace Cog button (Settings)
        content = re.sub(r'<button class="icon-btn">\s*<i class="fas fa-cog"></i>\s*</button>', new_settings, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")

print("Update complete")
