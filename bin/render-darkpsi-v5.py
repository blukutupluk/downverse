#!/usr/bin/env python3
# Dark Psychology Character & Environment Designer
# Creates a character sheet and environment preview

import os, math, random
from PIL import Image, ImageDraw, ImageFont
OUTPUT_DIR = "/data/data/com.termux/files/usr/tmp/opencode/darkpsi_frames5"
OUTPUT_VIDEO = "/storage/7544-8C33/output/DarkPsi_Ep1_v5.mp4"
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION

SCENES = [
    (0, 3, "DIA BILANG", chr(34)+"AKU CUMA BERCANDA"+chr(34), "", (255, 60, 60), "suspicious", "idle"),
    (3, 5, "TAPI SEBENARNYA?", "", "", (255, 60, 60), "suspicious", "think"),
    (5, 8, "Robert Greene", "48 Laws of Power - Law 3", "Conceal Your Intentions", (255, 180, 0), "neutral", "explain"),
    (8, 11, "TANDA 1", "Jawaban selalu ambigu", "Tidak pernah jelas, selalu nanti atau lihat dulu", (255, 60, 60), "confused", "shrug"),
    (11, 14, "", "Selalu ada alasan", "Kamu tanya kenapa dia tidak datang. Dia jawab: aku sibuk.", (255, 60, 60), "confused", "think"),
    (14, 17, "TANDA 2", "Tidak pernah komitmen", "Selalu ada alasan untuk tidak menepati janji", (255, 60, 60), "suspicious", "crossed"),
    (17, 20, "TANDA 3", "Selalu ada alasan baru", "Hari ini alasan A, besok alasan B", (255, 60, 60), "deceptive", "explain"),
    (20, 23, "RED FLAG", "Jika dia tidak bisa jawab kenapa", "dengan jawaban yang konsisten", (255, 60, 60), "warning", "emphasize"),
    (23, 26, "CARA MELINDUNGI DIRI", "Tanya kenapa", "sampai dapat jawaban jelas dan konsisten", (0, 255, 136), "protected", "point"),
    (26, 28, "PELAJARAN", "Jangan percaya niat yang disembunyikan", "Orang yang jujur tidak takut menjelaskan", (255, 180, 0), "wise", "nod"),
    (28, 30, "SIMPAN | SHARE | FOLLOW", "Episode 2: Court Attention", "Follow untuk episode selanjutnya", (255, 180, 0), "happy", "wave"),
]

WIDTH, HEIGHT = 1080, 1920
FONT_BOLD = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/BricolageGrotesque-Bold.ttf"
FONT_REG = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf"

# === COLOR PALETTE (DARK MIND brand) ===
C = {
    "bg": (12, 12, 18),
    "wall": (22, 22, 32),
    "floor": (30, 25, 20),
    "desk": (50, 40, 30),
    "desk_top": (65, 52, 38),
    "window": (15, 25, 45),
    "window_frame": (70, 60, 50),
    "lamp": (180, 160, 100),
    "lamp_glow": (255, 220, 150),
    "plant": (40, 90, 50),
    "plant_leaf": (50, 130, 60),
    "shelf": (55, 45, 35),
    "skin": (215, 175, 145),
    "skin_shadow": (175, 135, 105),
    "hair": (35, 25, 15),
    "shirt": (35, 45, 65),
    "shirt_highlight": (50, 60, 85),
    "pants": (25, 25, 35),
    "shoes": (20, 20, 25),
    "eyes": (30, 30, 30),
    "eyes_highlight": (255, 255, 255),
    "mouth": (170, 70, 70),
    "outline": (10, 10, 15),
    "accent_violet": (120, 80, 180),
    "accent_amber": (255, 180, 0),
    "accent_red": (255, 60, 60),
    "accent_green": (0, 255, 136),
    "accent_white": (235, 235, 235),
    "accent_gray": (130, 130, 130),
    "card_bg": (40, 35, 50),
    "card_border": (80, 70, 100),
}

