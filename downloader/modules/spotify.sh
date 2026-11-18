module_spotify() {
  ui_header; ui_section "SPOTIFY / SPOTDL"
  printf '1) Track\n2) Album\n3) Playlist\n0) Kembali\nPilih: '; IFS= read -r x
  [[ "$x" == "0" ]] && return 0
  case "$x" in 1|2|3) ;; *) ui_error "Pilihan tidak valid."; ui_pause; return 1 ;; esac
  ask_url "Spotify URL" || { ui_pause; return 1; }
  check_host || { ui_pause; return 1; }
  proot_require || { ui_pause; return 1; }
  if ! proot_login test -x "$SPOTDL_BIN"; then ui_error "spotdl belum tersedia di Debian. Jalankan fish ~/install.fish."; ui_pause; return 1; fi
  run_spotdl download "$URL" --output "$OUTPUT_ROOT/Spotify/{artist} - {title}.{output-ext}"
  local rc=$?; if [[ $rc -eq 0 ]]; then ui_ok "Spotify selesai."; else ui_error "Spotify gagal (exit $rc)."; fi
  ui_pause; return "$rc"
}
