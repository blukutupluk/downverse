#!/data/data/com.termux/files/usr/bin/bash
# Termux Media Downloader - launcher utama.
set -euo pipefail
BASE_DIR="$(cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")" && pwd)"
readonly BASE_DIR VERSION="2026.11.21"

# ===== Colors =====
readonly C_RESET='\033[0m'
readonly C_BOLD='\033[1m'
readonly C_DIM='\033[2m'
readonly C_RED='\033[31m'
readonly C_GREEN='\033[32m'
readonly C_YELLOW='\033[33m'
readonly C_BLUE='\033[34m'
readonly C_MAGENTA='\033[35m'
readonly C_CYAN='\033[36m'
readonly C_WHITE='\033[37m'
readonly C_GRAY='\033[90m'

# ===== Load libraries =====
for _lib in config.sh lib/ui.sh lib/logging.sh lib/proot.sh lib/common.sh lib/checks.sh; do
  [[ -f "$BASE_DIR/downloader/$_lib" ]] || { echo -e "${C_RED}${C_BOLD}FATAL:${C_RESET} Library hilang: $_lib" >&2; exit 78; }
  # shellcheck source=/dev/null
  source "$BASE_DIR/downloader/$_lib"
done

# ===== Validate critical config =====
: "${INSTALLER:?}" "${SDCARD_ROOT:?}" "${OUTPUT_ROOT:?}" "${PROOT_DISTRO:?}" "${PROOT_VENV:?}"
[[ -f "$INSTALLER" ]] || { echo -e "${C_RED}${C_BOLD}FATAL:${C_RESET} Installer tidak ditemukan: $INSTALLER" >&2; exit 78; }

# ===== Startup dependency check =====
for cmd in proot-distro ffmpeg ffprobe python3 git; do
  command -v "$cmd" >/dev/null 2>&1 || { echo -e "${C_RED}DEPENDENSI HILANG:${C_RESET} $cmd" >&2; exit 1; }
done

# ===== Trap cleanup =====
CHILD_PIDS=()
trap 'for p in "${CHILD_PIDS[@]}"; do kill -TERM "$p" 2>/dev/null; done; wait 2>/dev/null; exit 130' INT TERM

# ===== Ready flag =====
[[ -f "$HOME/.media-downloader-ready" ]] || {
  echo -e "\n${C_RED}${C_BOLD}SETUP BELUM SELESAI${C_RESET}"
  echo -e "Jalankan: ${C_CYAN}fish $INSTALLER${C_RESET}"
  exit 78
}

# ===== Module runner =====
run_module() {
  local m="${1:-}" f="${2:-}" p
  p="$BASE_DIR/downloader/modules/$m.sh"
  [[ -n "$m" && -n "$f" ]] || { ui_error "Modul tidak valid."; sleep 2; return 1; }
  [[ -f "$p" ]] || { ui_error "Modul tidak ditemukan: $p"; sleep 2; return 1; }
  source "$p"
  declare -F "$f" >/dev/null 2>&1 || { ui_error "Fungsi $f tidak ada di $m.sh"; sleep 2; return 1; }
  "$f"
}

# ===== CLI flags =====
if [[ "${1:-}" == "--check" ]]; then
  echo -e "${C_CYAN}Termux Media Downloader v$VERSION${C_RESET}"
  echo -e "${C_GREEN}OK:${C_RESET} config & dependencies"
  exit 0
fi
if [[ "${1:-}" == "--version" ]]; then
  echo "v$VERSION"
  exit 0
fi