def draw_room(draw, t):
    """Draw room environment with desk, window, lamp, plant, shelf"""
    # Wall
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=C["wall"])
    
    # Floor
    floor_y = int(HEIGHT * 0.78)
    draw.rectangle([0, floor_y, WIDTH, HEIGHT], fill=C["floor"])
    draw.rectangle([0, floor_y-3, WIDTH, floor_y], fill=(40, 35, 25))
    
    # Window (left)
    win_x, win_y = 60, 180
    win_w, win_h = 280, 380
    draw.rectangle([win_x, win_y, win_x+win_w, win_y+win_h], fill=C["window"], outline=C["window_frame"], width=4)
    draw.line([(win_x+win_w//2, win_y), (win_x+win_w//2, win_y+win_h)], fill=C["window_frame"], width=3)
    draw.line([(win_x, win_y+win_h//2), (win_x+win_w, win_y+win_h//2)], fill=C["window_frame"], width=3)
    draw.rectangle([win_x-10, win_y+win_h, win_x+win_w+10, win_y+win_h+8], fill=C["window_frame"])
    
    # Moonlight
    for i in range(5):
        alpha = 12 - i * 2
        draw.rectangle([win_x+5, win_y+5+i*12, win_x+win_w-5, win_y+win_h-5], 
                      fill=(20+alpha, 30+alpha, 50+alpha))
    
    # Clouds
    cloud_x = (int(t * 15) % (win_w + 80)) - 40
    draw.ellipse([win_x+cloud_x, win_y+40, win_x+cloud_x+50, win_y+65], fill=(35, 45, 65))
    draw.ellipse([win_x+cloud_x+25, win_y+25, win_x+cloud_x+75, win_y+55], fill=(35, 45, 65))
    
    # Desk
    desk_x, desk_y = WIDTH//2 - 160, int(HEIGHT * 0.68)
    draw.rectangle([desk_x, desk_y, desk_x+320, desk_y+20], fill=C["desk_top"], outline=C["desk"], width=2)
    draw.rectangle([desk_x+15, desk_y+20, desk_x+30, desk_y+100], fill=C["desk"], outline=(30, 25, 15), width=1)
    draw.rectangle([desk_x+290, desk_y+20, desk_x+305, desk_y+100], fill=C["desk"], outline=(30, 25, 15), width=1)
    
    # Laptop
    lap_x, lap_y = desk_x + 90, desk_y - 5
    draw.rectangle([lap_x, lap_y-45, lap_x+140, lap_y], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([lap_x+5, lap_y-40, lap_x+135, lap_y-5], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        ly = lap_y - 32 + i * 9
        draw.line([(lap_x+10, ly), (lap_x+130, ly)], fill=(0, 120, 180), width=1)
    draw.rectangle([lap_x-5, lap_y, lap_x+145, lap_y+8], fill=(30, 30, 40), outline=(60, 60, 70), width=1)
    
    # Chair
    chair_x = WIDTH//2 - 35
    chair_y = desk_y + 15
    draw.rectangle([chair_x, chair_y, chair_x+70, chair_y+90], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([chair_x+5, chair_y-70, chair_x+65, chair_y], fill=(40, 40, 45), outline=(60, 60, 65), width=2)
    
    # Plant
    plant_x, plant_y = WIDTH - 130, int(HEIGHT * 0.62)
    draw.rectangle([plant_x-6, plant_y, plant_x+6, plant_y+50], fill=(60, 40, 20), outline=(40, 30, 15), width=1)
    import math
    sway = math.sin(t * 1.5) * 6
    for i in range(6):
        angle = (i * 60 + sway) % 360
        rad = math.radians(angle)
        lx = plant_x + int(22 * math.cos(rad))
        ly = plant_y - 15 - int(18 * math.sin(rad))
        draw.ellipse([lx-14, ly-10, lx+14, ly+10], fill=C["plant_leaf"], outline=C["plant"], width=1)
    
    # Lamp
    lamp_x, lamp_y = 180, int(HEIGHT * 0.32)
    draw.rectangle([lamp_x-3, lamp_y, lamp_x+3, lamp_y+120], fill=(80, 70, 50), outline=(60, 50, 30), width=1)
    draw.polygon([(lamp_x-28, lamp_y-25), (lamp_x+28, lamp_y-25), (lamp_x+18, lamp_y), (lamp_x-18, lamp_y)], 
                 fill=C["lamp"], outline=(150, 130, 80), width=1)
    for i in range(6):
        r = 35 + i * 12
        draw.ellipse([lamp_x-r, lamp_y-25-r, lamp_x+r, lamp_y-25+r], fill=(255, 220, 150))
    
    # Shelf
    shelf_y = int(HEIGHT * 0.28)
    draw.rectangle([WIDTH-220, shelf_y, WIDTH-40, shelf_y+8], fill=(50, 40, 30), outline=(30, 25, 15), width=1)
    for i in range(5):
        bx = WIDTH - 210 + i * 32
        bh = 20 + (i % 3) * 8
        draw.rectangle([bx, shelf_y-bh, bx+22, shelf_y], fill=(60+i*15, 40+i*8, 30+i*5), outline=(30, 25, 15), width=1)
    
    # Vignette
    for i in range(40):
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0), width=1)

def draw_character(draw, t, expression, gesture, cx, cy):
    """Draw detailed character with expressions and gestures"""
    # Breathing
    breath = 0.015 * math.sin(t * 2.5)
    sway = 0.01 * math.sin(t * 1.8)
    blink = 1.0 if (t % 3.2) > 0.12 else 0.1
    
    cx += int(sway * 60)
    cy += int(breath * 30)
    
    head_r = 52
    head_y = cy - 185
    
    # Head (with slight 3D effect)
    draw.ellipse([cx-head_r, head_y-head_r, cx+head_r, head_y+head_r], 
                 fill=C["skin"], outline=C["outline"], width=2)
    # Shadow on left side
    draw.ellipse([cx-head_r, head_y-head_r, cx-head_r+15, head_y+head_r], 
                 fill=C["skin_shadow"])
    
    # Hair (top)
    draw.ellipse([cx-head_r-5, head_y-head_r-10, cx+head_r+5, head_y-25], 
                 fill=C["hair"], outline=C["outline"], width=1)
    draw.rectangle([cx-head_r-5, head_y-head_r-10, cx+head_r+5, head_y-30], fill=C["hair"])
    
    # Eyes
    eye_y = head_y - 3
    eye_l = cx - 18
    eye_r = cx + 18
    
    if expression == "confused":
        draw.arc([eye_l-10, eye_y-6, eye_l+10, eye_y+6], 0, 180, fill=C["eyes"], width=2)
        draw.ellipse([eye_r-7, eye_y-5, eye_r+7, eye_y+7], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-3, eye_y-1, eye_r+3, eye_y+5], fill=C["eyes"])
        # Question mark
        font_q = ImageFont.truetype(FONT_BOLD, 30)
        draw.text((cx+35, eye_y-25), "?", font=font_q, fill=C["accent_yellow"])
    elif expression == "suspicious":
        draw.line([(eye_l-8, eye_y), (eye_l+8, eye_y)], fill=C["eyes"], width=3)
        draw.line([(eye_r-8, eye_y), (eye_r+8, eye_y)], fill=C["eyes"], width=3)
        draw.arc([cx-30, eye_y-12, cx, eye_y+3], 180, 360, fill=C["eyes"], width=2)
    elif expression == "deceptive":
        draw.ellipse([eye_l-7, eye_y-5, eye_l+7, eye_y+7], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-3, eye_y-1, eye_l+3, eye_y+5], fill=C["eyes"])
        draw.ellipse([eye_r-7, eye_y-5, eye_r+7, eye_y+7], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-3, eye_y-1, eye_r+3, eye_y+5], fill=C["eyes"])
        draw.arc([cx-8, eye_y+15, cx+12, eye_y+30], 0, 180, fill=C["mouth"], width=2)
    elif expression == "warning":
        draw.ellipse([eye_l-10, eye_y-8, eye_l+10, eye_y+8], fill=(255, 100, 100))
        draw.ellipse([eye_r-10, eye_y-8, eye_r+10, eye_y+8], fill=(255, 100, 100))
        draw.ellipse([eye_l-3, eye_y-2, eye_l+3, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-3, eye_y-2, eye_r+3, eye_y+4], fill=C["eyes"])
        # Exclamation mark
        font_ex = ImageFont.truetype(FONT_BOLD, 36)
        draw.text((cx-8, head_y-head_r-35), "!", font=font_ex, fill=C["accent_red"])
    elif expression == "protected":
        draw.ellipse([eye_l-7, eye_y-5, eye_l+7, eye_y+7], fill=(100, 255, 150))
        draw.ellipse([eye_r-7, eye_y-5, eye_r+7, eye_y+7], fill=(100, 255, 150))
        draw.ellipse([eye_l-3, eye_y-1, eye_l+3, eye_y+5], fill=C["eyes"])
        draw.ellipse([eye_r-3, eye_y-1, eye_r+3, eye_y+5], fill=C["eyes"])
        draw.line([(cx-12, eye_y+20), (cx+12, eye_y+20)], fill=(100, 255, 150), width=2)
    elif expression == "wise":
        draw.ellipse([eye_l-7, eye_y-5, eye_l+7, eye_y+7], fill=(255, 200, 100))
        draw.ellipse([eye_r-7, eye_y-5, eye_r+7, eye_y+7], fill=(255, 200, 100))
        draw.ellipse([eye_l-3, eye_y-1, eye_l+3, eye_y+5], fill=C["eyes"])
        draw.ellipse([eye_r-3, eye_y-1, eye_r+3, eye_y+5], fill=C["eyes"])
        draw.arc([cx-12, eye_y+18, cx+12, eye_y+30], 0, 180, fill=(255, 200, 100), width=2)
    elif expression == "happy":
        draw.ellipse([eye_l-7, eye_y-4, eye_l+7, eye_y+6], fill=(255, 200, 100))
        draw.ellipse([eye_r-7, eye_y-4, eye_r+7, eye_y+6], fill=(255, 200, 100))
        draw.ellipse([eye_l-3, eye_y, eye_l+3, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-3, eye_y, eye_r+3, eye_y+4], fill=C["eyes"])
        draw.arc([cx-15, eye_y+15, cx+15, eye_y+30], 0, 180, fill=C["mouth"], width=2)
    else:
        # neutral
        draw.ellipse([eye_l-7, eye_y-5, eye_l+7, eye_y+7], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-7, eye_y-5, eye_r+7, eye_y+7], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-3, eye_y-1, eye_l+3, eye_y+5], fill=C["eyes"])
        draw.ellipse([eye_r-3, eye_y-1, eye_r+3, eye_y+5], fill=C["eyes"])
    
    # Eyebrows
    brow_y = eye_y - 14
    if expression == "confused":
        draw.line([(eye_l-8, brow_y-3), (eye_l+8, brow_y+3)], fill=C["hair"], width=2)
        draw.line([(eye_r-8, brow_y+3), (eye_r+8, brow_y-3)], fill=C["hair"], width=2)
    elif expression in ("warning", "surprised"):
        draw.line([(eye_l-8, brow_y-5), (eye_l+8, brow_y-5)], fill=C["hair"], width=2)
        draw.line([(eye_r-8, brow_y-5), (eye_r+8, brow_y-5)], fill=C["hair"], width=2)
    elif expression == "suspicious":
        draw.line([(eye_l-8, brow_y+2), (eye_l+8, brow_y-2)], fill=C["hair"], width=2)
        draw.line([(eye_r-8, brow_y-2), (eye_r+8, brow_y+2)], fill=C["hair"], width=2)
    elif expression == "deceptive":
        draw.line([(eye_l-8, brow_y), (eye_l+8, brow_y-2)], fill=C["hair"], width=2)
        draw.line([(eye_r-8, brow_y-2), (eye_r+8, brow_y)], fill=C["hair"], width=2)
    else:
        draw.line([(eye_l-8, brow_y), (eye_l+8, brow_y)], fill=C["hair"], width=2)
        draw.line([(eye_r-8, brow_y), (eye_r+8, brow_y)], fill=C["hair"], width=2)
    
    # Mouth
    mouth_y = eye_y + 30
    if expression in ("neutral", "suspicious", "confused"):
        draw.line([(cx-12, mouth_y), (cx+12, mouth_y)], fill=C["mouth"], width=2)
    elif expression in ("deceptive",):
        draw.arc([cx-8, mouth_y-3, cx+12, mouth_y+8], 0, 180, fill=C["mouth"], width=2)
    elif expression in ("warning", "surprised"):
        draw.ellipse([cx-8, mouth_y-4, cx+8, mouth_y+4], fill=C["mouth"])
    elif expression in ("protected",):
        draw.line([(cx-12, mouth_y), (cx+12, mouth_y)], fill=(100, 255, 150), width=2)
    elif expression in ("wise", "happy"):
        draw.arc([cx-15, mouth_y-5, cx+15, mouth_y+8], 0, 180, fill=C["mouth"], width=2)
    elif expression == "sad":
        draw.arc([cx-12, mouth_y, cx+12, mouth_y+12], 180, 360, fill=C["mouth"], width=2)
    
    # Body
    body_top = head_y + 55
    draw.rectangle([cx-50, body_top, cx+50, body_top+145], fill=C["shirt"], outline=C["outline"], width=2)
    draw.rectangle([cx-48, body_top+2, cx, body_top+143], fill=C["shirt_highlight"])
    
    # Arms (gesture-based)
    gesture = gesture if gesture in GESTURES else "idle"
    g = GESTURES[gesture]
    arm_y = body_top + 20
    t_mod = t % 1.0
    
    al_x = cx - 50 + int(g["arm_l"][0] * 55)
    al_y = arm_y + int(g["arm_l"][1] * 55)
    if gesture == "idle":
        al_y += int(4 * math.sin(t * 2))
    draw.line([(cx-50, arm_y), (al_x, al_y)], fill=C["shirt_highlight"], width=5)
    draw.ellipse([al_x-8, al_y-8, al_x+8, al_y+8], fill=C["skin"], outline=C["outline"], width=1)
    
    ar_x = cx + 50 + int(g["arm_r"][0] * 55)
    ar_y = arm_y + int(g["arm_r"][1] * 55)
    if gesture == "idle":
        ar_y += int(4 * math.sin(t * 2 + 1))
    draw.line([(cx+50, arm_y), (ar_x, ar_y)], fill=C["shirt_highlight"], width=5)
    draw.ellipse([ar_x-8, ar_y-8, ar_x+8, ar_y+8], fill=C["skin"], outline=C["outline"], width=1)
    
    # Laptop
    laptop_y = body_top + 145
    draw.rectangle([cx-100, laptop_y, cx+100, laptop_y+45], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([cx-90, laptop_y+5, cx+90, laptop_y+40], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        ly = laptop_y + 12 + i * 9
        draw.line([(cx-80, ly), (cx+80, ly)], fill=(0, 120, 180), width=1)
    draw.rectangle([cx-105, laptop_y+45, cx+105, laptop_y+55], fill=C["desk_top"], outline=C["desk"], width=2)
    
    # Chair
    draw.rectangle([cx-38, body_top+145, cx+38, body_top+250], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([cx-33, body_top+85, cx+33, body_top+145], fill=(40, 40, 45), outline=(60, 60, 65), width=2)
    
    # Pointing indicator
    if gesture == "point":
        draw.line([(ar_x, ar_y), (ar_x+50, ar_y-80)], fill=C["accent_yellow"], width=2)
        draw.polygon([(ar_x+50, ar_y-80), (ar_x+45, ar_y-68), (ar_x+55, ar_y-68)], fill=C["accent_yellow"])
    
    # Warning indicator
    if expression == "warning":
        font_ex = ImageFont.truetype(FONT_BOLD, 40)
        draw.text((cx-10, head_y-head_r-40), "!", font=font_ex, fill=C["accent_red"])

def draw_background(draw, t, bg_color, accent):
    # Wall
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=C["wall"])
    
    # Floor
    floor_y = int(HEIGHT * 0.78)
    draw.rectangle([0, floor_y, WIDTH, HEIGHT], fill=C["floor"])
    draw.rectangle([0, floor_y-3, WIDTH, floor_y], fill=(40, 35, 25))
    
    # Window
    win_x, win_y = 60, 180
    win_w, win_h = 280, 380
    draw.rectangle([win_x, win_y, win_x+win_w, win_y+win_h], fill=C["window"], outline=C["window_frame"], width=4)
    draw.line([(win_x+win_w//2, win_y), (win_x+win_w//2, win_y+win_h)], fill=C["window_frame"], width=3)
    draw.line([(win_x, win_y+win_h//2), (win_x+win_w, win_y+win_h//2)], fill=C["window_frame"], width=3)
    draw.rectangle([win_x-10, win_y+win_h, win_x+win_w+10, win_y+win_h+8], fill=C["window_frame"])
    
    # Moonlight
    for i in range(5):
        alpha = 12 - i * 2
        draw.rectangle([win_x+5, win_y+5+i*12, win_x+win_w-5, win_y+win_h-5], 
                      fill=(20+alpha, 30+alpha, 50+alpha))
    
    # Clouds
    cloud_x = (int(t * 15) % (win_w + 80)) - 40
    draw.ellipse([win_x+cloud_x, win_y+40, win_x+cloud_x+50, win_y+65], fill=(35, 45, 65))
    draw.ellipse([win_x+cloud_x+25, win_y+25, win_x+cloud_x+75, win_y+55], fill=(35, 45, 65))
    
    # Desk
    desk_x, desk_y = WIDTH//2 - 160, int(HEIGHT * 0.68)
    draw.rectangle([desk_x, desk_y, desk_x+320, desk_y+20], fill=C["desk_top"], outline=C["desk"], width=2)
    draw.rectangle([desk_x+15, desk_y+20, desk_x+30, desk_y+100], fill=C["desk"], outline=(30, 25, 15), width=1)
    draw.rectangle([desk_x+290, desk_y+20, desk_x+305, desk_y+100], fill=C["desk"], outline=(30, 25, 15), width=1)
    
    # Laptop
    lap_x, lap_y = desk_x + 90, desk_y - 5
    draw.rectangle([lap_x, lap_y-45, lap_x+140, lap_y], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([lap_x+5, lap_y-40, lap_x+135, lap_y-5], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        ly = lap_y - 32 + i * 9
        draw.line([(lap_x+10, ly), (lap_x+130, ly)], fill=(0, 120, 180), width=1)
    draw.rectangle([lap_x-5, lap_y, lap_x+145, lap_y+8], fill=(30, 30, 40), outline=(60, 60, 70), width=1)
    
    # Chair
    chair_x = WIDTH//2 - 35
    chair_y = desk_y + 15
    draw.rectangle([chair_x, chair_y, chair_x+70, chair_y+90], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([chair_x+5, chair_y-70, chair_x+65, chair_y], fill=(40, 40, 45), outline=(60, 60, 65), width=2)
    
    # Plant
    plant_x, plant_y = WIDTH - 130, int(HEIGHT * 0.62)
    draw.rectangle([plant_x-6, plant_y, plant_x+6, plant_y+50], fill=(60, 40, 20), outline=(40, 30, 15), width=1)
    import math
    sway = math.sin(t * 1.5) * 6
    for i in range(6):
        angle = (i * 60 + sway) % 360
        rad = math.radians(angle)
        lx = plant_x + int(22 * math.cos(rad))
        ly = plant_y - 15 - int(18 * math.sin(rad))
        draw.ellipse([lx-14, ly-10, lx+14, ly+10], fill=C["plant_leaf"], outline=C["plant"], width=1)
    
    # Lamp
    lamp_x, lamp_y = 180, int(HEIGHT * 0.32)
    draw.rectangle([lamp_x-3, lamp_y, lamp_x+3, lamp_y+120], fill=(80, 70, 50), outline=(60, 50, 30), width=1)
    draw.polygon([(lamp_x-28, lamp_y-25), (lamp_x+28, lamp_y-25), (lamp_x+18, lamp_y), (lamp_x-18, lamp_y)], 
                 fill=C["lamp"], outline=(150, 130, 80), width=1)
    for i in range(6):
        r = 35 + i * 12
        draw.ellipse([lamp_x-r, lamp_y-25-r, lamp_x+r, lamp_y-25+r], fill=(255, 220, 150))
    
    # Shelf
    shelf_y = int(HEIGHT * 0.28)
    draw.rectangle([WIDTH-220, shelf_y, WIDTH-40, shelf_y+8], fill=(50, 40, 30), outline=(30, 25, 15), width=1)
    for i in range(5):
        bx = WIDTH - 210 + i * 32
        bh = 20 + (i % 3) * 8
        draw.rectangle([bx, shelf_y-bh, bx+22, shelf_y], fill=(60+i*15, 40+i*8, 30+i*5), outline=(30, 25, 15), width=1)
    
    # Vignette
    for i in range(40):
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0), width=1)

def draw_text(draw, text, font, y, color, alpha=1.0, max_width=None):
    if not text:
        return
    if max_width is None:
        max_width = WIDTH - 120
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
        draw.text(((WIDTH - tw) // 2, y + i * (th + 8)), line, font=font, fill=color)

def get_scene(t):
    for scene in SCENES:
        if scene[0] <= t < scene[1]:
            return scene
    return SCENES[-1]

def create_frame(frame_num):
    t = frame_num / FPS
    scene = get_scene(t)
    start, end, title, subtitle, body, accent, expression, gesture = scene
    
    scene_duration = end - start
    scene_progress = (t - start) / scene_duration if scene_duration > 0 else 0
    
    if scene_progress < 0.15:
        alpha = scene_progress / 0.15
    elif scene_progress > 0.85:
        alpha = (1 - scene_progress) / 0.15
    else:
        alpha = 1.0
    
    img = Image.new('RGB', (WIDTH, HEIGHT), (13, 13, 20))
    draw = ImageDraw.Draw(img)
    
    draw_background(draw, t, (13, 13, 20), accent)
    
    cx = WIDTH // 2
    cy = int(HEIGHT * 0.62)
    draw_character(draw, t, expression, gesture, cx, cy)
    
    if title:
        font = ImageFont.truetype(FONT_BOLD, 64)
        draw_text(draw, title, font, int(HEIGHT * 0.08), accent, alpha)
    
    if subtitle:
        font = ImageFont.truetype(FONT_REG, 40)
        draw_text(draw, subtitle, font, int(HEIGHT * 0.15), (220, 220, 220), alpha)
    
    if body:
        font = ImageFont.truetype(FONT_REG, 32)
        draw_text(draw, body, font, int(HEIGHT * 0.22), (180, 180, 180), alpha)
    
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
    
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("frame_") and f.endswith(".png"):
            os.remove(os.path.join(OUTPUT_DIR, f))
    
    print(f"Done! Output: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
