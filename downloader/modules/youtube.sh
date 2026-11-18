module_youtube() {
  while true; do
    ui_header; ui_section "YOUTUBE"
    ui_item "1" "Single Video" "Satu URL"
    ui_item "2" "Playlist" "Semua item playlist"
    ui_item "0" "Kembali" ""
    printf '\nPilih: '; IFS= read -r x
    case "$x" in
      1) platform_download "YouTube" "$OUTPUT_ROOT/YouTube" "$YOUTUBE_COOKIE" no; return ;;
      2) platform_download "YouTube Playlist" "$OUTPUT_ROOT/YouTube" "$YOUTUBE_COOKIE" yes; return ;;
      0) return 0 ;;
      *) ui_error "Pilihan tidak valid."; sleep 1 ;;
    esac
  done
}
