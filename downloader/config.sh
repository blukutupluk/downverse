# Konfigurasi utama. Dapat dioverride melalui environment sebelum launcher.
PROOT_DISTRO="${PROOT_DISTRO:-debian}"
PROOT_VENV="${PROOT_VENV:-/opt/media-downloader-venv}"
PROOT_PYTHON="$PROOT_VENV/bin/python"
YTDLP_BIN="$PROOT_VENV/bin/yt-dlp"
GALLERYDL_BIN="$PROOT_VENV/bin/gallery-dl"
SPOTDL_BIN="$PROOT_VENV/bin/spotdl"

# SD card eksternal yang sudah dikonfirmasi pengguna.
SDCARD_ROOT="${SDCARD_ROOT:-/storage/7544-8C33}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$SDCARD_ROOT/output}"
THREADS_OUTPUT="$OUTPUT_ROOT/Threads"

COOKIE_DIR="${COOKIE_DIR:-$HOME/cookies}"
THREADS_COOKIE="${THREADS_COOKIE:-$COOKIE_DIR/threads.txt}"
INSTAGRAM_COOKIE="${INSTAGRAM_COOKIE:-$COOKIE_DIR/instagram.txt}"
FACEBOOK_COOKIE="${FACEBOOK_COOKIE:-$COOKIE_DIR/facebook.txt}"
YOUTUBE_COOKIE="${YOUTUBE_COOKIE:-$COOKIE_DIR/youtube.txt}"

LOG_DIR="$BASE_DIR/logs"
