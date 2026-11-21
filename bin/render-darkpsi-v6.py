#!/usr/bin/env python3
# Character Sheet Generator — Dark Psychology (DARK MIND brand)
# Creates a character sheet showing all poses and expressions

import os, math
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG = (18, 16, 24)
FONT_BOLD = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/BricolageGrotesque-Bold.ttf"
FONT_REG = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf"
OUT = "/storage/7544-8C33/output/CharacterSheet_DarkMind.png"
WIDTH, HEIGHT = 1080, 1920
OUTPUT_DIR = "/data/data/com.termux/files/usr/tmp/opencode/darkpsi_frames6"
OUTPUT_VIDEO = "/storage/7544-8C33/output/DarkPsi_Ep1_v6.mp4"
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION

# DARK MIND palette
C = {
    "bg": (18, 16, 24),
    "wall": (28, 26, 36),
    "skin": (215, 175, 145),
    "skin_shadow": (175, 135, 105),
    "hair": (35, 25, 15),
    "shirt": (45, 40, 60),
    "shirt_highlight": (65, 55, 85),
    "pants": (30, 28, 40),
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
}

def draw_character(draw, cx, cy, expression="neutral", gesture="idle", scale=0.7):
    """Draw detailed character with expression and gesture"""
    s = scale
    head_r = int(48 * s)
    head_y = cy - int(170 * s)
    
    # Head (with shadow for depth)
    draw.ellipse([cx-head_r, head_y-head_r, cx+head_r, head_y+head_r], 
                 fill=C["skin"], outline=C["outline"], width=2)
    # Shadow on left
    draw.ellipse([cx-head_r, head_y-head_r, cx-head_r+12, head_y+head_r], 
                 fill=C["skin_shadow"])
    
    # Hair
    draw.ellipse([cx-head_r-4, head_y-head_r-8, cx+head_r+4, head_y-22*s], 
                 fill=C["hair"], outline=C["outline"], width=1)
    draw.rectangle([cx-head_r-4, head_y-head_r-8, cx+head_r+4, head_y-28*s], fill=C["hair"])
    
    # Eyes
    eye_y = head_y - 3
    eye_l = cx - int(16*s)
    eye_r = cx + int(16*s)
    
    if expression == "confused":
        draw.arc([eye_l-9, eye_y-5, eye_l+9, eye_y+5], 0, 180, fill=C["eyes"], width=2)
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-3, eye_y, eye_r+3, eye_y+4], fill=C["eyes"])
        # Question mark
        font_q = ImageFont.truetype(FONT_BOLD, int(24*s))
        draw.text((cx+30, eye_y-20), "?", font=font_q, fill=C["accent_yellow"])
    elif expression == "suspicious":
        draw.line([(eye_l-7, eye_y), (eye_l+7, eye_y)], fill=C["eyes"], width=2)
        draw.line([(eye_r-7, eye_y), (eye_r+7, eye_y)], fill=C["eyes"], width=2)
        draw.arc([cx-28, eye_y-10, cx-4, eye_y+2], 180, 360, fill=C["eyes"], width=2)
    elif expression == "deceptive":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=C["eyes"])
        draw.arc([cx-6, eye_y+12, cx+10, eye_y+22], 0, 180, fill=C["mouth"], width=2)
    elif expression == "warning":
        draw.ellipse([eye_l-8, eye_y-7, eye_l+8, eye_y+7], fill=(255, 100, 100))
        draw.ellipse([eye_r-8, eye_y-7, eye_r+8, eye_y+7], fill=(255, 100, 100))
        draw.ellipse([eye_l-2, eye_y-2, eye_l+2, eye_y+2], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y-2, eye_r+2, eye_y+2], fill=C["eyes"])
        font_ex = ImageFont.truetype(FONT_BOLD, int(30*s))
        draw.text((cx-6, head_y-head_r-30), "!", font=font_ex, fill=C["accent_red"])
    elif expression == "protected":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=(100, 255, 150))
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(100, 255, 150))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=C["eyes"])
        draw.line([(cx-10, eye_y+18), (cx+10, eye_y+18)], fill=(100, 255, 150), width=2)
    elif expression == "wise":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=(255, 200, 100))
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(255, 200, 100))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=C["eyes"])
        draw.arc([cx-10, eye_y+15, cx+10, eye_y+25], 0, 180, fill=(255, 200, 100), width=2)
    elif expression == "happy":
        draw.ellipse([eye_l-6, eye_y-3, eye_l+6, eye_y+5], fill=(255, 200, 100))
        draw.ellipse([eye_r-6, eye_y-3, eye_r+6, eye_y+5], fill=(255, 200, 100))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+3], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+3], fill=C["eyes"])
        draw.arc([cx-12, eye_y+12, cx+12, eye_y+25], 0, 180, fill=C["mouth"], width=2)
    elif expression == "sad":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=C["eyes"])
        draw.arc([cx-10, eye_y+20, cx+10, eye_y+30], 180, 360, fill=C["mouth"], width=2)
    elif expression == "surprised":
        draw.ellipse([eye_l-9, eye_y-8, eye_l+9, eye_y+8], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-9, eye_y-8, eye_r+9, eye_y+8], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-3, eye_y-2, eye_l+3, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-3, eye_y-2, eye_r+3, eye_y+4], fill=C["eyes"])
        draw.ellipse([cx-6, eye_y+18, cx+6, eye_y+30], fill=C["mouth"])
    elif expression == "thinking":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=C["eyes"])
        draw.arc([cx-10, eye_y+18, cx+10, eye_y+28], 0, 180, fill=C["mouth"], width=1)
    else:
        # neutral
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=C["eyes"])
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=C["eyes"])
        draw.line([(cx-10, eye_y+28), (cx+10, eye_y+28)], fill=C["mouth"], width=2)
    
    # Eyebrows
    brow_y = eye_y - 14
    if expression == "confused":
        draw.line([(eye_l-7, brow_y-3), (eye_l+7, brow_y+3)], fill=C["hair"], width=2)
        draw.line([(eye_r-7, brow_y+3), (eye_r+7, brow_y-3)], fill=C["hair"], width=2)
    elif expression in ("warning", "surprised"):
        draw.line([(eye_l-7, brow_y-5), (eye_l+7, brow_y-5)], fill=C["hair"], width=2)
        draw.line([(eye_r-7, brow_y-5), (eye_r+7, brow_y-5)], fill=C["hair"], width=2)
    elif expression == "suspicious":
        draw.line([(eye_l-7, brow_y+2), (eye_l+7, brow_y-2)], fill=C["hair"], width=2)
        draw.line([(eye_r-7, brow_y-2), (eye_r+7, brow_y+2)], fill=C["hair"], width=2)
    elif expression == "deceptive":
        draw.line([(eye_l-7, brow_y), (eye_l+7, brow_y-2)], fill=C["hair"], width=2)
        draw.line([(eye_r-7, brow_y-2), (eye_r+7, brow_y)], fill=C["hair"], width=2)
    elif expression in ("sad",):
        draw.line([(eye_l-7, brow_y+3), (eye_l+7, brow_y+3)], fill=C["hair"], width=2)
        draw.line([(eye_r-7, brow_y+3), (eye_r+7, brow_y+3)], fill=C["hair"], width=2)
    else:
        draw.line([(eye_l-7, brow_y), (eye_l+7, brow_y)], fill=C["hair"], width=2)
        draw.line([(eye_r-7, brow_y), (eye_r+7, brow_y)], fill=C["hair"], width=2)
    
    # Body
    body_top = head_y + 55
    draw.rectangle([cx-48, body_top, cx+48, body_top+140], fill=C["shirt"], outline=C["outline"], width=2)
    draw.rectangle([cx-46, body_top+2, cx, body_top+138], fill=C["shirt_highlight"])
    
    # Arms (gesture-based)
    gesture = gesture if gesture in GESTURES else "idle"
    g = GESTURES[gesture]
    arm_y = body_top + 20
    
    al_x = cx - 48 + int(g["arm_l"][0] * 50)
    al_y = arm_y + int(g["arm_l"][1] * 50)
    draw.line([(cx-48, arm_y), (al_x, al_y)], fill=C["shirt_highlight"], width=5)
    draw.ellipse([al_x-7, al_y-7, al_x+7, al_y+7], fill=C["skin"], outline=C["outline"], width=1)
    
    ar_x = cx + 48 + int(g["arm_r"][0] * 50)
    ar_y = arm_y + int(g["arm_r"][1] * 50)
    draw.line([(cx+48, arm_y), (ar_x, ar_y)], fill=C["shirt_highlight"], width=5)
    draw.ellipse([ar_x-7, ar_y-7, ar_x+7, ar_y+7], fill=C["skin"], outline=C["outline"], width=1)
    
    # Pointing indicator
    if gesture == "point":
        draw.line([(ar_x, ar_y), (ar_x+50, ar_y-80)], fill=C["accent_yellow"], width=2)
        draw.polygon([(ar_x+50, ar_y-80), (ar_x+45, ar_y-68), (ar_x+55, ar_y-68)], fill=C["accent_yellow"])
    
    # Laptop
    laptop_y = body_top + 140
    draw.rectangle([cx-95, laptop_y, cx+95, laptop_y+45], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([cx-85, laptop_y+5, cx+85, laptop_y+40], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        ly = laptop_y + 12 + i * 9
        draw.line([(cx-75, ly), (cx+75, ly)], fill=(0, 120, 180), width=1)
    draw.rectangle([cx-100, laptop_y+45, cx+100, laptop_y+55], fill=(60, 48, 38), outline=(40, 35, 25), width=2)
    
    # Chair
    draw.rectangle([cx-38, body_top+140, cx+38, body_top+240], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([cx-33, body_top+85, cx+33, body_top+145], fill=(40, 40, 45), outline=(60, 60, 65), width=2)

# === GESTURES ===
GESTURES = {
    "idle": {"arm_l": (0, 0), "arm_r": (0, 0)},
    "point": {"arm_l": (0, 0), "arm_r": (1, -0.8)},
    "explain": {"arm_l": (0.6, -0.3), "arm_r": (0.6, -0.3)},
    "think": {"arm_l": (0, 0), "arm_r": (0.3, -0.9)},
    "emphasize": {"arm_l": (0.8, -0.6), "arm_r": (0.8, -0.6)},
    "shrug": {"arm_l": (-0.5, -0.3), "arm_r": (0.5, -0.3)},
    "wave": {"arm_l": (0, 0), "arm_r": (1, -1.2)},
    "nod": {"arm_l": (0, 0), "arm_r": (0, 0)},
    "crossed": {"arm_l": (0.3, 0), "arm_r": (-0.3, 0)},
    "hands_up": {"arm_l": (-0.8, -1.2), "arm_r": (0.8, -1.2)},
}

# === SCENES (from storyboard) ===
SCENES = [
    (0, 4, "PERNAH NGGAK...", "Seseorang minta bantuan kecil", "", (255, 180, 0), "neutral", "idle"),
    (4, 7, "BISA BANTU SEBENTAR?", "", "", (255, 180, 0), "neutral", "nod"),
    (7, 11, "KITA MENGIAKAN", "Rasanya sepele, tidak ada alasan untuk menolak", "", (200, 200, 200), "neutral", "explain"),
    (11, 15, "LALU DATANG PERMINTAAN BERIKUTNYA", "Sedikit lebih besar. Setelah itu, satu lagi.", "", (255, 100, 100), "suspicious", "point"),
    (15, 19, "FOOT-IN-THE-DOOR", "Teknik pengaruh sosial", "Seseorang memulai dengan permintaan kecil, lalu mengajukan permintaan yang lebih besar", (255, 60, 60), "wise", "explain"),
    (19, 23, "KENAPA SULIT MENOLAK?", "Karena setelah berkata iya, kita ingin tetap konsisten", "Kita juga bisa mulai melihat diri sendiri sebagai orang yang bersedia membantu", (255, 180, 0), "thinking", "think"),
    (23, 26, "TIDAK SEMUA MANIPULASI", "Konteks, niat, dan kebebasan untuk menolak tetap penting", "", (0, 255, 136), "neutral", "palm_out" if False else "explain"),
    (26, 29, "BATAS TERUS BERGESER", "Kamu merasa bersalah setiap kali ingin berkata tidak", "", (255, 60, 60), "warning", "step_back"),
    (29, 32, "KAMU BOLEH BERUBAH PIKIRAN", "Persetujuan kecil kemarin bukan kontrak untuk semua permintaan besok", "", (0, 255, 136), "protected", "hands_up"),
    (32, 35, "BANTUAN TULUS MENGHARGAI BATAS", "Manipulasi justru mengujinya", "Jeda. Tatap kamera.", (255, 180, 0), "wise", "nod"),
    (35, 38, "SIMPAN | SHARE | FOLLOW", "Episode 2: Gaslighting", "Follow untuk episode selanjutnya", (255, 180, 0), "happy", "wave"),
]

def draw_background(draw, t, accent):
    # Wall
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(22, 22, 32))
    
    # Floor
    floor_y = int(HEIGHT * 0.78)
    draw.rectangle([0, floor_y, WIDTH, HEIGHT], fill=(30, 25, 20))
    draw.rectangle([0, floor_y-3, WIDTH, floor_y], fill=(40, 35, 25))
    
    # Window
    wx, wy, ww, wh = 60, 180, 280, 380
    draw.rectangle([wx, wy, wx+ww, wy+wh], fill=(15, 25, 45), outline=(70, 60, 50), width=4)
    draw.line([(wx+ww//2, wy), (wx+ww//2, wy+wh)], fill=(70, 60, 50), width=3)
    draw.line([(wx, wy+wh//2), (wx+ww, wy+wh//2)], fill=(70, 60, 50), width=3)
    draw.rectangle([wx-10, wy+wh, wx+ww+10, wy+wh+8], fill=(70, 60, 50))
    for i in range(5):
        a = 12 - i*2
        draw.rectangle([wx+5, wy+5+i*12, wx+ww-5, wy+wh-5], fill=(20+a, 30+a, 50+a))
    # Clouds
    cloud_x = (int(t * 15) % (ww + 80)) - 40
    draw.ellipse([wx+cloud_x, wy+40, wx+cloud_x+50, wy+65], fill=(35, 45, 65))
    draw.ellipse([wx+cloud_x+25, wy+25, wx+cloud_x+75, wy+55], fill=(35, 45, 65))
    
    # Desk
    dx, dy = WIDTH//2 - 160, int(HEIGHT * 0.68)
    draw.rectangle([dx, dy, dx+320, dy+20], fill=(65, 52, 38), outline=(45, 35, 25), width=2)
    draw.rectangle([dx+15, dy+20, dx+30, dy+100], fill=(45, 35, 25), outline=(30, 25, 15), width=1)
    draw.rectangle([dx+290, dy+20, dx+305, dy+100], fill=(45, 35, 25), outline=(30, 25, 15), width=1)
    
    # Laptop
    lx, ly = dx + 90, dy - 5
    draw.rectangle([lx, ly-45, lx+140, ly], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([lx+5, ly-40, lx+135, ly-5], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        lly = ly - 32 + i * 9
        draw.line([(lx+10, lly), (lx+130, lly)], fill=(0, 120, 180), width=1)
    draw.rectangle([lx-5, ly, lx+145, ly+8], fill=(30, 30, 40), outline=(60, 60, 70), width=1)
    
    # Chair
    cx, cy = WIDTH//2 - 35, dy + 15
    draw.rectangle([cx, cy, cx+70, cy+90], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([cx+5, cy-70, cx+65, cy], fill=(40, 40, 45), outline=(60, 60, 65), width=2)
    
    # Plant
    px, py = WIDTH - 130, int(HEIGHT * 0.62)
    draw.rectangle([px-6, py, px+6, py+50], fill=(60, 40, 20), outline=(40, 30, 15), width=1)
    sway = math.sin(t * 1.5) * 6
    for i in range(6):
        angle = (i * 60 + sway) % 360
        rad = math.radians(angle)
        lx_p = px + int(22 * math.cos(rad))
        ly_p = py - 15 - int(18 * math.sin(rad))
        draw.ellipse([lx_p-14, ly_p-10, lx_p+14, ly_p+10], fill=(40, 120, 50), outline=(30, 80, 40), width=1)
    
    # Lamp
    lamp_x, lamp_y = 180, int(HEIGHT * 0.32)
    draw.rectangle([lamp_x-3, lamp_y, lamp_x+3, lamp_y+120], fill=(80, 70, 50), outline=(60, 50, 30), width=1)
    draw.polygon([(lamp_x-28, lamp_y-25), (lamp_x+28, lamp_y-25), (lamp_x+18, lamp_y), (lamp_x-18, lamp_y)], fill=(200, 180, 120), outline=(150, 130, 80), width=1)
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
    """Draw expressive character"""
    import math
    breath = 0.015 * math.sin(t * 2.5)
    sway = 0.01 * math.sin(t * 1.8)
    blink = 1.0 if (t % 3.2) > 0.12 else 0.1
    
    cx += int(sway * 60)
    cy += int(breath * 30)
    
    head_r = 52
    head_y = cy - 185
    
    # Head
    draw.ellipse([cx-head_r, head_y-head_r, cx+head_r, head_y+head_r], 
                 fill=(220, 180, 150), outline=(10, 10, 15), width=2)
    draw.ellipse([cx-head_r, head_y-head_r, cx-head_r+12, head_y+head_r], 
                 fill=(180, 140, 110))
    
    # Hair
    draw.ellipse([cx-head_r-4, head_y-head_r-8, cx+head_r+4, head_y-22], 
                 fill=(35, 25, 15), outline=(10, 10, 15), width=1)
    draw.rectangle([cx-head_r-4, head_y-head_r-8, cx+head_r+4, head_y-30], fill=(35, 25, 15))
    
    # Eyes
    eye_y = head_y - 3
    eye_l = cx - 18
    eye_r = cx + 18
    
    if expression == "confused":
        draw.arc([eye_l-9, eye_y-5, eye_l+9, eye_y+5], 0, 180, fill=(30, 30, 30), width=2)
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(255, 255, 255))
        draw.ellipse([eye_r-3, eye_y, eye_r+3, eye_y+4], fill=(30, 30, 30))
    elif expression == "suspicious":
        draw.line([(eye_l-7, eye_y), (eye_l+7, eye_y)], fill=(30, 30, 30), width=3)
        draw.line([(eye_r-7, eye_y), (eye_r+7, eye_y)], fill=(30, 30, 30), width=3)
        draw.arc([cx-28, eye_y-10, cx-4, eye_y+2], 180, 360, fill=(30, 30, 30), width=2)
    elif expression == "deceptive":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=(255, 255, 255))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=(30, 30, 30))
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(255, 255, 255))
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=(30, 30, 30))
        draw.arc([cx-8, eye_y+15, cx+12, eye_y+25], 0, 180, fill=(180, 80, 80), width=2)
    elif expression == "warning":
        draw.ellipse([eye_l-8, eye_y-7, eye_l+8, eye_y+7], fill=(255, 100, 100))
        draw.ellipse([eye_r-8, eye_y-7, eye_r+8, eye_y+7], fill=(255, 100, 100))
        draw.ellipse([eye_l-2, eye_y-2, eye_l+2, eye_y+2], fill=(30, 30, 30))
        draw.ellipse([eye_r-2, eye_y-2, eye_r+2, eye_y+2], fill=(30, 30, 30))
    elif expression == "protected":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=(100, 255, 150))
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(100, 255, 150))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=(30, 30, 30))
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=(30, 30, 30))
        draw.line([(cx-10, eye_y+18), (cx+10, eye_y+18)], fill=(100, 255, 150), width=2)
    elif expression == "wise":
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=(255, 200, 100))
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(255, 200, 100))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=(30, 30, 30))
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=(30, 30, 30))
        draw.arc([cx-10, eye_y+15, cx+10, eye_y+25], 0, 180, fill=(255, 200, 100), width=2)
    elif expression == "happy":
        draw.ellipse([eye_l-6, eye_y-3, eye_l+6, eye_y+5], fill=(255, 200, 100))
        draw.ellipse([eye_r-6, eye_y-3, eye_r+6, eye_y+5], fill=(255, 200, 100))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+3], fill=(30, 30, 30))
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+3], fill=(30, 30, 30))
        draw.arc([cx-12, eye_y+12, cx+12, eye_y+25], 0, 180, fill=(180, 80, 80), width=2)
    else:
        draw.ellipse([eye_l-6, eye_y-4, eye_l+6, eye_y+6], fill=(255, 255, 255))
        draw.ellipse([eye_r-6, eye_y-4, eye_r+6, eye_y+6], fill=(255, 255, 255))
        draw.ellipse([eye_l-2, eye_y, eye_l+2, eye_y+4], fill=(30, 30, 30))
        draw.ellipse([eye_r-2, eye_y, eye_r+2, eye_y+4], fill=(30, 30, 30))
        draw.line([(cx-10, eye_y+28), (cx+10, eye_y+28)], fill=(180, 80, 80), width=2)
    
    # Eyebrows
    brow_y = eye_y - 14
    if expression == "confused":
        draw.line([(eye_l-7, brow_y-3), (eye_l+7, brow_y+3)], fill=(35, 25, 15), width=2)
        draw.line([(eye_r-7, brow_y+3), (eye_r+7, brow_y-3)], fill=(35, 25, 15), width=2)
    elif expression in ("warning", "surprised"):
        draw.line([(eye_l-7, brow_y-5), (eye_l+7, brow_y-5)], fill=(35, 25, 15), width=2)
        draw.line([(eye_r-7, brow_y-5), (eye_r+7, brow_y-5)], fill=(35, 25, 15), width=2)
    elif expression == "suspicious":
        draw.line([(eye_l-7, brow_y+2), (eye_l+7, brow_y-2)], fill=(35, 25, 15), width=2)
        draw.line([(eye_r-7, brow_y-2), (eye_r+7, brow_y+2)], fill=(35, 25, 15), width=2)
    elif expression == "deceptive":
        draw.line([(eye_l-7, brow_y), (eye_l+7, brow_y-2)], fill=(35, 25, 15), width=2)
        draw.line([(eye_r-7, brow_y-2), (eye_r+7, brow_y)], fill=(35, 25, 15), width=2)
    elif expression == "sad":
        draw.line([(eye_l-7, brow_y+3), (eye_l+7, brow_y+3)], fill=(35, 25, 15), width=2)
        draw.line([(eye_r-7, brow_y+3), (eye_r+7, brow_y+3)], fill=(35, 25, 15), width=2)
    else:
        draw.line([(eye_l-7, brow_y), (eye_l+7, brow_y)], fill=(35, 25, 15), width=2)
        draw.line([(eye_r-7, brow_y), (eye_r+7, brow_y)], fill=(35, 25, 15), width=2)
    
    # Mouth
    mouth_y = eye_y + 30
    if expression in ("neutral", "suspicious", "confused"):
        draw.line([(cx-12, mouth_y), (cx+12, mouth_y)], fill=(180, 80, 80), width=2)
    elif expression == "deceptive":
        draw.arc([cx-8, mouth_y-3, cx+12, mouth_y+8], 0, 180, fill=(180, 80, 80), width=2)
    elif expression in ("warning", "surprised"):
        draw.ellipse([cx-8, mouth_y-4, cx+8, mouth_y+4], fill=(180, 80, 80))
    elif expression == "protected":
        draw.line([(cx-12, mouth_y), (cx+12, mouth_y)], fill=(100, 255, 150), width=2)
    elif expression in ("wise", "happy"):
        draw.arc([cx-15, mouth_y-5, cx+15, mouth_y+8], 0, 180, fill=(180, 80, 80), width=2)
    elif expression == "sad":
        draw.arc([cx-12, mouth_y, cx+12, mouth_y+12], 180, 360, fill=(180, 80, 80), width=2)
    
    # Body
    body_top = head_y + 55
    draw.rectangle([cx-50, body_top, cx+50, body_top+145], fill=(35, 45, 65), outline=(10, 10, 15), width=2)
    draw.rectangle([cx-48, body_top+2, cx, body_top+143], fill=(50, 60, 85))
    
    # Arms
    gesture = gesture if gesture in GESTURES else "idle"
    g = GESTURES[gesture]
    arm_y = body_top + 20
    
    al_x = cx - 50 + int(g["arm_l"][0] * 55)
    al_y = arm_y + int(g["arm_l"][1] * 55)
    draw.line([(cx-50, arm_y), (al_x, al_y)], fill=(50, 60, 85), width=5)
    draw.ellipse([al_x-7, al_y-7, al_x+7, al_y+7], fill=(220, 180, 150), outline=(10, 10, 15), width=1)
    
    ar_x = cx + 50 + int(g["arm_r"][0] * 55)
    ar_y = arm_y + int(g["arm_r"][1] * 55)
    draw.line([(cx+50, arm_y), (ar_x, ar_y)], fill=(50, 60, 85), width=5)
    draw.ellipse([ar_x-7, ar_y-7, ar_x+7, ar_y+7], fill=(220, 180, 150), outline=(10, 10, 15), width=1)
    
    # Pointing indicator
    if gesture == "point":
        draw.line([(ar_x, ar_y), (ar_x+50, ar_y-80)], fill=(255, 180, 0), width=2)
        draw.polygon([(ar_x+50, ar_y-80), (ar_x+45, ar_y-68), (ar_x+55, ar_y-68)], fill=(255, 180, 0))
    
    # Warning indicator
    if expression == "warning":
        font_ex = ImageFont.truetype(FONT_BOLD, 40)
        draw.text((cx-10, head_y-head_r-40), "!", font=font_ex, fill=(255, 60, 60))
    
    # Laptop
    laptop_y = body_top + 140
    draw.rectangle([cx-95, laptop_y, cx+95, laptop_y+45], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([cx-85, laptop_y+5, cx+85, laptop_y+40], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        ly = laptop_y + 12 + i * 9
        draw.line([(cx-75, ly), (cx+75, ly)], fill=(0, 120, 180), width=1)
    draw.rectangle([cx-100, laptop_y+45, cx+100, laptop_y+55], fill=(60, 48, 38), outline=(40, 35, 25), width=2)
    
    # Chair
    draw.rectangle([cx-38, body_top+140, cx+38, body_top+240], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([cx-33, body_top+85, cx+33, body_top+145], fill=(40, 40, 45), outline=(60, 60, 65), width=2)

def draw_background(draw, t):
    # Wall
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(22, 22, 32))
    
    # Floor
    floor_y = int(HEIGHT * 0.78)
    draw.rectangle([0, floor_y, WIDTH, HEIGHT], fill=(30, 25, 20))
    draw.rectangle([0, floor_y-3, WIDTH, floor_y], fill=(40, 35, 25))
    
    # Window
    wx, wy, ww, wh = 60, 180, 280, 380
    draw.rectangle([wx, wy, wx+ww, wy+wh], fill=(15, 25, 45), outline=(70, 60, 50), width=4)
    draw.line([(wx+ww//2, wy), (wx+ww//2, wy+wh)], fill=(70, 60, 50), width=3)
    draw.line([(wx, wy+wh//2), (wx+ww, wy+wh//2)], fill=(70, 60, 50), width=3)
    draw.rectangle([wx-10, wy+wh, wx+ww+10, wy+wh+8], fill=(70, 60, 50))
    for i in range(5):
        a = 12 - i*2
        draw.rectangle([wx+5, wy+5+i*12, wx+ww-5, wy+wh-5], fill=(20+a, 30+a, 50+a))
    cloud_x = (int(t * 15) % (ww + 80)) - 40
    draw.ellipse([wx+cloud_x, wy+40, wx+cloud_x+50, wy+65], fill=(35, 45, 65))
    draw.ellipse([wx+cloud_x+25, wy+25, wx+cloud_x+75, wy+55], fill=(35, 45, 65))
    
    # Desk
    dx, dy = WIDTH//2 - 160, int(HEIGHT * 0.68)
    draw.rectangle([dx, dy, dx+320, dy+20], fill=(65, 52, 38), outline=(45, 35, 25), width=2)
    draw.rectangle([dx+15, dy+20, dx+30, dy+100], fill=(45, 35, 25), outline=(30, 25, 15), width=1)
    draw.rectangle([dx+290, dy+20, dx+305, dy+100], fill=(45, 35, 25), outline=(30, 25, 15), width=1)
    
    # Laptop
    lx, ly = dx + 90, dy - 5
    draw.rectangle([lx, ly-45, lx+140, ly], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([lx+5, ly-40, lx+135, ly-5], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
    for i in range(3):
        lly = ly - 32 + i * 9
        draw.line([(lx+10, lly), (lx+130, lly)], fill=(0, 120, 180), width=1)
    draw.rectangle([lx-5, ly, lx+145, ly+8], fill=(30, 30, 40), outline=(60, 60, 70), width=1)
    
    # Chair
    cx, cy = WIDTH//2 - 35, dy + 15
    draw.rectangle([cx, cy, cx+70, cy+90], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    draw.rectangle([cx+5, cy-70, cx+65, cy], fill=(40, 40, 45), outline=(60, 60, 65), width=2)
    
    # Plant
    px, py = WIDTH - 130, int(HEIGHT * 0.62)
    draw.rectangle([px-6, py, px+6, py+50], fill=(60, 40, 20), outline=(40, 30, 15), width=1)
    sway = math.sin(t * 1.5) * 6
    for i in range(6):
        angle = (i * 60 + sway) % 360
        rad = math.radians(angle)
        lx_p = px + int(22 * math.cos(rad))
        ly_p = py - 15 - int(18 * math.sin(rad))
        draw.ellipse([lx_p-14, ly_p-10, lx_p+14, ly_p+10], fill=(40, 120, 50), outline=(30, 80, 40), width=1)
    
    # Lamp
    lamp_x, lamp_y = 180, int(HEIGHT * 0.32)
    draw.rectangle([lamp_x-3, lamp_y, lamp_x+3, lamp_y+120], fill=(80, 70, 50), outline=(60, 50, 30), width=1)
    draw.polygon([(lamp_x-28, lamp_y-25), (lamp_x+28, lamp_y-25), (lamp_x+18, lamp_y), (lamp_x-18, lamp_y)], fill=(200, 180, 120), outline=(150, 130, 80), width=1)
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

def draw_text(draw, text, font, y, color, alpha=1.0):
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
    
    draw_background(draw, t)
    
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
