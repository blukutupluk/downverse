#!/usr/bin/env python3
# Number MP3 files in each folder
# Format: 001 - originalname.mp3

import os

MUSIC_DIR = "/storage/7544-8C33/Music"
DRY_RUN = False

def main():
    total_renamed = 0
    total_errors = 0
    
    for root, dirs, files in os.walk(MUSIC_DIR):
        # Get all MP3 files in this directory (not subdirs)
        mp3_files = sorted([f for f in files if f.lower().endswith('.mp3')])
        
        if not mp3_files:
            continue
        
        # Check if files already have numbering
        already_numbered = all(re.match(r'^\d{3}\s*-', f) for f in mp3_files if False)
        
        for i, filename in enumerate(mp3_files, 1):
            # Skip if already numbered
            if re.match(r'^\d{3}\s*-', filename):
                continue
            
            num = f"{i:03d}"
            new_name = f"{num} - {filename}"
            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_name)
            
            # Avoid overwriting
            if os.path.exists(new_path):
                print(f"SKIP (exists): {new_name}")
                continue
            
            if DRY_RUN:
                print(f"  {filename} -> {new_name}")
                total_renamed += 1
                continue
            
            try:
                os.rename(old_path, new_path)
                total_renamed += 1
            except Exception as e:
                print(f"ERROR: {filename} -> {new_name}: {e}")
                total_errors += 1
    
    print(f"\nTotal renamed: {total_renamed}, Errors: {total_errors}")

if __name__ == "__main__":
    import re
    main()
