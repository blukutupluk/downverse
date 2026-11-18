#!/data/data/com.termux/files/usr/bin/fish
# Konfigurasi backend Termux/Debian untuk proyek downloader yang SUDAH ADA.
# Installer ini tidak membuat/mengunduh file aplikasi.
set -l ROOT $HOME
set -l PROJECT $HOME/downloader
set -l SDROOT /storage/7544-8C33
set -l OUT $SDROOT/output
set -l DISTRO debian

function remove_ready_marker
    rm -f "$HOME/.media-downloader-ready"
end

function fail
    # Marker tidak boleh tertinggal saat instalasi gagal atau parsial.
    remove_ready_marker
    echo "[ERROR] $argv" >&2
    exit 1
end

function require_project_file
    if not test -f "$argv[1]"
        fail "Komponen proyek tidak ditemukan: $argv[1]. Proyek harus sudah disalin lengkap ke $HOME/downloader (lihat README.txt bagian Prasyarat Proyek)."
    end
end

function validate_project_layout
    set -l project "$HOME/downloader"
    require_project_file "$HOME/downloader.sh"
    require_project_file "$project/config.sh"
    for rel in lib/ui.sh lib/logging.sh lib/proot.sh lib/common.sh lib/checks.sh
        require_project_file "$project/$rel"
    end
    for mod in youtube instagram facebook tiktok threads audio spotify carousel
        require_project_file "$project/modules/$mod.sh"
    end
    require_project_file "$project/backend/threads_capture.py"
end

function make_executable
    if not chmod +x "$argv[1]"
        fail "Gagal chmod +x: $argv[1]"
    end
    if not test -x "$argv[1]"
        fail "File tidak executable setelah chmod: $argv[1]"
    end
end

# Hapus status lama sebelum pemeriksaan apa pun.
remove_ready_marker

if not command -q pkg
    fail "Installer ini harus dijalankan di Termux."
end

# Validasi proyek sebelum menyentuh paket/Debian. Gagal cepat = aman.
validate_project_layout
printf '[OK] Struktur proyek tervalidasi: %s\n' "$HOME/downloader"

printf '\n%s\n' '=== TERMUX FOUNDATION ==='
pkg update -y
or fail "pkg update gagal. Periksa repo Termux dengan termux-change-repo, lalu ulangi."

# Termux rolling-release: seluruh paket harus sinkron sebelum paket baru dipasang.
printf '\n%s\n' '=== FULL TERMUX PACKAGE UPGRADE ==='
pkg upgrade -y
or fail "Upgrade paket Termux gagal. Pulihkan package state terlebih dahulu; jangan lanjut memasang FFmpeg/PRoot."

# Pisahkan instalasi agar kegagalan paket terlihat jelas dan dapat diulang.
pkg install -y fish python
or fail "Fish/Python gagal dipasang."
pkg install -y proot-distro
or fail "PRoot-Distro gagal dipasang. Jalankan termux-change-repo, pilih mirror resmi, lalu ulangi."
pkg install -y ffmpeg curl wget termux-tools
or fail "Paket media/Termux gagal dipasang. Jalankan pkg update -y lalu pkg upgrade -y sebelum mengulang installer."

# Pastikan binary FFmpeg bukan sekadar ada, tetapi dapat dimuat oleh Android linker.
if not ffmpeg -version >/dev/null 2>&1
    fail "FFmpeg Termux terpasang tetapi gagal dijalankan (kemungkinan library belum sinkron). Jalankan: pkg update -y; and pkg upgrade -y; and dpkg --configure -a; lalu ulangi installer."
end
if not ffprobe -version >/dev/null 2>&1
    fail "FFprobe Termux terpasang tetapi gagal dijalankan. Pulihkan semua paket Termux sebelum melanjutkan."
end
printf '[OK] FFmpeg Termux: '
ffmpeg -version | head -n 1

if not command -q proot-distro
    fail "Paket proot-distro dilaporkan terpasang tetapi executable tidak ditemukan di PATH. Cek: echo \"$PATH\" dan ls -l $PREFIX/bin/proot-distro"
end
if not command -q proot
    pkg install -y proot
    or fail "Binary proot gagal dipasang."
end
printf '[OK] proot-distro: %s\n' (command -s proot-distro)
printf '[OK] proot: %s\n' (command -s proot)

# Android akan meminta izin akses file. User harus menyetujui dialognya.
if command -q termux-setup-storage
    termux-setup-storage
end

mkdir -p "$HOME/cookies" "$OUT" "$PROJECT/logs" "$HOME/bin"

printf '\n%s\n' '=== EXTERNAL STORAGE CHECK ==='
if not test -d "$SDROOT"
    fail "SD card tidak terlihat: $SDROOT. Jalankan termux-setup-storage dan pastikan izin Android diberikan. Tidak ada fallback ke storage internal."
