
import os

file_path = r"e:\final project\FarmerMarketplace\app\templates\admin\users.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for Edit button
edit_old = '<button class="icon-btn" style="color: var(--text-light);" title="Edit">\n                                        <i class="fas fa-edit"></i>\n                                    </button>'
# Wait, the indentation might be different. Let's look at the file content logically.

# Aggressive replacement for the action buttons
target_start = '<i class="fas fa-eye"></i>\n                                    </button>'
target_end = '</td>'

# Actually, let's just replace the specific buttons by looking for the title="Edit" attribute
new_edit = '<a href="{{ url_for(\'admin.edit_user\', user_id=user.id) }}" class="icon-btn" style="color: var(--text-light); text-decoration: none;" title="Edit"><i class="fas fa-edit"></i></a>'
new_delete = '<form action="{{ url_for(\'admin.delete_user\', user_id=user.id) }}" method="POST" style="display:inline;" onsubmit="return confirm(\'Are you sure you want to delete this user?\');"><button type="submit" class="icon-btn" style="color: var(--danger-color); border:none; background:none; cursor:pointer;" title="Delete"><i class="fas fa-trash"></i></button></form>'

# Simplified matching
import re

# Replace Edit button
content = re.sub(r'<button class="icon-btn" style="color: var\(--text-light\);" title="Edit">\s*<i class="fas fa-edit"></i>\s*</button>', new_edit, content)

# Replace Delete button
content = re.sub(r'<button class="icon-btn" style="color: var\(--danger-color\);" title="Delete">\s*<i class="fas fa-trash"></i>\s*</button>', new_delete, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update complete")
