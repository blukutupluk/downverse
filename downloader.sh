#!/data/data/com.termux/files/usr/bin/bash
# Termux Media Downloader - launcher utama.
# Backend umum: Debian/PRoot. Threads: Chromium + Playwright + capture network.
BASE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Jangan aktifkan set -u: kompatibilitas dengan variabel UI opsional.
for _lib in config.sh lib/ui.sh lib/logging.sh lib/proot.sh lib/common.sh lib/checks.sh; do
  if [[ ! -f "$BASE_DIR/downloader/$_lib" ]]; then
    printf 'File library tidak ditemukan: %s\n' "$BASE_DIR/downloader/$_lib" >&2
    printf 'Instalasi rusak. Jalankan ulang: fish ~/install.fish\n' >&2
    exit 78
  fi
done
unset _lib

source "$BASE_DIR/downloader/config.sh"
source "$BASE_DIR/downloader/lib/ui.sh"
source "$BASE_DIR/downloader/lib/logging.sh"
source "$BASE_DIR/downloader/lib/proot.sh"
source "$BASE_DIR/downloader/lib/common.sh"
source "$BASE_DIR/downloader/lib/checks.sh"

if [[ ! -f "$HOME/.media-downloader-ready" ]]; then
  printf '\n%b\n' "${RED}${BOLD}SETUP BELUM SELESAI / BELUM LOLOS VERIFIKASI.${RESET}"
  printf 'Jalankan installer fondasi: fish ~/install.fish\n'
  printf 'Launcher dihentikan agar tidak menjalankan backend yang belum siap.\n'
  exit 78
fi

# Folder output baru dibuat setelah status kesiapan lolos. Jika kartu SD belum
# ter-mount, launcher tidak dihentikan agar Dependency Check tetap bisa dipakai.
STARTUP_NOTICE=""
if ! ensure_system_dirs 2>/dev/null; then
  STARTUP_NOTICE+="${RED}${BOLD}PERINGATAN: folder output gagal disiapkan: ${OUTPUT_ROOT}${RESET}"$'\n'
  STARTUP_NOTICE+="            Periksa akses kartu SD (${SDCARD_ROOT}) lalu jalankan: fish ~/install.fish"$'\n'
fi

if ! command -v proot-distro >/dev/null 2>&1; then
  STARTUP_NOTICE+="${RED}${BOLD}PERINGATAN: proot-distro belum tersedia di Termux.${RESET}"$'\n'
  STARTUP_NOTICE+="            Perbaikan: pkg update -y; pkg install -y proot-distro; fish ~/install.fish"$'\n'
fi

# Muat modul saat dipilih saja, dengan validasi file dan nama fungsi.
run_module() {
  local module="$1" func="$2" path
  path="$BASE_DIR/downloader/modules/$module.sh"
  if [[ ! -f "$path" ]]; then
    ui_error "Modul tidak ditemukan: $path"
    sleep 2
    return 1
  fi
  # shellcheck source=/dev/null
  source "$path"
  if ! declare -F "$func" >/dev/null 2>&1; then
    ui_error "Fungsi $func tidak ditemukan di $module.sh"
    sleep 2
    return 1
  fi
  "$func"
}

while true; do
  clear
  if [[ -n "$STARTUP_NOTICE" ]]; then
    printf '%b\n' "$STARTUP_NOTICE"
    STARTUP_NOTICE=""
  fi
  printf '\n%b\n' "${BOLD}${CYAN}  +----------------------------------------------+${RESET}"
  printf '%b\n' "${BOLD}${CYAN}  |          TERMUX MEDIA DOWNLOADER             |${RESET}"
  printf '%b\n' "${BOLD}${BLUE}  |       TERMUX LAUNCHER  /  DEBIAN BACKEND     |${RESET}"
  printf '%b\n' "${BOLD}${CYAN}  +----------------------------------------------+${RESET}"

  printf '\n%b\n' "${BOLD}${BLUE}  DOWNLOAD MEDIA${RESET}"
  ui_line
  ui_item "01" "YouTube" "Video tunggal dan playlist"
  ui_item "02" "Instagram" "Video / audio / post yang didukung"
  ui_item "03" "Facebook" "Video / audio / post yang didukung"
  ui_item "04" "TikTok" "Video dan media yang didukung"
  ui_item "05" "Threads" "Video saja; tanpa gambar dan tanpa traversal carousel"

  printf '\n%b\n' "${BOLD}${YELLOW}  SPECIAL TOOLS${RESET}"
  ui_line
  ui_item "06" "Extract Audio" "Konversi MP3 / WAV"
  ui_item "07" "Spotify / SpotDL" "Track / album / playlist"
  ui_item "08" "Carousel" "Gallery downloader untuk platform yang didukung"

  printf '\n%b\n' "${BOLD}${GREEN}  SYSTEM${RESET}"
  ui_line
  ui_item "09" "Dependency Check" "Periksa Termux, Debian, Chromium, Playwright, FFmpeg"

  printf '\n  %b[00]%b  Keluar\n' "${RED}${BOLD}" "$RESET"
  printf '\n%b' "${CYAN}${BOLD}  PILIH MODUL [00-09] > ${RESET}"
  IFS= read -r choice || exit 0

  case "$choice" in
    1|01) run_module youtube module_youtube ;;
    2|02) run_module instagram module_instagram ;;
    3|03) run_module facebook module_facebook ;;
    4|04) run_module tiktok module_tiktok ;;
    5|05) run_module threads module_threads ;;
    6|06) run_module audio module_audio ;;
    7|07) run_module spotify module_spotify ;;
    8|08) run_module carousel module_carousel ;;
    9|09) ui_header; ui_section "DEPENDENCY CHECK"; dependency_check; ui_pause ;;
    0|00) clear; printf '\n%b\n\n' "${GREEN}${BOLD}Sampai jumpa.${RESET}"; exit 0 ;;
    *) ui_error "Pilihan tidak valid."; sleep 1 ;;
  esac
done
