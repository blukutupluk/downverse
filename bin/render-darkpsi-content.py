#!/usr/bin/env python3
# Dark Psychology Content Video Generator
# Creates a 30s 9:16 vertical video with narrative text and characters

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Configuration
WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION
OUTPUT_DIR = "/data/data/com.termux/files/usr/tmp/opencode/darkpsi_frames"
OUTPUT_VIDEO = "/storage/7544-8C33/output/DarkPsi_Ep1_Content.mp4"

# Font paths
FONT_BOLD = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/BricolageGrotesque-Bold.ttf"
FONT_REG = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf"

# Scene definitions: (start_sec, end_sec, title, subtitle, bg_color, accent_color)
SCENES = [
    (0, 3, "DIA BILANG", "\"AKU CUMA BERCANDA\"", (13, 13, 13), (255, 68, 68)),
    (3, 5, "TAPI SEBENARNYA?", "", (13, 13, 13), (255, 68, 68)),
    (5, 8, "Robert Greene", "48 Laws of Power — Law 3", (20, 10, 10), (255, 170, 0)),
    (8, 10, "CONCEAL", "YOUR INTENTIONS", (20, 10, 10), (255, 170, 0)),
    (10, 13, "TANDA #1", "Jawaban selalu ambigu", (15, 10, 20), (255, 68, 68)),
    (13, 16, "", "Tidak pernah jelas", (15, 10, 20), (200, 200, 200)),
    (16, 19, "", "Selalu 'nanti' atau 'lihat dulu'", (15, 10, 20), (200, 200, 200)),
    (19, 22, "TANDA #2", "Tidak pernah komitmen", (15, 10, 20), (255, 68, 68)),
    (22, 25, "", "Selalu ada alasan berubah-ubah", (15, 10, 20), (200, 200, 200)),
    (25, 28, "TANDA #3", "Selalu ada 'alasan' baru", (15, 10, 20), (255, 68, 68)),
    (28, 30, "TANYA 'KENAPA'", "sampai dapat jawaban jelas", (10, 20, 10), (0, 255, 136)),
    (30, 30, "SIMPAN | SHARE | FOLLOW", "", (10, 10, 10), (255, 170, 0)),
]

def draw_character(draw, t, style="typing"):
    """Draw a simple character silhouette"""
    cx, cy = WIDTH // 2, HEIGHT // 2 + 100
    # Head
    draw.ellipse([cx-60, cy-200, cx+60, cy-80], fill=(40, 40, 40), outline=(80, 80, 80), width=2)
    # Body
    draw.rectangle([cx-50, cy-80, cx+50, cy+50], fill=(40, 40, 40), outline=(80, 80, 80), width=2)
    # Arms (typing animation)
    arm_offset = int(5 * (t % 0.3) / 0.3) if t % 0.3 < 0.15 else int(5 - 5 * (t % 0.3 - 0.15) / 0.15)
    draw.rectangle([cx-80, cy-60, cx-50, cy-20 + arm_offset], fill=(40, 40, 40), outline=(80, 80, 80), width=2)
    draw.rectangle([cx+50, cy-60, cx+80, cy-20 - arm_offset], fill=(40, 40, 40), outline=(80, 80, 80), width=2)
    # Laptop
    draw.rectangle([cx-90, cy+50, cx+90, cy+90], fill=(30, 30, 30), outline=(100, 100, 100), width=2)
    # Screen glow
    draw.rectangle([cx-80, cy+55, cx+80, cy+85], fill=(0, 50, 80), outline=(0, 100, 150), width=1)

def get_scene(t):
    for scene in SCENES:
        if scene[0] <= t < scene[1]:
            return scene
    return SCENES[-1]

def create_frame(frame_num):
    t = frame_num / FPS
    scene = get_scene(t)
    start, end, title, subtitle, bg_color, accent = scene
    
    # Calculate progress within scene
    scene_duration = end - start
    scene_progress = (t - start) / scene_duration if scene_duration > 0 else 0
    
    # Create image
    img = Image.new('RGB', (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add subtle gradient overlay
    for y in range(HEIGHT):
        alpha = int(20 * (1 - y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(bg_color[0]+alpha, bg_color[1]+alpha, bg_color[2]+alpha))
    
    # Draw character
    draw_character(draw, t)
    
    # Draw title
    if title:
        font = ImageFont.truetype(FONT_BOLD, 72)
        bbox = draw.textbbox((0, 0), title, font=font)
        tw = bbox[2] - bbox[0]
        # Fade in
        alpha = min(1.0, scene_progress * 3)
        color = tuple(int(c * alpha) for c in accent)
        draw.text(((WIDTH - tw) // 2, int(HEIGHT * 0.25)), title, font=font, fill=color)
    
    # Draw subtitle
    if subtitle:
        font = ImageFont.truetype(FONT_REG, 44)
        bbox = draw.textbbox((0, 0), subtitle, font=font)
        tw = bbox[2] - bbox[0]
        alpha = min(1.0, max(0, scene_progress * 3 - 0.3))
        color = tuple(int(c * alpha) for c in (200, 200, 200))
        draw.text(((WIDTH - tw) // 2, int(HEIGHT * 0.35)), subtitle, font=font, fill=color)
    
    # Add scene indicator
    font_small = ImageFont.truetype(FONT_REG, 24)
    draw.text((50, HEIGHT - 80), f"Ep.1 | {int(t)}s/{DURATION}s", font=font_small, fill=(60, 60, 60))
    
    return img

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Generating {TOTAL_FRAMES} frames...")
    for i in range(TOTAL_FRAMES):
        img = create_frame(i)
        img.save(os.path.join(OUTPUT_DIR, f"frame_{i:04d}.png"))
        if i % 60 == 0:
            print(f"  Frame {i}/{TOTAL_FRAMES}")
    
    print("Frames generated. Combining with ffmpeg...")
    os.system(f'ffmpeg -y -framerate {FPS} -i {OUTPUT_DIR}/frame_%04d.png -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p -movflags +faststart -an {OUTPUT_VIDEO} 2>/dev/null')
    
    # Cleanup frames
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("frame_") and f.endswith(".png"):
            os.remove(os.path.join(OUTPUT_DIR, f))
    
    print(f"Done! Output: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
