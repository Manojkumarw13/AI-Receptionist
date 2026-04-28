from rembg import remove
from PIL import Image
import shutil
import os

input_path = 'static/images/logo.png'
backup_path = 'static/images/logo_backup.png'
output_path = 'static/images/logo.png'

print("Starting background removal process...")

# Backup
if os.path.exists(input_path):
    # Only backup if backup doesn't exist to avoid overwriting original backup with already processed image if run multiple times
    if not os.path.exists(backup_path):
        shutil.copy(input_path, backup_path)
        print(f"Backed up {input_path} to {backup_path}")
    else:
        print(f"Backup already exists at {backup_path}, skipping backup.")
else:
    print(f"Error: {input_path} not found!")
    exit(1)

# Process
try:
    print("Reading image...")
    input_image = Image.open(input_path)
    
    print("Removing background...")
    output_image = remove(input_image)
    
    print("Saving image...")
    output_image.save(output_path)
    print(f"Background removed and saved to {output_path}")
except Exception as e:
    print(f"Error during processing: {e}")
    exit(1)
