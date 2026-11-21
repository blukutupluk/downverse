#!/usr/bin/env python3
# Character Animation System v1 — inspired by Stick (skeleton + procedural animation)
# Implements: skeleton joints, procedural breathing/blink/sway, expressions, gestures
# Environment: Termux (Python 3 + PIL + ffmpeg)

import os, math, random
from PIL import Image, ImageDraw, ImageFont

# === CONFIG ===
WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION
OUTPUT_DIR = "/data/data/com.termux/files/usr/tmp/opencode/char_frames"
OUTPUT_VIDEO = "/storage/7544-8C33/output/DarkPsi_CharAnim_v1.mp4"

FONT_BOLD = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/BricolageGrotesque-Bold.ttf"
FONT_REG = "/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf"

# === COLOR PALETTE ===
C = {
    "skin": (220, 180, 150),
    "skin_shadow": (180, 140, 110),
    "hair": (40, 30, 20),
    "shirt": (30, 40, 60),
    "shirt_highlight": (50, 60, 80),
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
    "accent_gray": (140, 140, 140),
}

# === SKELETON (inspired by Stick) ===
class Skeleton:
    """Named joints with bone hierarchy"""
    def __init__(self, x, y, height=400, scale=1.0):
        self.x = x
        self.y = y
        self.h = height * scale
        self.scale = scale
        
        # Proportions (inspired by Stick's geom)
        self.head_r = 0.135 * self.h
        self.neck_len = 0.045 * self.h
        self.torso = 0.30 * self.h
        self.upper_arm = 0.20 * self.h
        self.forearm = 0.175 * self.h
        self.thigh = 0.22 * self.h
        self.shin = 0.22 * self.h
        self.foot = 0.10 * self.h
        
        # Joint positions (relative to origin)
        self.joints = {}
        self._compute_base()
    
    def _compute_base(self):
        """Compute base joint positions"""
        self.joints = {
            "pelvis": (0, 0),
            "neck": (0, -self.torso),
            "head": (0, -self.torso - self.neck_len - self.head_r),
            "shoulder_l": (-0.08 * self.h, -self.torso + 0.05 * self.h),
            "shoulder_r": (0.08 * self.h, -self.torso + 0.05 * self.h),
            "elbow_l": (-0.15 * self.h, -self.torso + 0.15 * self.h),
            "elbow_r": (0.15 * self.h, -self.torso + 0.15 * self.h),
            "hand_l": (-0.18 * self.h, -self.torso + 0.28 * self.h),
            "hand_r": (0.18 * self.h, -self.torso + 0.28 * self.h),
            "hip_l": (-0.06 * self.h, 0),
            "hip_r": (0.06 * self.h, 0),
            "knee_l": (-0.08 * self.h, self.thigh),
            "knee_r": (0.08 * self.h, self.thigh),
            "ankle_l": (-0.08 * self.h, self.thigh + self.shin),
            "ankle_r": (0.08 * self.h, self.thigh + self.shin),
        }

# === EXPRESSIONS ===
EXPRESSIONS = {
    "neutral": {"eye_open": 1.0, "brow_raise": 0.0, "brow_tilt": 0.0, "mouth": "neutral", "mouth_open": 0.0},
    "confused": {"eye_open": 0.9, "brow_raise": 0.3, "brow_tilt": 0.5, "mouth": "flat", "mouth_open": 0.0},
    "suspicious": {"eye_open": 0.6, "brow_raise": 0.5, "brow_tilt": -0.3, "mouth": "flat", "mouth_open": 0.0},
    "deceptive": {"eye_open": 0.9, "brow_raise": 0.0, "brow_tilt": 0.0, "mouth": "smirk", "mouth_open": 0.0},
    "warning": {"eye_open": 1.0, "brow_raise": 0.8, "brow_tilt": 0.0, "mouth": "open", "mouth_open": 0.3},
    "protected": {"eye_open": 0.9, "brow_raise": 0.0, "brow_tilt": 0.0, "mouth": "flat", "mouth_open": 0.0},
    "wise": {"eye_open": 0.7, "brow_raise": 0.2, "brow_tilt": 0.0, "mouth": "smile", "mouth_open": 0.0},
    "happy": {"eye_open": 0.8, "brow_raise": 0.3, "brow_tilt": 0.0, "mouth": "smile", "mouth_open": 0.1},
    "sad": {"eye_open": 0.6, "brow_raise": -0.3, "brow_tilt": 0.0, "mouth": "frown", "mouth_open": 0.0},
    "surprised": {"eye_open": 1.0, "brow_raise": 1.0, "brow_tilt": 0.0, "mouth": "open", "mouth_open": 0.5},
    "thinking": {"eye_open": 0.8, "brow_raise": 0.4, "brow_tilt": 0.3, "mouth": "flat", "mouth_open": 0.0},
}

