#!/usr/bin/env python3
import os, math, random
from PIL import Image, ImageDraw

W, H = 1080, 1920
BG_PATH = "/data/data/com.termux/files/usr/tmp/opencode/darkpsi_bg.png"

img = Image.new('RGB', (W, H), (18, 18, 28))
draw = ImageDraw.Draw(img)

# Wall
draw.rectangle([0, 0, W, H], fill=(22, 22, 32))

# Floor
floor_y = int(H * 0.78)
draw.rectangle([0, floor_y, W, H], fill=(30, 25, 20))
draw.rectangle([0, floor_y-3, W, floor_y], fill=(40, 35, 25))

# Window
wx, wy, ww, wh = 60, 180, 280, 380
draw.rectangle([wx, wy, wx+ww, wy+wh], fill=(15, 25, 45), outline=(70, 60, 50), width=4)
draw.line([(wx+ww//2, wy), (wx+ww//2, wy+wh)], fill=(70, 60, 50), width=3)
draw.line([(wx, wy+wh//2), (wx+ww, wy+wh//2)], fill=(70, 60, 50), width=3)
draw.rectangle([wx-10, wy+wh, wx+ww+10, wy+wh+8], fill=(70, 60, 50))
for i in range(5):
    a = 12 - i*2
    draw.rectangle([wx+5, wy+5+i*12, wx+ww-5, wy+wh-5], fill=(20+a, 30+a, 50+a))
draw.ellipse([wx+20, wy+40, wx+70, wy+65], fill=(35, 45, 65))
draw.ellipse([wx+45, wy+25, wx+95, wy+55], fill=(35, 45, 65))

# Desk
dx, dy = W//2 - 160, int(H * 0.68)
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
cx, cy = W//2 - 35, dy + 15
draw.rectangle([cx, cy, cx+70, cy+90], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
draw.rectangle([cx+5, cy-70, cx+65, cy], fill=(40, 40, 45), outline=(60, 60, 65), width=2)

# Plant
px, py = W - 130, int(H * 0.62)
draw.rectangle([px-6, py, px+6, py+50], fill=(60, 40, 20), outline=(40, 30, 15), width=1)
for i in range(6):
    angle = i * 60
    rad = math.radians(angle)
    lx_p = px + int(22 * math.cos(rad))
    ly_p = py - 15 - int(18 * math.sin(rad))
    draw.ellipse([lx_p-14, ly_p-10, lx_p+14, ly_p+10], fill=(40, 120, 50), outline=(30, 80, 40), width=1)

# Lamp
lamp_x, lamp_y = 180, int(H * 0.32)
draw.rectangle([lamp_x-3, lamp_y, lamp_x+3, lamp_y+120], fill=(80, 70, 50), outline=(60, 50, 30), width=1)
draw.polygon([(lamp_x-28, lamp_y-25), (lamp_x+28, lamp_y-25), (lamp_x+18, lamp_y), (lamp_x-18, lamp_y)], fill=(200, 180, 120), outline=(150, 130, 80), width=1)
for i in range(6):
    r = 35 + i * 12
    draw.ellipse([lamp_x-r, lamp_y-25-r, lamp_x+r, lamp_y-25+r], fill=(255, 220, 150))

# Shelf
shelf_y = int(H * 0.28)
draw.rectangle([W-220, shelf_y, W-40, shelf_y+8], fill=(50, 40, 30), outline=(30, 25, 15), width=1)
for i in range(5):
    bx = W - 210 + i * 32
    bh = 20 + (i % 3) * 8
    draw.rectangle([bx, shelf_y-bh, bx+22, shelf_y], fill=(60+i*15, 40+i*8, 30+i*5), outline=(30, 25, 15), width=1)

# Character (center, detailed)
cx, cy = W//2, int(H * 0.62)
draw.ellipse([cx-52, cy-237, cx+52, cy-133], fill=(220, 180, 150), outline=(10, 10, 15), width=2)
draw.ellipse([cx-55, cy-245, cx+55, cy-175], fill=(35, 25, 15), outline=(10, 10, 15), width=1)
draw.rectangle([cx-55, cy-245, cx+55, cy-200], fill=(35, 25, 15))
eye_y = cy - 188
draw.ellipse([cx-26, eye_y-5, cx-10, eye_y+7], fill=(255, 255, 255))
draw.ellipse([cx-22, eye_y-1, cx-14, eye_y+5], fill=(30, 30, 30))
draw.ellipse([cx+10, eye_y-5, cx+26, eye_y+7], fill=(255, 255, 255))
draw.ellipse([cx+14, eye_y-1, cx+22, eye_y+5], fill=(30, 30, 30))
draw.line([(cx-26, eye_y-12), (cx-10, eye_y-12)], fill=(35, 25, 15), width=2)
draw.line([(cx+10, eye_y-12), (cx+26, eye_y-12)], fill=(35, 25, 15), width=2)
draw.line([(cx-12, eye_y+30), (cx+12, eye_y+30)], fill=(180, 80, 80), width=2)
draw.rectangle([cx-50, cy-133, cx+50, cy+12], fill=(35, 45, 65), outline=(10, 10, 15), width=2)
draw.rectangle([cx-48, cy-131, cx, cy+10], fill=(50, 60, 85))
draw.line([(cx-50, cy-113), (cx-85, cy-70)], fill=(50, 60, 85), width=5)
draw.ellipse([cx-90, cy-75, cx-80, cy-65], fill=(220, 180, 150), outline=(10, 10, 15), width=1)
draw.line([(cx+50, cy-113), (cx+85, cy-70)], fill=(50, 60, 85), width=5)
draw.ellipse([cx+80, cy-75, cx+90, cy-65], fill=(220, 180, 150), outline=(10, 10, 15), width=1)
draw.rectangle([cx-95, cy+12, cx+95, cy+52], fill=(25, 25, 35), outline=(80, 80, 90), width=2)
draw.rectangle([cx-85, cy+17, cx+85, cy+47], fill=(0, 20, 50), outline=(0, 80, 130), width=1)
for i in range(3):
    ly = cy + 22 + i * 8
    draw.line([(cx-75, ly), (cx+75, ly)], fill=(0, 120, 180), width=1)
draw.rectangle([cx-100, cy+52, cx+100, cy+62], fill=(60, 48, 38), outline=(40, 35, 25), width=2)
draw.rectangle([cx-38, cy+12, cx+38, cy+112], fill=(35, 35, 40), outline=(60, 60, 65), width=2)
draw.rectangle([cx-33, cy-50, cx+33, cy+12], fill=(40, 40, 45), outline=(60, 60, 65), width=2)

# Particles
random.seed(42)
for _ in range(30):
    px = random.randint(0, W)
    py = random.randint(0, H)
    size = random.randint(1, 2)
    brightness = random.randint(20, 50)
    draw.ellipse([px-size, py-size, px+size, py+size], fill=(brightness, brightness, brightness))

# Vignette
for i in range(50):
    draw.rectangle([i, i, W-i, H-i], outline=(0, 0, 0), width=1)

img.save(BG_PATH)
print("Background saved")
" 2>&1 | tail -3