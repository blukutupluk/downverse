module_audio() {
  ui_header; ui_section "EXTRACT AUDIO"
  ask_url "Media URL" || { ui_pause; return 1; }
  printf '\n1) MP3\n2) WAV\n0) Kembali\nPilih: '; IFS= read -r x
  case "$x" in
    1) run_ytdlp "Extract Audio" "" -x --audio-format mp3 --audio-quality 0 -o "$OUTPUT_ROOT/Audio/MP3/%(title).150B [%(id)s].%(ext)s" "$URL" ;;
    2) run_ytdlp "Extract Audio" "" -x --audio-format wav -o "$OUTPUT_ROOT/Audio/WAV/%(title).150B [%(id)s].%(ext)s" "$URL" ;;
    0) return 0 ;;
    *) ui_error "Pilihan tidak valid."; ui_pause; return 1 ;;
  esac
  local rc=$?; ui_pause; return "$rc"
}