end
mkdir -p "$OUT"
set -l probe "$OUT/.downloader_probe_$fish_pid"
if touch "$probe" 2>/dev/null
    rm -f "$probe"
    echo "[OK] SD card writable: $OUT"
else
    fail "SD card ditemukan tetapi output tidak bisa ditulis: $OUT. Periksa izin Android."
end

printf '\n%s\n' '=== DEBIAN PROOT ==='
if not proot-distro login "$DISTRO" -- /bin/true >/dev/null 2>&1
    proot-distro install "$DISTRO"
    or fail "Instalasi Debian gagal. Periksa jaringan/storage lalu ulangi install.fish."
end

# Create an otherwise-empty destination inside the Debian rootfs, then bind
# the real removable volume over it for all downloader sessions.
proot-distro login "$DISTRO" -- mkdir -p "$OUT"
or fail "Tidak bisa menyiapkan mount point SD card di Debian."
set -l host_id (stat -c '%d:%i' "$OUT")
set -l guest_id (proot-distro login --bind "$OUT:$OUT" "$DISTRO" -- stat -c '%d:%i' "$OUT")
or fail "Debian tidak bisa mengakses output melalui bind mount SD card."
if test "$host_id" != "$guest_id"
    fail "Bind mount SD card gagal diverifikasi. Termux=$host_id Debian=$guest_id. Installer dihentikan."
end
echo "[OK] Bind mount output SD card terverifikasi: $host_id"

proot-distro login "$DISTRO" -- bash -lc 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl wget ffmpeg python3 python3-venv python3-pip chromium fonts-liberation'
or fail "Dependency Debian gagal dipasang."

printf '\n%s\n' '=== PYTHON VENV + MEDIA TOOLS ==='
proot-distro login "$DISTRO" -- bash -lc 'python3 -m venv /opt/media-downloader-venv && /opt/media-downloader-venv/bin/python -m pip install --upgrade pip setuptools wheel && /opt/media-downloader-venv/bin/pip install --upgrade yt-dlp gallery-dl spotdl playwright requests'
or fail "Instalasi venv/alat Python gagal."

printf '\n%s\n' '=== VERIFY CHROMIUM + PLAYWRIGHT ==='
proot-distro login "$DISTRO" -- /opt/media-downloader-venv/bin/python -c 'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox","--disable-gpu"]); page=b.new_page(); page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000); print("Chromium + Playwright OK:", page.title()); b.close(); p.stop()'
or fail "Tes Chromium + Playwright gagal. Jangan lanjut menjalankan downloader."

make_executable "$HOME/downloader.sh"
make_executable "$PROJECT/modules/threads.sh"
fish_add_path "$HOME/bin"

# Alias praktis untuk launcher.
printf '%s\n' '#!/data/data/com.termux/files/usr/bin/bash' 'exec bash "$HOME/downloader.sh"' > "$HOME/bin/downloader"
or fail "Gagal menulis shortcut: $HOME/bin/downloader"
if not test -f "$HOME/bin/downloader"
    fail "Shortcut bukan file biasa: $HOME/bin/downloader"
end
make_executable "$HOME/bin/downloader"

# Upayakan Fish menjadi shell default; jika chsh tak tersedia, Fish tetap dapat dipanggil manual.
if command -q chsh
    chsh -s "$PREFIX/bin/fish" 2>/dev/null
end

# Revalidasi terakhir: marker hanya boleh ditulis jika semua komponen masih ada.
validate_project_layout
printf '%s\n' 'ready' > "$HOME/.media-downloader-ready"
or fail "Gagal menulis marker: $HOME/.media-downloader-ready"
if not test -s "$HOME/.media-downloader-ready"
    fail "Marker kosong/tidak valid: $HOME/.media-downloader-ready"
end

printf '\n%s\n' '=== KONFIGURASI BACKEND SELESAI (PROYEK TERVALIDASI) ==='
echo "Proyek   : $PROJECT (tidak dibuat installer; hanya divalidasi)"
echo "Launcher : bash ~/downloader.sh"
echo "Shortcut : downloader"
echo "Cookies  : ~/cookies/threads.txt (ekspor Netscape; jangan tempel isi cookie ke chat)"
echo "SD card  : $SDROOT (bind mount wajib)"
echo "Output   : $OUT/"
echo "Threads  : /storage/7544-8C33/output/Threads"
echo "Debian   : $DISTRO"
echo "Venv     : /opt/media-downloader-venv"
echo ""
echo "Carousel Threads belum diklaim teruji; uji dengan URL carousel nyata setelah install."
echo "Buka Fish sekarang."
exec fish
