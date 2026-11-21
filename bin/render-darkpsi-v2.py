#!/usr/bin/env python3
# Dark Psychology Content Video Generator v2
# Creates a 30s 9:16 vertical video with narrative text, characters, and visual elements

import os
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION
OUTPUT_DIR = "/data/data/com.termux/files/usr/tmp/opencode/darkpsi_frames2"
OUTPUT_VIDEO = "/storage/7544-8C33/output/DarkPsi_Ep1_v2.mp4"

FONT_BOLD = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/BricolageGrotesque-Bold.ttf"
FONT_REG = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf"
FONT_ITALIC = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Italic.ttf"

# Scene: (start, end, title, subtitle, body, accent_color, bg_color, char_pose)
SCENES = [
    (0, 3, "DIA BILANG", "\"AKU CUMA BERCANDA\"", "", (255, 68, 68), (13, 8, 8), "neutral"),
    (3, 5, "TAPI SEBENARNYA?", "", "", (255, 68, 68), (13, 8, 8), "suspicious"),
    (5, 8, "Robert Greene", "48 Laws of Power — Law 3", "Conceal Your Intentions", (255, 170, 0), (20, 15, 5), "neutral"),
    (8, 11, "TANDA #1", "Jawaban selalu ambigu", "Tidak pernah jelas, selalu \"nanti\" atau \"lihat dulu\"", (255, 68, 68), (15, 10, 15), "confused"),
    (11, 14, "TANDA #2", "Tidak pernah komitmen", "Selalu ada alasan untuk tidak menepati janji", (255, 68, 68), (15, 10, 15), "hesitant"),
    (14, 17, "TANDA #3", "Selalu ada 'alasan' baru", "Hari ini alasan A, besok alasan B", (255, 68, 68), (15, 10, 15), "deceptive"),
    (17, 20, "RED FLAG", "Jika dia tidak bisa jawab 'kenapa'", "dengan jawaban yang konsisten", (255, 68, 68), (20, 5, 5), "warning"),
    (20, 24, "CARA MELINDUNGI DIRI", "Tanya 'kenapa'", "sampai dapat jawaban jelas dan konsisten", (0, 255, 136), (5, 20, 10), "protected"),
    (24, 27, "PELAJARAN", "Jangan percaya niat yang disembunyikan", "Orang yang jujur tidak takut menjelaskan alasannya", (255, 170, 0), (20, 15, 5), "wise"),
    (27, 30, "SIMPAN | SHARE | FOLLOW", "Episode 2: Court Attention", "Follow untuk episode selanjutnya", (255, 170, 0), (10, 10, 10), "neutral"),
]

