#!/bin/bash
FONT_BOLD=/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/BricolageGrotesque-Bold.ttf
FONT_REG=/data/data/com.termux/files/home/.config/opencode/skills/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf
OUT=/storage/7544-8C33/output/DarkPsi_Ep1_Text.mp4

ffmpeg -y -f lavfi -i color=c=0x0d0d0d:s=1080x1920:d=30:r=30 \
  -vf "
    drawtext=fontfile=${FONT_BOLD}:text='DIA BILANG':fontsize=72:fontcolor=0xff4444:x=(w-text_w)/2:y=h*0.35:enable='between(t\,0\,1.5)',
    drawtext=fontfile=${FONT_BOLD}:text='AKU CUMA BERCANDA':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=h*0.45:enable='between(t\,1.5\,3)',
    drawtext=fontfile=${FONT_BOLD}:text='TAPI SEBENARNYA':fontsize=64:fontcolor=0xff4444:x=(w-text_w)/2:y=h*0.55:enable='between(t\,3\,5)',
    drawtext=fontfile=${FONT_REG}:text='Robert Greene - 48 Laws of Power':fontsize=36:fontcolor=0x888888:x=(w-text_w)/2:y=h*0.15:enable='between(t\,5\,8)',
    drawtext=fontfile=${FONT_REG}:text='Law 3 - Conceal Your Intentions':fontsize=44:fontcolor=0xffaa00:x=(w-text_w)/2:y=h*0.22:enable='between(t\,5\,8)',
    drawtext=fontfile=${FONT_BOLD}:text='TANDA 1':fontsize=60:fontcolor=0xff4444:x=(w-text_w)/2:y=h*0.35:enable='between(t\,8\,13)',
    drawtext=fontfile=${FONT_REG}:text='Jawaban selalu ambigu':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h*0.45:enable='between(t\,8\,13)',
    drawtext=fontfile=${FONT_REG}:text='Tidak pernah jelas selalu nanti atau lihat dulu':fontsize=36:fontcolor=0xcccccc:x=(w-text_w)/2:y=h*0.55:enable='between(t\,8\,13)',
    drawtext=fontfile=${FONT_BOLD}:text='TANDA 2':fontsize=60:fontcolor=0xff4444:x=(w-text_w)/2:y=h*0.35:enable='between(t\,13\,18)',
    drawtext=fontfile=${FONT_REG}:text='Tidak pernah komitmen jelas':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h*0.45:enable='between(t\,13\,18)',
    drawtext=fontfile=${FONT_REG}:text='Selalu ada alasan untuk tidak menepati janji':fontsize=36:fontcolor=0xcccccc:x=(w-text_w)/2:y=h*0.55:enable='between(t\,13\,18)',
    drawtext=fontfile=${FONT_BOLD}:text='TANDA 3':fontsize=60:fontcolor=0xff4444:x=(w-text_w)/2:y=h*0.35:enable='between(t\,18\,23)',
    drawtext=fontfile=${FONT_REG}:text='Selalu ada alasan berubah-ubah':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h*0.45:enable='between(t\,18\,23)',
    drawtext=fontfile=${FONT_REG}:text='Hari ini alasan A besok alasan B':fontsize=36:fontcolor=0xcccccc:x=(w-text_w)/2:y=h*0.55:enable='between(t\,18\,23)',
    drawtext=fontfile=${FONT_BOLD}:text='CARA MELINDUNGI DIRI':fontsize=52:fontcolor=0x00ff88:x=(w-text_w)/2:y=h*0.35:enable='between(t\,23\,27)',
    drawtext=fontfile=${FONT_REG}:text='Tanya kenapa sampai dapat jawaban jelas':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=h*0.45:enable='between(t\,23\,27)',
    drawtext=fontfile=${FONT_REG}:text='Jika tidak bisa jawab RED FLAG':fontsize=40:fontcolor=0xff4444:x=(w-text_w)/2:y=h*0.55:enable='between(t\,23\,27)',
    drawtext=fontfile=${FONT_BOLD}:text='SIMPAN  SHARE  FOLLOW':fontsize=44:fontcolor=0xffaa00:x=(w-text_w)/2:y=h*0.45:enable='between(t\,27\,30)'
  " -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p -movflags +faststart -an "$OUT" 2>&1 | tail -5