# === GESTURES ===
GESTURES = {
    "idle": {"arm_l": (0, 0), "arm_r": (0, 0), "head_tilt": 0},
    "point": {"arm_l": (0, 0), "arm_r": (1, -0.5), "head_tilt": 0.1},
    "explain": {"arm_l": (0.5, -0.3), "arm_r": (0.5, -0.3), "head_tilt": 0},
    "think": {"arm_l": (0, 0), "arm_r": (0.3, -0.8), "head_tilt": 0.2},
    "emphasize": {"arm_l": (0.8, -0.5), "arm_r": (0.8, -0.5), "head_tilt": 0},
    "shrug": {"arm_l": (-0.5, -0.3), "arm_r": (0.5, -0.3), "head_tilt": 0},
    "wave": {"arm_l": (0, 0), "arm_r": (1, -1), "head_tilt": 0.1},
    "nod": {"arm_l": (0, 0), "arm_r": (0, 0), "head_tilt": -0.2},
    "crossed": {"arm_l": (0.3, 0), "arm_r": (-0.3, 0), "head_tilt": 0},
    "hands_up": {"arm_l": (-0.8, -1), "arm_r": (0.8, -1), "head_tilt": 0},
}

# === NARRATIVE SCENES ===
# Format: (start, end, title, subtitle, body, expression, gesture, bg_color, accent)
SCENES = [
    (0, 3, "DIA BILANG", "\"AKU CUMA BERCANDA\"", "", "suspicious", "idle", (13, 8, 8), (255, 68, 68)),
    (3, 5, "TAPI SEBENARNYA?", "", "", "suspicious", "think", (13, 8, 8), (255, 68, 68)),
    (5, 8, "Robert Greene", "48 Laws of Power - Law 3", "Conceal Your Intentions", "neutral", "explain", (20, 15, 5), (255, 170, 0)),
    (8, 11, "TANDA 1", "Jawaban selalu ambigu", "Tidak pernah jelas, selalu 'nanti' atau 'lihat dulu'", "confused", "shrug", (15, 10, 15), (255, 68, 68)),
    (11, 14, "", "Selalu ada alasan", "Kamu tanya kenapa dia tidak datang. Dia jawab: aku sibuk.", "confused", "think", (15, 10, 15), (255, 68, 68)),
    (14, 17, "TANDA 2", "Tidak pernah komitmen", "Selalu ada alasan untuk tidak menepati janji", "suspicious", "crossed", (15, 10, 15), (255, 68, 68)),
    (17, 20, "TANDA 3", "Selalu ada alasan baru", "Hari ini alasan A, besok alasan B", "deceptive", "explain", (15, 10, 15), (255, 68, 68)),
    (20, 23, "RED FLAG", "Jika dia tidak bisa jawab 'kenapa'", "dengan jawaban yang konsisten", "warning", "emphasize", (20, 5, 5), (255, 68, 68)),
    (23, 26, "CARA MELINDUNGI DIRI", "Tanya 'kenapa'", "sampai dapat jawaban jelas dan konsisten", "protected", "point", (5, 20, 10), (0, 255, 136)),
    (26, 28, "PELAJARAN", "Jangan percaya niat yang disembunyikan", "Orang yang jujur tidak takut menjelaskan", "wise", "nod", (20, 15, 5), (255, 170, 0)),
    (28, 30, "SIMPAN | SHARE | FOLLOW", "Episode 2: Court Attention", "Follow untuk episode selanjutnya", "happy", "wave", (10, 10, 10), (255, 170, 0)),
]

def lerp(a, b, t):
    return a + (b - a) * t

def ease_in_out(t):
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2