def draw_character(draw, t, pose, cx, cy):
    """Draw a more expressive character silhouette"""
    # Base colors
    body_color = (50, 50, 60)
    outline = (90, 90, 100)
    
    # Head
    head_y = cy - 180
    draw.ellipse([cx-50, head_y, cx+50, head_y+100], fill=body_color, outline=outline, width=2)
    
    # Eyes (change based on pose)
    eye_y = head_y + 35
    if pose == "confused":
        # One eyebrow raised
        draw.arc([cx-30, eye_y-5, cx-10, eye_y+15], 0, 180, fill=(200, 200, 200), width=2)
        draw.ellipse([cx+10, eye_y, cx+25, eye_y+15], fill=(200, 200, 200))
    elif pose == "suspicious":
        # Narrow eyes
        draw.line([(cx-30, eye_y+5), (cx-10, eye_y+5)], fill=(200, 200, 200), width=3)
        draw.line([(cx+10, eye_y+5), (cx+30, eye_y+5)], fill=(200, 200, 200), width=3)
    elif pose == "deceptive":
        # Smirking
        draw.ellipse([cx-30, eye_y, cx-15, eye_y+15], fill=(200, 200, 200))
        draw.ellipse([cx+15, eye_y, cx+30, eye_y+15], fill=(200, 200, 200))
        draw.arc([cx-20, eye_y+20, cx+20, eye_y+40], 0, 180, fill=(200, 200, 200), width=2)
    elif pose == "warning":
        # Wide eyes
        draw.ellipse([cx-30, eye_y-5, cx-10, eye_y+15], fill=(255, 100, 100))
        draw.ellipse([cx+10, eye_y-5, cx+30, eye_y+15], fill=(255, 100, 100))
    elif pose == "protected":
        # Determined
        draw.ellipse([cx-30, eye_y, cx-15, eye_y+15], fill=(100, 255, 150))
        draw.ellipse([cx+15, eye_y, cx+30, eye_y+15], fill=(100, 255, 150))
        draw.line([(cx-15, eye_y+25), (cx+15, eye_y+25)], fill=(100, 255, 150), width=2)
    elif pose == "wise":
        # Calm
        draw.ellipse([cx-30, eye_y, cx-15, eye_y+15], fill=(255, 200, 100))
        draw.ellipse([cx+15, eye_y, cx+30, eye_y+15], fill=(255, 200, 100))
        draw.arc([cx-15, eye_y+20, cx+15, eye_y+35], 0, 180, fill=(255, 200, 100), width=2)
    else:
        # Neutral
        draw.ellipse([cx-30, eye_y, cx-15, eye_y+15], fill=(200, 200, 200))
        draw.ellipse([cx+15, eye_y, cx+30, eye_y+15], fill=(200, 200, 200))
    
    # Body
    draw.rectangle([cx-45, head_y+100, cx+45, head_y+220], fill=body_color, outline=outline, width=2)
    
    # Arms (typing animation)
    arm_offset = int(8 * (t % 0.4) / 0.4) if t % 0.4 < 0.2 else int(8 - 8 * (t % 0.4 - 0.2) / 0.2)
    if pose in ("neutral", "suspicious", "deceptive"):
        draw.rectangle([cx-75, head_y+120, cx-45, head_y+160 + arm_offset], fill=body_color, outline=outline, width=2)
        draw.rectangle([cx+45, head_y+120, cx+75, head_y+160 - arm_offset], fill=body_color, outline=outline, width=2)
    elif pose == "confused":
        draw.rectangle([cx-75, head_y+120, cx-45, head_y+160], fill=body_color, outline=outline, width=2)
        draw.rectangle([cx+45, head_y+120, cx+75, head_y+160], fill=body_color, outline=outline, width=2)
        # Shrugging arms
        draw.line([(cx-45, head_y+120), (cx-90, head_y+80)], fill=outline, width=3)
        draw.line([(cx+45, head_y+120), (cx+90, head_y+80)], fill=outline, width=3)
    elif pose == "warning":
        # Arms raised
        draw.line([(cx-45, head_y+120), (cx-90, head_y+60)], fill=outline, width=3)
        draw.line([(cx+45, head_y+120), (cx+90, head_y+60)], fill=outline, width=3)
    elif pose == "protected":
        # Arms crossed
        draw.line([(cx-45, head_y+140), (cx+45, head_y+140)], fill=outline, width=4)
    elif pose == "wise":
        # Hand on chin
        draw.line([(cx+45, head_y+120), (cx+30, head_y+160)], fill=outline, width=3)
    
    # Laptop
    laptop_y = head_y + 220
    draw.rectangle([cx-100, laptop_y, cx+100, laptop_y+50], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    # Screen
    draw.rectangle([cx-90, laptop_y+5, cx+90, laptop_y+45], fill=(0, 30, 60), outline=(0, 80, 120), width=1)
    # Screen content (scrolling lines)
    for i in range(3):
        ly = laptop_y + 10 + i * 12
        draw.line([(cx-80, ly), (cx+80, ly)], fill=(0, 100, 150), width=1)
    
    # Table
    draw.rectangle([cx-120, laptop_y+50, cx+120, laptop_y+60], fill=(40, 30, 20), outline=(60, 50, 30), width=2)
    
    # Chair
    draw.rectangle([cx-30, head_y+220, cx+30, head_y+320], fill=(35, 35, 40), outline=(60, 60, 65), width=2)

def draw_background(draw, t, bg_color, accent):
    """Draw atmospheric background"""
    # Gradient
    for y in range(HEIGHT):
        r = int(bg_color[0] + (accent[0] - bg_color[0]) * 0.1 * (1 - y / HEIGHT))
        g = int(bg_color[1] + (accent[1] - bg_color[1]) * 0.1 * (1 - y / HEIGHT))
        b = int(bg_color[2] + (accent[2] - bg_color[2]) * 0.1 * (1 - y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Vignette
    for i in range(50):
        alpha = int(80 * (i / 50))
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0, alpha), width=1)
    
    # Floating particles
    import random
    random.seed(42)
    for _ in range(20):
        px = random.randint(0, WIDTH)
        py = random.randint(0, HEIGHT)
        # Animate particles
        py = (py + int(t * 30)) % HEIGHT
        size = random.randint(1, 3)
        brightness = random.randint(30, 80)
        draw.ellipse([px-size, py-size, px+size, py+size], fill=(brightness, brightness, brightness))

def draw_text_centered(draw, text, font, y, color, alpha=1.0):
    """Draw centered text with alpha"""
    if not text:
        return
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    color = tuple(int(c * alpha) for c in color)
    draw.text(((WIDTH - tw) // 2, y - th // 2), text, font=font, fill=color)

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
    if scene_progress < 0.15:
        alpha = scene_progress / 0.15
    elif scene_progress > 0.85:
        alpha = (1 - scene_progress) / 0.15
    else:
        alpha = 1.0
    
    img = Image.new('RGB', (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    draw_background(draw, t, bg_color, accent)
    
    cx = WIDTH // 2
    cy = int(HEIGHT * 0.65)
    draw_character(draw, t, pose, cx, cy)
    
    # Draw title
    if title:
        font = ImageFont.truetype(FONT_BOLD, 64)
        draw_text_centered(draw, title, font, int(HEIGHT * 0.12), accent, alpha)
    
    # Draw subtitle
    if subtitle:
        font = ImageFont.truetype(FONT_REG, 42)
        draw_text_centered(draw, subtitle, font, int(HEIGHT * 0.20), (220, 220, 220), alpha)
    
    # Draw body
    if body:
        font = ImageFont.truetype(FONT_REG, 36)
        draw_text_centered(draw, body, font, int(HEIGHT * 0.28), (180, 180, 180), alpha)
    
    # Scene indicator
    font_small = ImageFont.truetype(FONT_REG, 20)
    draw.text((50, HEIGHT - 60), f"Ep.1  |  {int(t)}s", font=font_small, fill=(50, 50, 50))
    
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
