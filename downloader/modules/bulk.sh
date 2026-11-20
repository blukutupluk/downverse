#!/data/data/com.termux/files/usr/bin/bash
# Download Massal: membaca daftar URL (satu per baris) dari file .txt lalu
# mengunduh semuanya lewat run_ytdlp. Hasil sukses dicatat di <daftar>.done
# supaya menjalankan ulang bisa melewati URL yang sudah berhasil.

bulk_parse_list() {
  local file="$1" line
  local -A seen=()

  [[ -f "$file" && -r "$file" ]] || return 1

  while IFS= read -r line || [[ -n "$line" ]]; do
    # Buang spasi di ujung/kiri supaya baris dengan indentasi tetap terbaca.
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    case "$line" in
      http://*|https://*) ;;
      *) continue ;;
    esac
    [[ -n "${seen[$line]:-}" ]] && continue
    seen["$line"]=1
    printf '%s\n' "$line"
  done < "$file"
  return 0
}

bulk_run() {
  local label="$1" out="$2" cookie="$3" format="$4" list="$5"
  local done_file="$list.done" url rc
  local total=0 berhasil=0 gagal=0 dilewati=0
  local -A done_map=()
  local -a opts=() failed_urls=()

  mkdir -p "$out"

  # Opsi identik dengan platform_download, hanya playlist yang selalu dimatikan.
  opts=(-o "$out/%(title).150B [%(id)s].%(ext)s" --no-playlist)
  case "$format" in
    1) opts+=(-f 'bv*+ba/b' --merge-output-format mp4) ;;
    2) opts+=(-x --audio-format mp3 --audio-quality 0) ;;
    3) opts+=(-f 'best/b') ;;
    *) ui_error "Format tidak valid: $format"; return 2 ;;
  esac

  if [[ -f "$done_file" ]]; then
    while IFS= read -r url || [[ -n "$url" ]]; do
      [[ -z "$url" ]] && continue
      done_map["$url"]=1
    done < "$done_file"
  fi

  # Process substitution (bukan pipe) agar counter tetap di shell ini.
  while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    total=$((total + 1))
    if [[ -n "${done_map[$url]:-}" ]]; then
      dilewati=$((dilewati + 1))
      continue
    fi
    run_ytdlp "$label" "$cookie" "${opts[@]}" "$url"
    rc=$?
    if ((rc == 0)); then
      printf '%s\n' "$url" >> "$done_file"
      done_map["$url"]=1
      berhasil=$((berhasil + 1))
    else
      gagal=$((gagal + 1))
      failed_urls+=("$url")
    fi
  done < <(bulk_parse_list "$list")

  if ((total == 0)); then
    ui_error "Tidak ada URL valid di daftar: $list"
    return 1
  fi

  printf '\n%s\n' "TOTAL=$total BERHASIL=$berhasil GAGAL=$gagal DILEWATI=$dilewati"
  local i=0
  for url in "${failed_urls[@]}"; do
    ((i >= 10)) && break
    printf 'GAGAL_URL=%s\n' "$url"
    i=$((i + 1))
  done

  ((gagal == 0)) && return 0
  return 1
}

module_bulk() {
  local label out cookie platform list format rc

  ui_header
  ui_section "DOWNLOAD MASSAL"
  ui_item "1" "Facebook" "Daftar URL reel/post Facebook"
  ui_item "2" "Instagram" "Daftar URL Instagram"
  ui_item "3" "YouTube" "Daftar URL YouTube"
  ui_item "4" "TikTok" "Daftar URL TikTok"
  ui_item "0" "Kembali" ""
  printf '\nPilih platform: '
  IFS= read -r platform
  case "$platform" in
    1) label="Facebook"; out="$OUTPUT_ROOT/Facebook"; cookie="$FACEBOOK_COOKIE" ;;
    2) label="Instagram"; out="$OUTPUT_ROOT/Instagram"; cookie="$INSTAGRAM_COOKIE" ;;
    3) label="YouTube"; out="$OUTPUT_ROOT/YouTube"; cookie="$YOUTUBE_COOKIE" ;;
    4) label="TikTok"; out="$OUTPUT_ROOT/TikTok"; cookie="" ;;
    0) return 0 ;;
    *) ui_error "Pilihan platform tidak valid."; ui_pause; return 1 ;;
  esac

  printf '%b' "${CYAN}${BOLD}Path file daftar URL (.txt): ${RESET}"
  IFS= read -r list
  if [[ -z "$list" || ! -f "$list" || ! -r "$list" || ! -s "$list" ]]; then
    ui_error "File daftar tidak valid atau kosong: $list"
    ui_pause
    return 1
  fi

  printf '\n%s\n' \
    '1) Video MP4 (best available)' \
    '2) Audio MP3' \
    '3) Original / best format' \
    '0) Kembali'
  printf 'Pilih format: '
  IFS= read -r format
  [[ "$format" == "0" ]] && return 0

  bulk_run "$label" "$out" "$cookie" "$format" "$list"
  rc=$?
  log_info "Bulk $label list=$list rc=$rc"
  ui_pause
  return "$rc"
}
