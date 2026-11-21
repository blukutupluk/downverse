#!/usr/bin/env python3
# Music filename cleanup script
# Removes redundant descriptors from MP3 filenames

import os
import re

MUSIC_DIR = "/storage/7544-8C33/Music"
DRY_RUN = False

PATTERNS = [
    r'\(Official\s*(Lyric\s*)?Video\)',
    r'\(Official\s*Music\s*Video\)',
    r'\(Official\s*Audio\)',
    r'\(Official\s*Lyric\s*Visualizer\)',
    r'\(Lyrics?\)',
    r'\(HQ\s*Audio\)',
    r'\(HQ\s*Sound\)',
    r'\(Drumless\)',
    r'\(No\s*ADS?\)',
    r'\(Vertical\s*Video\)',
    r'\(stereo\)',
    r'\(No\s*Drum\)',
    r'\(Extended\s*Version\)',
    r'\(Live\)',
    r'\(Remastered\)',
    r'\(HQ\)',
    r'Official\s*(Lyric\s*)?Video',
    r'Official\s*Music\s*Video',
    r'Official\s*Audio',
    r'Official\s*Lyric\s*Visualizer',
    r'Lirik\s*Lagu',
    r'Lirik',
    r'Lyrics?',
    r'HQ\s*Audio',
    r'HQ\s*Sound',
    r'Suara\s*Jernih',
    r'Videomix',
    r'Extended\s*Party\s*Mix',
    r'Extended\s*Version',
    r'\(MP3_\d+K\)',
    r'\[\s*video\s*\]',
    r'Official\s*Remaster',
    r'\[\s*\w*video\w*\s*\]',
    r'\[가사비디오\s*_\s*Video\]',
    r'Official__Video',
    r'OFFICIAL__VIDEO',
    r'OFFICIAL_VIDEO',
    r'Official_Video',
    r'Video\s+by\s+\w+',
]

def clean_filename(name):
    base, ext = os.path.splitext(name)
    
    for pattern in PATTERNS:
        base = re.sub(pattern, '', base, flags=re.IGNORECASE)
    
    base = base.replace('_', ' ')
    base = re.sub(r'\s+', ' ', base)
    base = base.strip(' .-_')
    base = re.sub(r'\(\s*\)', '', base)
    base = re.sub(r'\s+\)', ')', base)
    base = re.sub(r'\(\s+', '(', base)
    base = base.strip()
    
    if not base:
        base = "untitled"
    
    return base + ext

def main():
    changes = []
    
    for root, dirs, files in os.walk(MUSIC_DIR):
        for filename in files:
            if not filename.lower().endswith('.mp3'):
                continue
            
            new_name = clean_filename(filename)
            if new_name == filename:
                continue
            
            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_name)
            
            if os.path.exists(new_path) and old_path != new_path:
                base, ext = os.path.splitext(new_name)
                counter = 1
                while os.path.exists(os.path.join(root, f"{base}_{counter}{ext}")):
                    counter += 1
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(root, new_name)
            
            changes.append((old_path, new_path, filename, new_name))
    
    print(f"Total changes: {len(changes)}")
    
    if DRY_RUN:
        for old, new, old_name, new_name in changes[:20]:
            print(f"  {old_name} -> {new_name}")
        if len(changes) > 20:
            print(f"  ... and {len(changes)-20} more")
        return
    
    applied = 0
    errors = 0
    for old_path, new_path, old_name, new_name in changes:
        try:
            os.rename(old_path, new_path)
            applied += 1
        except Exception as e:
            print(f"ERROR: {old_name} -> {new_name}: {e}")
            errors += 1
    
    print(f"Applied: {applied}, Errors: {errors}")

if __name__ == "__main__":
    main()
