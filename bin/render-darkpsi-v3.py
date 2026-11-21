#!/usr/bin/env python3
# Character Design Module for Dark Psychology Content
# Simple but expressive characters using PIL

import os
from PIL import Image, ImageDraw, ImageFont
OUTPUT_DIR = "/data/data/com.termux/files/usr/tmp/opencode/darkpsi_frames3"
OUTPUT_VIDEO = "/storage/7544-8C33/output/DarkPsi_Ep1_v3.mp4"
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION

# Character color palette
COLORS = {
    "skin": (220, 180, 150),
    "skin_shadow": (180, 140, 110),
    "hair": (40, 30, 20),
    "shirt": (30, 30, 50),
    "shirt_highlight": (50, 50, 70),
    "pants": (25, 25, 35),
    "shoes": (20, 20, 25),
    "eyes": (30, 30, 30),
    "eyes_highlight": (255, 255, 255),
    "mouth": (180, 80, 80),
    "outline": (15, 15, 20),
    "bg_dark": (13, 13, 13),
    "accent_red": (255, 68, 68),
    "accent_green": (0, 255, 136),
    "accent_yellow": (255, 170, 0),
    "accent_white": (220, 220, 220),
}

def draw_character(draw, cx, cy, pose="neutral", scale=1.0):
    """Draw an expressive character silhouette"""
    s = scale
    # Head
    head_r = int(55 * s)
    draw.ellipse([cx-head_r, cy-200*s, cx+head_r, cy-90*s], fill=COLORS["skin"], outline=COLORS["outline"], width=2)
    
    # Hair
    draw.ellipse([cx-head_r-5, cy-210*s, cx+head_r+5, cy-140*s], fill=COLORS["hair"], outline=COLORS["outline"], width=1)
    draw.rectangle([cx-head_r-5, cy-210*s, cx+head_r+5, cy-170*s], fill=COLORS["hair"])
    
    # Eyes
    eye_y = cy - 150*s
    eye_l = cx - 20*s
    eye_r = cx + 20*s
    
    if pose == "confused":
        # One eyebrow raised, one normal
        draw.arc([eye_l-12, eye_y-8, eye_l+12, eye_y+8], 0, 180, fill=COLORS["eyes"], width=2)
        draw.ellipse([eye_r-8, eye_y-5, eye_r+8, eye_y+10], fill=COLORS["eyes"])
        # Question mark
        draw.text((cx+40, eye_y-20), "?", fill=COLORS["accent_yellow"])
    elif pose == "suspicious":
        # Narrow eyes
        draw.line([(eye_l-10, eye_y), (eye_l+10, eye_y)], fill=COLORS["eyes"], width=3)
        draw.line([(eye_r-10, eye_y), (eye_r+10, eye_y)], fill=COLORS["eyes"], width=3)
        # Raised eyebrow
        draw.arc([cx-35, eye_y-15, cx-5, eye_y+5], 180, 360, fill=COLORS["eyes"], width=2)
    elif pose == "deceptive":
        # Smirking
        draw.ellipse([eye_l-8, eye_y-5, eye_l+8, eye_y+10], fill=COLORS["eyes"])
        draw.ellipse([eye_r-8, eye_y-5, eye_r+8, eye_y+10], fill=COLORS["eyes"])
        # Smirk
        draw.arc([cx-15, eye_y+15, cx+25, eye_y+35], 0, 180, fill=COLORS["mouth"], width=2)
    elif pose == "warning":
        # Wide eyes
        draw.ellipse([eye_l-12, eye_y-8, eye_l+12, eye_y+12], fill=(255, 100, 100))
        draw.ellipse([eye_r-12, eye_y-8, eye_r+12, eye_y+12], fill=(255, 100, 100))
        draw.ellipse([eye_l-4, eye_y-2, eye_l+4, eye_y+6], fill=COLORS["eyes"])
        draw.ellipse([eye_r-4, eye_y-2, eye_r+4, eye_y+6], fill=COLORS["eyes"])
    elif pose == "protected":
        # Determined eyes
        draw.ellipse([eye_l-8, eye_y-5, eye_l+8, eye_y+10], fill=(100, 255, 150))
        draw.ellipse([eye_r-8, eye_y-5, eye_r+8, eye_y+10], fill=(100, 255, 150))
        draw.line([(cx-15, eye_y+20), (cx+15, eye_y+20)], fill=(100, 255, 150), width=2)
    elif pose == "wise":
        # Calm, knowing eyes
        draw.ellipse([eye_l-8, eye_y-5, eye_l+8, eye_y+10], fill=(255, 200, 100))
        draw.ellipse([eye_r-8, eye_y-5, eye_r+8, eye_y+10], fill=(255, 200, 100))
        draw.arc([cx-15, eye_y+18, cx+15, eye_y+32], 0, 180, fill=(255, 200, 100), width=2)
    else:
        # Neutral
        draw.ellipse([eye_l-8, eye_y-5, eye_l+8, eye_y+10], fill=COLORS["eyes_highlight"])
        draw.ellipse([eye_r-8, eye_y-5, eye_r+8, eye_y+10], fill=COLORS["eyes_highlight"])
        draw.ellipse([eye_l-4, eye_y-1, eye_l+4, eye_y+7], fill=COLORS["eyes"])
        draw.ellipse([eye_r-4, eye_y-1, eye_r+4, eye_y+7], fill=COLORS["eyes"])
    
    # Mouth
    mouth_y = eye_y + 25
    if pose == "confused":
        draw.line([(cx-10, mouth_y), (cx+10, mouth_y)], fill=COLORS["mouth"], width=2)
    elif pose == "deceptive":
        pass  # smirk already drawn
    elif pose == "warning":
        draw.ellipse([cx-8, mouth_y-4, cx+8, mouth_y+4], fill=COLORS["mouth"])
    elif pose == "protected":
        draw.line([(cx-12, mouth_y), (cx+12, mouth_y)], fill=COLORS["mouth"], width=2)
    else:
        draw.arc([cx-12, mouth_y-5, cx+12, mouth_y+5], 0, 180, fill=COLORS["mouth"], width=2)
    
    # Body (shirt)
    body_top = cy - 90*s + 100  # below head
    draw.rectangle([cx-50*s, body_top, cx+50*s, body_top+140*s], fill=COLORS["shirt"], outline=COLORS["outline"], width=2)
    
    # Arms
    arm_y = body_top + 20*s
    if pose == "confused":
        # Arms up (shrugging)
        draw.line([(cx-50*s, arm_y), (cx-90*s, arm_y-40*s)], fill=COLORS["shirt_highlight"], width=4)
        draw.line([(cx+50*s, arm_y), (cx+90*s, arm_y-40*s)], fill=COLORS["shirt_highlight"], width=4)
    elif pose == "warning":
        # Arms up (defensive)
        draw.line([(cx-50*s, arm_y), (cx-80*s, arm_y-60*s)], fill=COLORS["shirt_highlight"], width=4)
        draw.line([(cx+50*s, arm_y), (cx+80*s, arm_y-60*s)], fill=COLORS["shirt_highlight"], width=4)
    elif pose == "protected":
        # Arms crossed
        draw.line([(cx-50*s, arm_y+20*s), (cx+50*s, arm_y+20*s)], fill=COLORS["shirt_highlight"], width=4)
    else:
        # Typing arms
        arm_offset = int(10 * (t % 0.5) / 0.5) if t % 0.5 < 0.25 else int(10 - 10 * (t % 0.5 - 0.25) / 0.25)
        draw.rectangle([cx-80*s, arm_y, cx-50*s, arm_y+40*s+arm_offset], fill=COLORS["shirt_highlight"], outline=COLORS["outline"], width=1)
        draw.rectangle([cx+50*s, arm_y, cx+80*s, arm_y+40*s-arm_offset], fill=COLORS["shirt_highlight"], outline=COLORS["outline"], width=1)
    
    # Laptop
    laptop_y = body_top + 140*s
    draw.rectangle([cx-100*s, laptop_y, cx+100*s, laptop_y+40*s], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    # Screen
    draw.rectangle([cx-90*s, laptop_y+5*s, cx+90*s, laptop_y+35*s], fill=(0, 20, 40), outline=(0, 80, 120), width=1)
    # Screen content
    for i in range(2):
        ly = laptop_y + 12*s + i * 10*s
        draw.line([(cx-80*s, ly), (cx+80*s, ly)], fill=(0, 100, 150), width=1)
    
    # Table
    draw.rectangle([cx-130*s, laptop_y+40*s, cx+130*s, laptop_y+50*s], fill=(40, 30, 20), outline=(60, 50, 30), width=2)
    
    # Chair
    draw.rectangle([cx-35*s, body_top+140*s, cx+35*s, body_top+260*s], fill=(35, 35, 40), outline=(60, 60, 65), width=2)

def draw_background(draw, t, bg_color, accent):
    """Draw atmospheric background with particles"""
    import random
    random.seed(42)
    
    # Gradient
    for y in range(HEIGHT):
        r = int(bg_color[0] + (accent[0] - bg_color[0]) * 0.15 * (1 - y / HEIGHT))
        g = int(bg_color[1] + (accent[1] - bg_color[1]) * 0.15 * (1 - y / HEIGHT))
        b = int(bg_color[2] + (accent[2] - bg_color[2]) * 0.15 * (1 - y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Vignette
    for i in range(80):
        alpha = int(120 * (i / 80))
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0), width=1)
    
    # Floating particles
    for _ in range(30):
        px = random.randint(0, WIDTH)
        py = random.randint(0, HEIGHT)
        py = (py + int(t * 20)) % HEIGHT
        size = random.randint(1, 2)
        brightness = random.randint(20, 60)
        draw.ellipse([px-size, py-size, px+size, py+size], fill=(brightness, brightness, brightness))
    
    # Accent glow at top
    for i in range(50):
        alpha = int(30 * (1 - i / 50))
        draw.line([(0, i), (WIDTH, i)], fill=(accent[0]//4, accent[1]//4, accent[2]//4))

def draw_text(draw, text, font, y, color, alpha=1.0, max_width=None):
    """Draw centered text with alpha"""
    if not text:
        return
    if max_width is None:
        max_width = WIDTH - 100
    # Word wrap
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + " " + word if current else word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        color = tuple(int(c * alpha) for c in color)
        draw.text(((WIDTH - tw) // 2, y + i * (th + 10) - th // 2), line, font=font, fill=color)

def get_scene(t):
    for scene in SCENES:
        if scene[0] <= t < scene[1]:
            return scene
    return SCENES[-1]

def create_frame(frame_num):
    t = frame_num / FPS
    scene = get_scene(t)
    start, end, title, subtitle, body, accent, bg_color, pose = scene
    
    scene_duration = end - start
    scene_progress = (t - start) / scene_duration if scene_duration > 0 else 0
    
    # Fade in/out
    if scene_progress < 0.12:
        alpha = scene_progress / 0.12
    elif scene_progress > 0.88:
        alpha = (1 - scene_progress) / 0.12
    else:
        alpha = 1.0
    
    img = Image.new('RGB', (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    draw_background(draw, t, bg_color, accent)
    
    cx = WIDTH // 2
    cy = int(HEIGHT * 0.62)
    draw_character(draw, t, pose, cx, cy)
    
    # Draw title
    if title:
        font = ImageFont.truetype(FONT_BOLD, 68)
        draw_text(draw, title, font, int(HEIGHT * 0.10), accent, alpha)
    
    # Draw subtitle
    if subtitle:
        font = ImageFont.truetype(FONT_REG, 40)
        draw_text(draw, subtitle, font, int(HEIGHT * 0.18), (220, 220, 220), alpha)
    
    # Draw body
    if body:
        font = ImageFont.truetype(FONT_REG, 34)
        draw_text(draw, body, font, int(HEIGHT * 0.26), (180, 180, 180), alpha)
    
    # Scene indicator
    font_small = ImageFont.truetype(FONT_REG, 18)
    draw.text((50, HEIGHT - 50), f"Ep.1 | {int(t)}s/{DURATION}s", font=font_small, fill=(40, 40, 40))
    
    return img

def main():
    import shutil
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
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
