#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# Downverse installer untuk Termux
# ----------------------------------------------------------------------------
# Memasang semua dependency, menyiapkan Debian proot + Python venv,
# mendeteksi lokasi output, menulis konfigurasi, dan membuat shortcut.
#
# Pemakaian:
#   bash install.sh
#   bash install.sh --yes
#   bash install.sh --output /storage/XXXX-XXXX/output
#   bash install.sh --dry-run
# ============================================================================
set -Eeuo pipefail

readonly VERSION="2026.11.22"
BASE_DIR="$(cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")" && pwd)"
readonly BASE_DIR
export BASE_DIR
CONFIG="${DOWNVERSE_CONFIG:-$BASE_DIR/downloader/config.sh}"
readonly CONFIG
readonly MARKER="$HOME/.media-downloader-ready"

ASSUME_YES=0
DRY_RUN=0
OUTPUT_OVERRIDE=""

DISTRO=""
VENV=""

# ===== Colors =====
readonly C_RESET=$'\033[0m'
readonly C_BOLD=$'\033[1m'
readonly C_DIM=$'\033[2m'
readonly C_RED=$'\033[31m'
readonly C_GREEN=$'\033[32m'
readonly C_YELLOW=$'\033[33m'
readonly C_MAGENTA=$'\033[35m'
readonly C_CYAN=$'\033[36m'

trap 'printf "\n%b\n" "${C_RED}${C_BOLD}✖ Instalasi gagal di baris $LINENO.${C_RESET}" >&2' ERR

# ===== Helpers =====
log()     { printf '%b\n' "${C_CYAN}${C_BOLD}==>${C_RESET} $*"; }
ok()      { printf '%b\n' "${C_GREEN}${C_BOLD}✔${C_RESET} $*"; }
warn()    { printf '%b\n' "${C_YELLOW}${C_BOLD}⚠${C_RESET} $*"; }
die()     { printf '%b\n' "${C_RED}${C_BOLD}✖${C_RESET} $*" >&2; exit 1; }
section() { printf '\n%b\n' "${C_MAGENTA}${C_BOLD}━━ $* ━━${C_RESET}"; }

run() {
  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + $*${C_RESET}"
  else
    "$@"
  fi
}

confirm() {
  (( ASSUME_YES )) && return 0
  local reply
  printf '%b' "${C_YELLOW}?${C_RESET} $1 [Y/n] "
  read -r reply || true
  [[ -z "$reply" || "$reply" =~ ^[Yy]$ ]]
}

usage() {
  cat <<EOF
Downverse installer v$VERSION

Penggunaan:
  bash install.sh [opsi]

Opsi:
  -y, --yes          Jawab "ya" otomatis (non-interaktif)
      --output PATH  Tentukan folder output manual
      --dry-run      Tampilkan langkah tanpa mengubah sistem
  -h, --help         Tampilkan bantuan ini

Contoh:
  bash install.sh
  bash install.sh --yes
  bash install.sh --output /storage/7544-8C33/output
EOF
}

# ===== Validasi awal =====
require_termux() {
  [[ -n "${PREFIX:-}" && -d "${PREFIX:-}" ]] || die "Jalankan script ini di dalam Termux."
  [[ "${PREFIX}" == *com.termux* ]] || warn "PREFIX tidak terlihat seperti Termux: $PREFIX"
  command -v pkg >/dev/null 2>&1 || die "Perintah 'pkg' tidak ditemukan. Ini bukan Termux?"
  [[ -f "$BASE_DIR/downloader.sh" ]] || die "downloader.sh tidak ditemukan di $BASE_DIR"
  [[ -f "$CONFIG" ]] || die "downloader/config.sh tidak ditemukan. Pastikan repo di-clone lengkap."
}

# Baca nilai variabel dari config tanpa mengubah shell saat ini.
config_value() {
  local key="$1"
  bash -c '
    source "$1" >/dev/null 2>&1 || exit 1
    printf "%s" "${!2:-}"
  ' _ "$CONFIG" "$key" 2>/dev/null || true
}

# Escape karakter khusus untuk replacement sed.
sed_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//&/\\&}"
  s="${s//|/\\|}"
  printf '%s' "$s"
}

