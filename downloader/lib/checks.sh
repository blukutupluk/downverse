dependency_check() {
  local bad=0 host_proot=0 debian_ready=0
  printf '%b\n' "${BOLD}TERMUX HOST${RESET}"
  for c in bash fish proot-distro proot curl python; do
    if command -v "$c" >/dev/null 2>&1; then printf '  [OK] %-14s %s\n' "$c" "$(command -v "$c")"; else printf '  [MISSING] %s\n' "$c"; bad=1; fi
  done
  for c in ffmpeg ffprobe; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -version >/dev/null 2>&1; then
      printf '  [OK] %-14s %s (runtime OK)\n' "$c" "$(command -v "$c")"
    else
      printf '  [BROKEN/MISSING] %s (binary tidak bisa dieksekusi)\n' "$c"
      bad=1
    fi
  done
  if command -v proot-distro >/dev/null 2>&1; then host_proot=1; fi
  if [[ -d "$OUTPUT_ROOT" && -w "$OUTPUT_ROOT" ]]; then printf '  [OK] Output writable: %s\n' "$OUTPUT_ROOT"; else printf '  [WARN] Output tidak bisa ditulis: %s\n' "$OUTPUT_ROOT"; bad=1; fi

  printf '\n%b\n' "${BOLD}DEBIAN / PROOT${RESET}"
  if [[ $host_proot -eq 1 ]] && proot_require; then
    debian_ready=1
    printf '  [OK] Debian tersedia + bind SD card cocok\n'
    printf '  [OK] Filesystem output: %s\n' "$OUTPUT_ROOT"
  else
    printf '  [MISSING] Debian belum siap atau bind SD card tidak cocok\n'
    printf '  [FIX] Periksa akses SD card; jalankan: fish ~/install.fish\n'
    bad=1
  fi
  if [[ $debian_ready -eq 1 ]]; then
    if proot_login "$PROOT_PYTHON" -c 'import playwright; print("Playwright installed")' >/dev/null 2>&1; then printf '  [OK] Python + Playwright\n'; else printf '  [MISSING] Python / Playwright venv\n'; bad=1; fi
    for bin in chromium yt-dlp gallery-dl spotdl ffmpeg; do
      if proot_login bash -lc "command -v '$bin' >/dev/null 2>&1 || test -x '$PROOT_VENV/bin/$bin'" >/dev/null 2>&1; then printf '  [OK] %s\n' "$bin"; else printf '  [MISSING] %s\n' "$bin"; bad=1; fi
    done
  else
    printf '  [SKIP] Pemeriksaan software Debian karena distro belum aktif.\n'
  fi
  if [[ -f "$THREADS_COOKIE" ]]; then printf '  [OK] Threads cookie file exists (contents not inspected)\n'; else printf '  [WARN] Cookie belum ada: %s\n' "$THREADS_COOKIE"; fi
  printf '\n'
  if [[ $bad -eq 0 ]]; then ui_ok "Pondasi utama terdeteksi."; else ui_warn "Ada dependency/path yang belum siap."; fi
}
