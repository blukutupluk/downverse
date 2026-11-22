# Video Splitter 10 Seconds - modul baru.
# Memecah video menjadi klip 10 detik tanpa audio.
# Input:  /storage/7544-8C33/output/input/
# Output: /storage/7544-8C33/output/audio/

module_video_splitter() {
  ui_header; ui_section "VIDEO SPLITTER 10 DETIK"

  local INPUT_DIR="/storage/7544-8C33/output/input"
  local OUTPUT_DIR="/storage/7544-8C33/output/audio"

  # Buat folder jika belum ada
  if ! mkdir -p "$INPUT_DIR" "$OUTPUT_DIR" 2>/dev/null; then
    ui_error "Gagal membuat folder input/output."
    ui_pause
    return 1
  fi

  printf '\n%b\n' "${DIM}Input:  $INPUT_DIR${RESET}"
  printf '%b\n' "${DIM}Output: $OUTPUT_DIR${RESET}"

  # Kumpulkan daftar file video yang didukung
  local -a videos=()
  while IFS= read -r -d '' f; do
    videos+=("$f")
  done < <(find "$INPUT_DIR" -maxdepth 1 -type f \( \
    -iname "*.mp4" -o -iname "*.mkv" -o -iname "*.mov" -o \
    -iname "*.webm" -o -iname "*.avi" -o -iname "*.flv" -o \
    -iname "*.wmv" -o -iname "*.m4v" -o -iname "*.3gp" -o \
    -iname "*.ts" -o -iname "*.mts" -o -iname "*.m2ts" \) -print0 2>/dev/null)

  if [[ ${#videos[@]} -eq 0 ]]; then
    ui_warn "Tidak ada file video di: $INPUT_DIR"
    printf '\n%b\n' "${DIM}Letakkan file video di folder input, lalu jalankan ulang.${RESET}"
    ui_pause
    return 0
  fi

  printf '\n%b\n' "${BOLD}Ditemukan ${#videos[@]} file video.${RESET}"

  # Trap untuk membersihkan file sementara jika terputus
  local -a tmp_files=()
  _vs_cleanup() {
    local f
    for f in "${tmp_files[@]}"; do
      [[ -f "$f" ]] && rm -f -- "$f"
    done
  }
  trap _vs_cleanup EXIT INT TERM

  local total_ok=0
  local total_fail=0
  local total_clips=0

  for video in "${videos[@]}"; do
    local basename name
    basename=$(basename -- "$video")
    name="${basename%.*}"

    printf '\n%b\n' "${CYAN}${BOLD}► Memproses: $basename${RESET}"

    # Ambil durasi dengan ffprobe
    local duration
    duration=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 -- "$video" 2>/dev/null)

    if [[ -z "$duration" || "$duration" == "N/A" ]]; then
      ui_error "Gagal membaca durasi: $basename"
      ((total_fail++))
      continue
    fi

    # Hitung jumlah klip 10 detik (floor)
    local num_clips
    num_clips=$(awk "BEGIN {printf \"%d\", int($duration / 10)}")

    if (( num_clips == 0 )); then
      printf '  %bDurasi %.2fs < 10s, dilewati (0 klip).%b\n' "$DIM" "$duration" "$RESET"
      continue
    fi

    printf '  Durasi: %.2fs → %d klip\n' "$duration" "$num_clips"

    local clip_ok=0
    local clip_fail=0

    for ((i = 0; i < num_clips; i++)); do
      local start=$((i * 10))
      local part_num=$((i + 1))
      local part_str
      part_str=$(printf "%03d" "$part_num")

      local output_name="${name}_part${part_str}.mp4"
      local output_path="$OUTPUT_DIR/$output_name"

      # Hindari menimpa file yang sudah ada
      if [[ -e "$output_path" ]]; then
        local counter=1
        while [[ -e "$OUTPUT_DIR/${name}_part${part_str}_${counter}.mp4" ]]; do
          ((counter++))
        done
        output_name="${name}_part${part_str}_${counter}.mp4"
        output_path="$OUTPUT_DIR/$output_name"
      fi

      local tmp_output="${output_path}.tmp"
      tmp_files+=("$tmp_output")

      printf '  Klip %d/%d (mulai %ds)... ' "$part_num" "$num_clips" "$start"

      # Jalankan FFmpeg: potong 10 detik, tanpa audio
      if ffmpeg -y -ss "$start" -i "$video" -t 10 -an \
        -c:v libx264 -preset ultrafast -crf 23 \
        -movflags +faststart \
        -avoid_negative_ts make_zero \
        -f mp4 "$tmp_output" >/dev/null 2>&1; then

        # Validasi hasil
        local out_duration out_has_audio
        out_duration=$(ffprobe -v error -show_entries format=duration \
          -of default=noprint_wrappers=1:nokey=1 -- "$tmp_output" 2>/dev/null)
        out_has_audio=$(ffprobe -v error -show_entries stream=codec_type \
          -of csv=p=0 -- "$tmp_output" 2>/dev/null | grep -c '^audio$' || true)

        # Validasi: durasi harus >= 9.5s dan tidak ada audio stream
        local valid=1
        if [[ -z "$out_duration" ]]; then
          valid=0
        else
          local dur_check
          dur_check=$(awk "BEGIN {print ($out_duration >= 9.5) ? 1 : 0}")
          if [[ "$dur_check" != "1" ]]; then
            valid=0
          fi
        fi
        if [[ "$out_has_audio" -gt 0 ]]; then
          valid=0
        fi

        if [[ "$valid" -eq 1 ]]; then
          # Ganti nama temp → final
          if mv -- "$tmp_output" "$output_path" 2>/dev/null; then
            printf '%bOK%b (%.2fs, no audio)\n' "$GREEN" "$RESET" "$out_duration"
            ((clip_ok++))
          else
            printf '%bGAGAL%b (rename)\n' "$RED" "$RESET"
            rm -f -- "$tmp_output"
            ((clip_fail++))
          fi
        else
          printf '%bGAGAL%b (validasi: dur=%.2fs audio=%s)\n' "$RED" "$RESET" "${out_duration:-0}" "$out_has_audio"
          rm -f -- "$tmp_output"
          ((clip_fail++))
        fi
      else
        printf '%bGAGAL%b (ffmpeg error)\n' "$RED" "$RESET"
        rm -f -- "$tmp_output"
        ((clip_fail++))
      fi
    done

    printf '  → %d berhasil, %d gagal\n' "$clip_ok" "$clip_fail"
    ((total_ok += clip_ok))
    ((total_fail += clip_fail))
    ((total_clips += num_clips))
  done

  # Bersihkan trap
  trap - EXIT INT TERM

  printf '\n%b\n' "${BOLD}${GREEN}=== RINGKASAN ===${RESET}"
  printf '  File video diproses: %d\n' "${#videos[@]}"
  printf '  Total klip target:   %d\n' "$total_clips"
  printf '  Klip berhasil:       %d\n' "$total_ok"
  printf '  Klip gagal:          %d\n' "$total_fail"
  printf '  Output:              %s\n' "$OUTPUT_DIR"

  if (( total_fail > 0 )); then
    ui_warn "Ada $total_fail klip yang gagal. Periksa log FFmpeg."
  else
    ui_ok "Semua klip berhasil dibuat."
  fi

  ui_pause
  return 0
}