# Ganti satu baris konfigurasi: KEY="${KEY:-value}"
replace_config_line() {
  local key="$1" value="$2" escaped replacement
  escaped="$(sed_escape "$value")"
  replacement="${key}=\"\${${key}:-${escaped}}\""
  if grep -qE "^${key}=" "$CONFIG"; then
    sed -i -E "s|^${key}=.*$|${replacement}|" "$CONFIG"
  else
    printf '%s\n' "$replacement" >> "$CONFIG"
  fi
}

# ===== 0. Deteksi output =====
detect_output() {
  if [[ -n "$OUTPUT_OVERRIDE" ]]; then
    OUTPUT_ROOT="$OUTPUT_OVERRIDE"
    [[ "$OUTPUT_ROOT" == /* ]] || OUTPUT_ROOT="$PWD/$OUTPUT_ROOT"
    SDCARD_ROOT="$(dirname -- "$OUTPUT_ROOT")"
    return 0
  fi

  local cur_sd cur_out
  cur_sd="$(config_value SDCARD_ROOT)"
  cur_out="$(config_value OUTPUT_ROOT)"

  if [[ -n "$cur_sd" && -d "$cur_sd" && -w "$cur_sd" ]]; then
    SDCARD_ROOT="$cur_sd"
    OUTPUT_ROOT="${cur_out:-$cur_sd/output}"
    ok "Memakai konfigurasi yang sudah ada: $OUTPUT_ROOT"
    return 0
  fi

  local -a vols=()
  local d base
  for d in /storage/*; do
    [[ -d "$d" && -w "$d" ]] || continue
    base="$(basename -- "$d")"
    case "$base" in
      emulated|self) continue ;;
    esac
    [[ "$base" =~ ^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$ ]] || continue
    vols+=("$d")
  done

  if (( ${#vols[@]} == 0 )); then
    SDCARD_ROOT="/storage/emulated/0"
    OUTPUT_ROOT="/storage/emulated/0/Download/Downverse"
    warn "SD card eksternal tidak ditemukan. Memakai storage internal."
  elif (( ${#vols[@]} == 1 )) || (( ASSUME_YES )); then
    SDCARD_ROOT="${vols[0]}"
    OUTPUT_ROOT="$SDCARD_ROOT/output"
  else
    printf '\n%b\n' "${C_BOLD}Pilih lokasi output:${C_RESET}"
    local i
    for i in "${!vols[@]}"; do
      printf '  [%d] %s\n' "$((i + 1))" "${vols[$i]}"
    done
    local choice
    while true; do
      printf 'Pilihan [1-%d]: ' "${#vols[@]}"
      if ! read -r choice; then
        die "Input tidak tersedia. Gunakan --output PATH atau --yes."
      fi
      if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#vols[@]} )); then
        SDCARD_ROOT="${vols[$((choice - 1))]}"
        OUTPUT_ROOT="$SDCARD_ROOT/output"
        break
      fi
      warn "Pilihan tidak valid."
    done
  fi
}

# ===== 1. Paket Termux =====
install_termux_packages() {
  section "1/6 Paket Termux"
  run pkg update -y
  if confirm "Upgrade semua paket Termux? (disarankan)"; then
    run pkg upgrade -y
  fi
  run pkg install -y bash fish python proot-distro proot ffmpeg curl wget git termux-tools

  if (( ! DRY_RUN )); then
    command -v ffmpeg >/dev/null 2>&1 || die "FFmpeg tidak terpasang."
    ffmpeg -version >/dev/null 2>&1 || die "FFmpeg terpasang tetapi gagal dijalankan. Jalankan: pkg update && pkg upgrade -y"
    command -v proot-distro >/dev/null 2>&1 || die "proot-distro tidak terpasang."
  fi
  ok "Paket Termux siap."
}

# ===== 2. Izin storage =====
setup_storage() {
  section "2/6 Izin storage"
  if [[ -d "$HOME/storage/shared" ]]; then
    ok "Storage Termux sudah aktif."
    return 0
  fi

  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + termux-setup-storage${C_RESET}"
    return 0
  fi

  if command -v termux-setup-storage >/dev/null 2>&1; then
    log "Menampilkan dialog izin storage Android..."
    termux-setup-storage || warn "termux-setup-storage gagal atau dibatalkan."
    sleep 2
  else
    warn "termux-setup-storage tidak ditemukan."
  fi

  [[ -d "$HOME/storage/shared" ]] || warn "Folder ~/storage/shared belum ada. Pastikan izin storage diberikan."
}

# ===== 3. Debian + dependency =====
setup_debian() {
  section "3/6 Debian + dependency media"

  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + proot-distro install $DISTRO (jika belum ada)${C_RESET}"
  else
    if proot-distro login "$DISTRO" -- /bin/true >/dev/null 2>&1; then
      ok "Distro '$DISTRO' sudah terpasang."
    else
      log "Menginstal Debian (pertama kali, butuh waktu)..."
      run proot-distro install "$DISTRO"
    fi
  fi

  run proot-distro login "$DISTRO" -- bash -lc \
    'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl wget ffmpeg python3 python3-venv python3-pip chromium fonts-liberation'

  ok "Dependency Debian siap."
}

# ===== 4. Python venv =====
setup_venv() {
  section "4/6 Python venv + tool downloader"

  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + python3 -m venv $VENV (jika belum ada)${C_RESET}"
  else
    if ! proot-distro login "$DISTRO" -- test -x "$VENV/bin/python" >/dev/null 2>&1; then
      log "Membuat Python venv di $VENV..."
      run proot-distro login "$DISTRO" -- python3 -m venv "$VENV"
    fi
  fi

  run proot-distro login "$DISTRO" -- "$VENV/bin/pip" install -U \
    pip setuptools wheel yt-dlp gallery-dl spotdl playwright requests

  if (( ! DRY_RUN )); then
    proot-distro login "$DISTRO" -- "$VENV/bin/yt-dlp" --version >/dev/null 2>&1 \
      || die "yt-dlp gagal dijalankan di venv."
    proot-distro login "$DISTRO" -- "$VENV/bin/python" -c 'import playwright' >/dev/null 2>&1 \
      || die "Playwright gagal diimpor di venv."
  fi
  ok "Venv siap: $VENV"
}

# ===== 5. Output + konfigurasi + shortcut =====
prepare_dirs() {
  section "5/6 Output, konfigurasi, shortcut"

  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + mkdir -p $OUTPUT_ROOT $HOME/cookies $BASE_DIR/downloader/logs${C_RESET}"
  else
    mkdir -p "$OUTPUT_ROOT" "$HOME/cookies" "$BASE_DIR/downloader/logs"
    [[ -d "$OUTPUT_ROOT" && -w "$OUTPUT_ROOT" ]] || die "Folder output tidak bisa ditulis: $OUTPUT_ROOT"

    local probe="$OUTPUT_ROOT/.downverse-write-test.$$"
    : > "$probe" || die "Gagal menulis ke $OUTPUT_ROOT"
    rm -f "$probe"
    ok "Output siap: $OUTPUT_ROOT"
  fi
}

write_config() {
  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + tulis konfigurasi ke $CONFIG${C_RESET}"
    printf '%b\n' "${C_DIM}    SDCARD_ROOT=$SDCARD_ROOT${C_RESET}"
    printf '%b\n' "${C_DIM}    OUTPUT_ROOT=$OUTPUT_ROOT${C_RESET}"
    printf '%b\n' "${C_DIM}    INSTALLER=\$BASE_DIR/install.sh${C_RESET}"
    return 0
  fi

  # Hapus blok override lama (jika ada).
  sed -i '/^# >>> downverse-install >>>$/,/^# <<< downverse-install <<<$/d' "$CONFIG"

  replace_config_line PROOT_DISTRO "$DISTRO"
  replace_config_line PROOT_VENV "$VENV"
  replace_config_line SDCARD_ROOT "$SDCARD_ROOT"
  replace_config_line OUTPUT_ROOT "$OUTPUT_ROOT"
  replace_config_line INSTALLER '$BASE_DIR/install.sh'

  ok "Konfigurasi ditulis: $CONFIG"
}

create_shortcut() {
  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + ln -sf $BASE_DIR/downloader.sh $PREFIX/bin/downverse${C_RESET}"
    return 0
  fi

  chmod +x "$BASE_DIR/downloader.sh" "$BASE_DIR/install.sh"
  mkdir -p "$PREFIX/bin"
  ln -sf "$BASE_DIR/downloader.sh" "$PREFIX/bin/downverse"
  ok "Shortcut dibuat: downverse"
}

# ===== 6. Validasi =====
validate_install() {
  section "6/6 Validasi"

  if (( DRY_RUN )); then
    printf '%b\n' "${C_DIM}  + validasi yt-dlp, FFmpeg, dan bind mount output${C_RESET}"
    return 0
  fi

  proot-distro login "$DISTRO" -- test -x "$VENV/bin/yt-dlp" \
    || die "yt-dlp tidak ditemukan di $VENV."
  proot-distro login "$DISTRO" -- "$VENV/bin/yt-dlp" --version >/dev/null \
    || die "yt-dlp gagal dijalankan."
  proot-distro login "$DISTRO" -- ffmpeg -version >/dev/null \
    || die "FFmpeg Debian gagal dijalankan."

  local host_id guest_id
  host_id="$(stat -c '%d:%i' "$OUTPUT_ROOT")" || die "Tidak bisa membaca folder output."
  guest_id="$(proot-distro login --bind "$OUTPUT_ROOT:$OUTPUT_ROOT" "$DISTRO" -- stat -c '%d:%i' "$OUTPUT_ROOT" 2>/dev/null || true)"
  [[ -n "$guest_id" && "$host_id" == "$guest_id" ]] \
    || die "Bind mount output gagal (host=$host_id, guest=${guest_id:-?}). Pastikan path output sama dan tidak memakai mode isolated."

  ok "Bind mount output terverifikasi."
}

# ===== Ringkasan =====
print_summary() {
  printf '\n%b\n' "${C_GREEN}${C_BOLD}🎉 Downverse siap dipakai!${C_RESET}"
  cat <<EOF

  Project : $BASE_DIR
  Output  : $OUTPUT_ROOT
  Debian  : $DISTRO
  Venv    : $VENV
  Cookies : $HOME/cookies
  Marker  : $MARKER

  Jalankan:
    downverse
    # atau
    bash $BASE_DIR/downloader.sh

  Cek dependency:
    bash $BASE_DIR/downloader.sh --check

  Panduan lengkap:
    $BASE_DIR/INSTALL.md
EOF
  if (( DRY_RUN )); then
    printf '\n%b\n' "${C_YELLOW}Mode dry-run: tidak ada perubahan yang dilakukan.${C_RESET}"
  fi
}

# ===== Main =====
main() {
  while (( $# )); do
    case "$1" in
      -y|--yes)   ASSUME_YES=1 ;;
      --output)
        [[ $# -ge 2 ]] || die "--output membutuhkan path."
        OUTPUT_OVERRIDE="$2"
        shift
        ;;
      --dry-run)  DRY_RUN=1; ASSUME_YES=1 ;;
      -h|--help)  usage; exit 0 ;;
      *)          die "Opsi tidak dikenal: $1 (lihat --help)" ;;
    esac
    shift
  done

  require_termux

  # Pertahankan nilai dari config lama kecuali di-override lewat environment.
  DISTRO="${PROOT_DISTRO:-$(config_value PROOT_DISTRO)}"
  DISTRO="${DISTRO:-debian}"
  VENV="${PROOT_VENV:-$(config_value PROOT_VENV)}"
  VENV="${VENV:-/opt/media-downloader-venv}"

  printf '%b\n' "${C_MAGENTA}${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
  printf '%b\n' "${C_MAGENTA}${C_BOLD}  🌌 DOWNVERSE INSTALLER v$VERSION${C_RESET}"
  printf '%b\n' "${C_MAGENTA}${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"

  if (( ! DRY_RUN )); then
    rm -f "$MARKER"
  fi

  detect_output
  install_termux_packages
  setup_storage
  setup_debian
  setup_venv
  prepare_dirs
  write_config
  create_shortcut
  validate_install

  if (( ! DRY_RUN )); then
    printf 'ready\n' > "$MARKER"
    chmod 600 "$MARKER" 2>/dev/null || true
    if bash "$BASE_DIR/downloader.sh" --check >/dev/null 2>&1; then
      ok "Launcher siap."
    else
      warn "Launcher --check gagal. Jalankan: bash $BASE_DIR/downloader.sh --check"
    fi
  fi

  print_summary
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