def draw_background(draw, t, bg_color, accent):
    """Draw atmospheric background with gradient and particles"""
    for y in range(HEIGHT):
        r = int(bg_color[0] + (accent[0] - bg_color[0]) * 0.12 * (1 - y / HEIGHT))
        g = int(bg_color[1] + (accent[1] - bg_color[1]) * 0.12 * (1 - y / HEIGHT))
        b = int(bg_color[2] + (accent[2] - bg_color[2]) * 0.12 * (1 - y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Vignette
    for i in range(60):
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0), width=1)
    
    # Floating particles (animated)
    import random
    random.seed(42)
    for _ in range(25):
        px = random.randint(0, WIDTH)
        py = (random.randint(0, HEIGHT) + int(t * 15)) % HEIGHT
        size = random.randint(1, 2)
        brightness = random.randint(15, 50)
        draw.ellipse([px-size, py-size, px+size, py+size], fill=(brightness, brightness, brightness))

def draw_character(draw, t, pose, expression, cx, cy):
    """Draw expressive character with skeleton-based proportions"""
    s = 1.0
    skel = Skeleton(cx, cy, 350, s)
    j = skel.joints
    
    # Breathing animation
    breath = 0.02 * math.sin(t * 2.5)
    sway = 0.015 * math.sin(t * 1.8)
    blink = 1.0 if (t % 3.5) > 0.15 else 0.1  # blink every ~3.5s
    
    # Idle sway
    cx_offset = int(sway * 100)
    cy_offset = int(breath * 50)
    
    # Head position
    head_cx = cx + cx_offset
    head_cy = cy - 200 + cy_offset
    
    # Head
    head_r = int(55 * s)
    draw.ellipse([head_cx-head_r, head_cy-head_r, head_cx+head_r, head_cy+head_r], 
                 fill=C["skin"], outline=C["outline"], width=2)
    
    # Hair
    draw.ellipse([head_cx-head_r-3, head_cy-head_r-8, head_cx+head_r+3, head_cy-20*s], 
                 fill=C["hair"], outline=C["outline"], width=1)
    
    # Eyes
    eye_y = head_cy - 5
    eye_l = head_cx - 18
    eye_r = head_cx + 18
    expr = EXPRESSIONS.get(expression, EXPRESSIONS["neutral"])
    
    eye_open = expr["eye_open"] * blink
    brow_raise = expr["brow_raise"]
    brow_tilt = expr["brow_tilt"]
    
    # Left eye
    if eye_open > 0.1:
        draw.ellipse([eye_l-8, eye_y-int(8*eye_open), eye_l+8, eye_y+int(8*eye_open)], fill=C["eyes_highlight"])
        draw.ellipse([eye_l-4, eye_y-int(4*eye_open), eye_l+4, eye_y+int(4*eye_open)], fill=C["eyes"])
    else:
        draw.line([(eye_l-8, eye_y), (eye_l+8, eye_y)], fill=C["eyes"], width=2)
    
    # Right eye
    if eye_open > 0.1:
        draw.ellipse([eye_r-8, eye_y-int(8*eye_open), eye_r+8, eye_y+int(8*eye_open)], fill=C["eyes_highlight"])
        draw.ellipse([eye_r-4, eye_y-int(4*eye_open), eye_r+4, eye_y+int(4*eye_open)], fill=C["eyes"])
    else:
        draw.line([(eye_r-8, eye_y), (eye_r+8, eye_y)], fill=C["eyes"], width=2)
    
    # Eyebrows
    brow_y = eye_y - 12
    brow_tilt_px = int(brow_tilt * 8)
    # Left brow
    draw.line([(eye_l-10, brow_y - int(brow_raise*5) + brow_tilt_px), 
               (eye_l+10, brow_y - int(brow_raise*5) - brow_tilt_px)], fill=C["hair"], width=2)
    # Right brow
    draw.line([(eye_r-10, brow_y - int(brow_raise*5) - brow_tilt_px), 
               (eye_r+10, brow_y - int(brow_raise*5) + brow_tilt_px)], fill=C["hair"], width=2)
    
    # Mouth
    mouth_y = eye_y + 25
    mouth_type = expr["mouth"]
    mouth_open = expr["mouth_open"]
    
    if mouth_type == "smile":
        draw.arc([head_cx-12, mouth_y-5, head_cx+12, mouth_y+8], 0, 180, fill=C["mouth"], width=2)
    elif mouth_type == "frown":
        draw.arc([head_cx-12, mouth_y, head_cx+12, mouth_y+12], 180, 360, fill=C["mouth"], width=2)
    elif mouth_type == "open":
        draw.ellipse([head_cx-8, mouth_y-4, head_cx+8, mouth_y+4+int(mouth_open*8)], fill=C["mouth"])
    elif mouth_type == "smirk":
        draw.arc([head_cx-5, mouth_y-3, head_cx+15, mouth_y+8], 0, 180, fill=C["mouth"], width=2)
    else:  # flat/neutral
        draw.line([(head_cx-10, mouth_y), (head_cx+10, mouth_y)], fill=C["mouth"], width=2)
    
    # Body
    body_top = head_cy + head_r + 5
    draw.rectangle([cx-45, body_top, cx+45, body_top+130], fill=C["shirt"], outline=C["outline"], width=2)
    
    # Arms (gesture-based)
    gesture = GESTURES.get(pose if pose in GESTURES else "idle", GESTURES["idle"])
    arm_l = gesture["arm_l"]
    arm_r = gesture["arm_r"]
    head_tilt = gesture["head_tilt"]
    
    # Head tilt
    if head_tilt != 0:
        # Simple head tilt indicator
        pass
    
    # Left arm
    arm_y = body_top + 15
    al_x = cx - 45 + int(arm_l[0] * 40)
    al_y = arm_y + int(arm_l[1] * 40)
    draw.line([(cx-45, arm_y), (al_x, al_y)], fill=C["shirt_highlight"], width=4)
    draw.ellipse([al_x-6, al_y-6, al_x+6, al_y+6], fill=C["skin"])  # hand
    
    # Right arm
    ar_x = cx + 45 + int(arm_r[0] * 40)
    ar_y = arm_y + int(arm_r[1] * 40)
    draw.line([(cx+45, arm_y), (ar_x, ar_y)], fill=C["shirt_highlight"], width=4)
    draw.ellipse([ar_x-6, ar_y-6, ar_x+6, ar_y+6], fill=C["skin"])  # hand
    
    # Laptop
    laptop_y = body_top + 130
    draw.rectangle([cx-90, laptop_y, cx+90, laptop_y+40], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
    draw.rectangle([cx-80, laptop_y+5, cx+80, laptop_y+35], fill=(0, 20, 40), outline=(0, 80, 120), width=1)
    
    # Table
    draw.rectangle([cx-120, laptop_y+40, cx+120, laptop_y+50], fill=(40, 30, 20), outline=(60, 50, 30), width=2)
    
    # Chair
    draw.rectangle([cx-30, body_top+130, cx+30, body_top+230], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
    
    # Pointing indicator (when gesture is point)
    if pose == "point":
        # Draw arrow from hand to text area
        draw.line([(ar_x, ar_y), (ar_x+30, ar_y-40)], fill=C["accent_yellow"], width=2)
        draw.polygon([(ar_x+30, ar_y-40), (ar_x+25, ar_y-30), (ar_x+35, ar_y-30)], fill=C["accent_yellow"])

def draw_background(draw, t, bg_color, accent):
    for y in range(HEIGHT):
        r = int(bg_color[0] + (accent[0] - bg_color[0]) * 0.12 * (1 - y / HEIGHT))
        g = int(bg_color[1] + (accent[1] - bg_color[1]) * 0.12 * (1 - y / HEIGHT))
        b = int(bg_color[2] + (accent[2] - bg_color[2]) * 0.12 * (1 - y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    for i in range(60):
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0), width=1)
    
    import random
    random.seed(42)
    for _ in range(25):
        px = random.randint(0, WIDTH)
        py = (random.randint(0, HEIGHT) + int(t * 15)) % HEIGHT
        size = random.randint(1, 2)
        brightness = random.randint(15, 50)
        draw.ellipse([px-size, py-size, px+size, py+size], fill=(brightness, brightness, brightness))

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
    start, end, title, subtitle, body, expression, gesture, bg_color, accent = scene
    
    scene_duration = end - start
    scene_progress = (t - start) / scene_duration if scene_duration > 0 else 0
    
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
    cy = int(HEIGHT * 0.60)
    draw_character(draw, t, gesture, expression, cx, cy)
    
    if title:
        font = ImageFont.truetype(FONT_BOLD, 68)
        draw_text(draw, title, font, int(HEIGHT * 0.10), accent, alpha)
    
    if subtitle:
        font = ImageFont.truetype(FONT_REG, 42)
        draw_text(draw, subtitle, font, int(HEIGHT * 0.18), (220, 220, 220), alpha)
    
    if body:
        font = ImageFont.truetype(FONT_REG, 34)
        draw_text(draw, body, font, int(HEIGHT * 0.26), (180, 180, 180), alpha)
    
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