# ===== Menu data: id|module|function|name|description|icon =====
MENU_ITEMS=(
  "1|youtube|module_youtube|YouTube|Video tunggal & playlist|▶"
  "2|instagram|module_instagram|Instagram|Video / audio / post|📷"
  "3|facebook|module_facebook|Facebook|Video / audio / post|📘"
  "4|tiktok|module_tiktok|TikTok|Video & media|🎵"
  "5|threads|module_threads|Threads|Video saja|🧵"
  "6|spotify|module_spotify|Spotify / SpotDL|Track / album / playlist|🎵"
  "7|carousel|module_carousel|Carousel|Gallery downloader|🖼"
  "8|audio|module_audio|Extract Audio|Konversi MP3 / WAV|🎧"
  "9|video_splitter|module_video_splitter|Video Splitter 10s|Klip 10 detik|✂"
  "10|bulk|module_bulk|Download Massal|Banyak URL dari .txt|📦"
  "11|audio_extractor|module_audio_extractor|Audio Extractor + Transcriber|MP3 + TXT dari video|🎙"
  "12|web_scraper|module_web_scraper|Web Scraper / Downloader|Scrape video dari situs bandel|🌐"
)

# ===== Helpers =====
print_header() {
  clear
  local w=52
  local title=" TERMUX MEDIA DOWNLOADER v$VERSION "
  local pad=$(( (w - ${#title}) / 2 ))
  printf '%b\n' "${C_MAGENTA}${C_BOLD}╔$(printf '═%.0s' $(seq 1 $w))╗${C_RESET}"
  printf '%b' "${C_MAGENTA}${C_BOLD}║${C_RESET}"
  printf '%*s' $pad ""
  printf '%b' "${C_WHITE}${C_BOLD}$title${C_RESET}"
  printf '%*s' $((w - pad - ${#title})) ""
  printf '%b\n' "${C_MAGENTA}${C_BOLD}║${C_RESET}"
  printf '%b\n' "${C_MAGENTA}${C_BOLD}╚$(printf '═%.0s' $(seq 1 $w))╝${C_RESET}"
  echo
}

print_section() {
  local title="$1" color="$2"
  echo -e "${color}${C_BOLD}  $title${C_RESET}"
  echo -e "${C_GRAY}  $(printf '─%.0s' $(seq 1 50))${C_RESET}"
}

print_item() {
  local num="$1" name="$2" desc="$3" icon="$4"
  printf '  %b[%2s]%b %s %-28s %b%s%b\n' \
    "${C_CYAN}${C_BOLD}" "$num" "${C_RESET}" \
    "$icon" "$name" \
    "${C_GRAY}" "$desc" "${C_RESET}"
}

# ===== Main loop =====
while true; do
  print_header

  print_section "DOWNLOAD MEDIA" "${C_BLUE}"
  for item in "${MENU_ITEMS[@]}"; do
    IFS='|' read -r id mod fn name desc icon <<<"$item"
    [[ "$id" =~ ^[1-7]$ ]] && print_item "$id" "$name" "$desc" "$icon"
  done
  echo

  print_section "SPECIAL TOOLS" "${C_YELLOW}"
  for item in "${MENU_ITEMS[@]}"; do
    IFS='|' read -r id mod fn name desc icon <<<"$item"
    [[ "$id" =~ ^(8|9|10|11|12)$ ]] && print_item "$id" "$name" "$desc" "$icon"
  done
  echo

  print_section "SYSTEM" "${C_GREEN}"
  echo -e "  ${C_YELLOW}${C_BOLD}[⭐]${C_RESET}  🔧 Dependency Check"
  echo

  echo -e "  ${C_RED}${C_BOLD}[00]${C_RESET}  Keluar"
  echo
  echo -ne "${C_MAGENTA}${C_BOLD}  PILIH [00-12,⭐] > ${C_RESET}"
  IFS= read -r choice || exit 0

  case "$choice" in
    0|00)
      clear
      echo -e "\n${C_GREEN}${C_BOLD}Sampai jumpa.${C_RESET}\n"
      exit 0
      ;;
    ⭐|star|dep)
      ui_header
      ui_section "DEPENDENCY CHECK"
      dependency_check
      ui_pause
      ;;
    1|2|3|4|5|6|7|8|9|10|11|12)
      for item in "${MENU_ITEMS[@]}"; do
        IFS='|' read -r id mod fn name desc icon <<<"$item"
        if [[ "$id" == "$choice" ]]; then
          run_module "$mod" "$fn"
          break
        fi
      done
      ;;
    *)
      ui_error "Pilihan tidak valid: $choice"
      sleep 1
      ;;
  esac
done