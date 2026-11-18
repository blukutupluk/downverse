module_carousel(){
  ui_header
  ui_section 'CAROUSEL / GALERI'
  printf '1) Instagram\n2) Facebook\n3) TikTok\n0) Kembali\nPilih: '
  IFS= read -r x
  case "$x" in
    1) local label=Instagram cookie="$INSTAGRAM_COOKIE" folder=Instagram ;;
    2) local label=Facebook cookie="$FACEBOOK_COOKIE" folder=Facebook ;;
    3) local label=TikTok cookie='' folder=TikTok ;;
    0) return 0 ;;
    *) ui_error 'Pilihan tidak valid'; ui_pause; return 1 ;;
  esac
  ask_url "$label Carousel URL" || { ui_pause; return 1; }
  mkdir -p "$OUTPUT_ROOT/Carousel/$folder"
  run_gallerydl "$label Carousel" "$cookie" -D "$OUTPUT_ROOT/Carousel/$folder" "$URL"
  local rc=$?
  if ((rc==0)); then
    ui_ok "Carousel tersimpan: $OUTPUT_ROOT/Carousel/$folder"
  else
    ui_error "gallery-dl gagal (exit $rc). Periksa URL, cookies, dan log."
  fi
  ui_pause
  return "$rc"
}
