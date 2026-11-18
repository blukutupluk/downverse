# UI Bash: ASCII-safe agar stabil di font Termux.
RESET="${RESET:-\033[0m}"
BOLD="${BOLD:-\033[1m}"
DIM="${DIM:-\033[2m}"
CYAN="${CYAN:-\033[1;36m}"
BLUE="${BLUE:-\033[1;34m}"
GREEN="${GREEN:-\033[1;32m}"
YELLOW="${YELLOW:-\033[1;33m}"
RED="${RED:-\033[1;31m}"
MAGENTA="${MAGENTA:-\033[1;35m}"
WHITE="${WHITE:-\033[1;37m}"

ui_header() {
  printf '\n%b\n' "${CYAN}${BOLD}  TERMUX MEDIA DOWNLOADER${RESET}"
  printf '%b\n' "${DIM}  Termux launcher / Debian Proot backend${RESET}"
  printf '%b\n' "${BLUE}  ----------------------------------------${RESET}"
}
ui_section() { printf '\n%b\n' "${YELLOW}${BOLD}  [$1]${RESET}"; }
ui_line() { printf '%b\n' "${BLUE}  ----------------------------------------${RESET}"; }
ui_item() {
  local n="$1" title="$2" desc="$3"
  printf '  %b[%s]%b  %b%s%b\n' "${CYAN}${BOLD}" "$n" "$RESET" "${WHITE}${BOLD}" "$title" "$RESET"
  printf '       %b%s%b\n' "$DIM" "$desc" "$RESET"
}
ui_error() { printf '\n%b\n' "${RED}${BOLD}ERROR: $*${RESET}" >&2; }
ui_warn() { printf '\n%b\n' "${YELLOW}PERINGATAN: $*${RESET}"; }
ui_ok() { printf '%b\n' "${GREEN}OK: $*${RESET}"; }
ui_pause() { printf '\n%b' "${DIM}Tekan Enter untuk kembali...${RESET}"; IFS= read -r _pause_value; }
