
import os
import re

directory = r"e:\final project\FarmerMarketplace\app\templates"
old_name = "AgriMarket"
new_name = "FARMER 2 BUYER"

for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith(".html"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_name in content:
                new_content = content.replace(old_name, new_name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated: {file_path}")

print("Rename complete")
