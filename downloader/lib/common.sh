ensure_system_dirs() {
  mkdir -p "$OUTPUT_ROOT" "$LOG_DIR" "$COOKIE_DIR" \
    "$OUTPUT_ROOT/YouTube" "$OUTPUT_ROOT/Instagram" "$OUTPUT_ROOT/Facebook" \
    "$OUTPUT_ROOT/TikTok" "$OUTPUT_ROOT/Threads" "$OUTPUT_ROOT/Audio/MP3" \
    "$OUTPUT_ROOT/Audio/WAV" "$OUTPUT_ROOT/Spotify" "$OUTPUT_ROOT/Carousel" \
    "$OUTPUT_ROOT/WebScraper"
}

ask_url() {
  local prompt="${1:-URL}"
  printf '%b' "${CYAN}${BOLD}${prompt}: ${RESET}"
  IFS= read -r URL
  if [[ -z "$URL" ]]; then ui_error "URL kosong."; return 1; fi
  case "$URL" in http://*|https://*) ;; *) ui_error "URL harus diawali http:// atau https://"; return 1 ;; esac
  return 0
}

check_host() {
  [[ "$URL" =~ ^https?://[^/]+ ]] || { ui_error "URL tidak valid."; return 1; }
  return 0
}

# Facebook terkadang mengubah struktur payload videonya sampai yt-dlp gagal
# ("Cannot parse data"), padahal URL MP4-nya masih ada di halaman. Ambil URL itu
# sebagai fallback lalu serahkan tetap ke yt-dlp untuk download/konversi.
resolve_facebook_direct_url() {
  local url="$1" cookie="$2"
  local helper="$BASE_DIR/downloader/backend/facebook_direct_url.py"
  [[ -f "$helper" ]] || return 1
  proot_require || return $?

  local cookie_dir
  cookie_dir="$(dirname -- "$cookie")"
  local -a binds=()
  [[ -d "$cookie_dir" ]] && binds+=(--bind "$cookie_dir:$cookie_dir")
  [[ -d "$BASE_DIR" ]] && binds+=(--bind "$BASE_DIR:$BASE_DIR")

  local out direct vid
  if ! out="$(proot-distro login "${binds[@]}" "$PROOT_DISTRO" -- \
      "$PROOT_VENV/bin/python" "$helper" "$url" "$cookie" 2>>"$LOG_DIR/facebook-direct.log")"; then
    return 1
  fi
  if [[ "$out" == *$'\n'* ]]; then
    direct="${out%%$'\n'*}"
    vid="${out#*$'\n'}"
  else
    direct="$out"
    vid=""
  fi
  [[ "$direct" == http://* || "$direct" == https://* ]] || return 1
  vid="${vid//[^0-9A-Za-z_-]/}"
  vid="${vid:0:64}"
  [[ -n "$vid" ]] || vid="video"
  printf '%s\n%s\n' "$direct" "$vid"
}

run_ytdlp() {
  local label="$1" cookie="$2"
  shift 2
  local url="${@: -1}"
  local -a cmd=("$YTDLP_BIN" --newline --ignore-errors --retries 3 --fragment-retries 3 --socket-timeout 30)
  if [[ -n "$cookie" && -f "$cookie" ]]; then cmd+=(--cookies "$cookie"); fi
  cmd+=("$@")
  log_info "yt-dlp start label=$label"
  local rc=0
  if proot_run "${cmd[@]}"; then rc=0; else rc=$?; fi

  if [[ $rc -ne 0 && "$label" == "Facebook" ]]; then
    local resolved direct vid
    if resolved="$(resolve_facebook_direct_url "$url" "$cookie")"; then
      direct="${resolved%%$'\n'*}"
      vid="${resolved#*$'\n'}"
      ui_warn "yt-dlp gagal parse Facebook. Mencoba URL langsung dari halaman..."
      log_info "facebook direct fallback: ${direct:0:120} id=$vid"
      cmd[-1]="$direct"

      # URL CDN jauh lebih panjang dari batas nama file. Karena yt-dlp generic
      # memakai URL sebagai %(title)s dan %(id)s, ganti template -o supaya
      # memakai ID numerik Facebook yang pendek.
      local i=0 template="" dir=""
      while (( i < ${#cmd[@]} )); do
        if [[ "${cmd[$i]}" == "-o" || "${cmd[$i]}" == "--output" ]]; then
          template="${cmd[$((i + 1))]}"
          if [[ "$template" == */* ]]; then dir="${template%/*}"; else dir="."; fi
          cmd[$((i + 1))]="$dir/facebook_${vid}.%(ext)s"
          break
        fi
        i=$((i + 1))
      done
      if [[ -z "$dir" ]]; then
        dir="$OUTPUT_ROOT/Facebook"
        mkdir -p "$dir"
        cmd+=(-o "$dir/facebook_${vid}.%(ext)s")
      fi

      if proot_run "${cmd[@]}"; then rc=0; else rc=$?; fi
    else
      log_error "facebook direct fallback gagal (lihat logs/facebook-direct.log)"
    fi
  fi

  if [[ $rc -eq 0 ]]; then log_info "yt-dlp success label=$label"; else log_error "yt-dlp failed label=$label rc=$rc"; fi
  return "$rc"
}

run_spotdl() {
  proot_run "$SPOTDL_BIN" "$@"
}

run_gallerydl() {
  local label="$1" cookie="$2"
  shift 2
  local -a cmd=("$GALLERYDL_BIN" --retries 3 --http-timeout 30)
  if [[ -n "$cookie" && -f "$cookie" ]]; then cmd+=(--cookies "$cookie"); fi
  cmd+=("$@")
  log_info "gallery-dl start label=$label"
  proot_run "${cmd[@]}"
  local rc=$?
  if [[ $rc -eq 0 ]]; then log_info "gallery-dl success label=$label"; else log_error "gallery-dl failed label=$label rc=$rc"; fi
  return "$rc"
}

platform_download() {
  local label="$1" out="$2" cookie="$3" playlist="${4:-no}"
  local choice="1" url
  mkdir -p "$out"
  ui_header; ui_section "$label"
  ask_url "$label URL" || { ui_pause; return 1; }
  check_host || { ui_pause; return 1; }
  printf '\n%s\n' '1) Video MP4 (best available)' '2) Audio MP3' '3) Original / best format' '0) Kembali'
  printf 'Pilih format: '; IFS= read -r choice
  [[ "$choice" == "0" ]] && return 0
  local -a opts=(-o "$out/%(title).150B [%(id)s].%(ext)s")
  if [[ "$playlist" == "yes" ]]; then opts+=(--yes-playlist); else opts+=(--no-playlist); fi
  case "$choice" in
    1) opts+=(-f 'bv*+ba/b' --merge-output-format mp4) ;;
    2) opts+=(-x --audio-format mp3 --audio-quality 0) ;;
    3) opts+=(-f 'best/b') ;;
    *) ui_error "Pilihan format tidak valid."; ui_pause; return 1 ;;
  esac
  printf '\n%b\n' "${DIM}Backend: Debian / yt-dlp${RESET}"
  run_ytdlp "$label" "$cookie" "${opts[@]}" "$URL"
  local rc=$?
  if [[ $rc -eq 0 ]]; then ui_ok "Download selesai: $out"; else ui_error "Download gagal (exit $rc). Periksa logs/downloader.log."; fi
  ui_pause
  return "$rc"
}
