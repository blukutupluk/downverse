#!/usr/bin/env bash
# Unit test modul audio_extractor dengan stub ffmpeg/ffprobe/proot_login/python3.
# Fixture per-file: baris pertama menentukan perilaku (VIDEO, NO_AUDIO, SILENT,
# FAIL, QUOTA, SILENT_GEMINI). Key Gemini memakai file temp, bukan key asli.
# Tidak menyentuh backend, model, jaringan, atau SD card asli.

DL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d /data/data/com.termux/files/usr/tmp/ae-test.XXXXXX)"
trap 'rm -rf -- "$TMP"' EXIT

AUDIO_EXTRACTOR_ROOT="$TMP/out"
OUTPUT_ROOT="$TMP/output"
LOG_DIR="$TMP/logs"
PROOT_PYTHON=/venv/python
FFMPEG_CALLS="$TMP/ffmpeg.calls"
PROOT_CALLS="$TMP/proot.calls"
GEMINI_CALLS="$TMP/gemini.calls"
GEMINI_KEY_USED="$TMP/gemini.key.used"
AE_GEMINI_KEY_FILE="$TMP/gemini/gemini.key"
mkdir -p "$AUDIO_EXTRACTOR_ROOT" "$OUTPUT_ROOT" "$LOG_DIR" \
  "$TMP/in" "$TMP/gemini" "$AUDIO_EXTRACTOR_ROOT/temp"
: > "$FFMPEG_CALLS"
: > "$PROOT_CALLS"
: > "$GEMINI_CALLS"
: > "$GEMINI_KEY_USED"

# --- stub ---
ffprobe() {
  local entries="" target="" key
  while (($#)); do
    key="$1"
    case "$key" in
      -show_entries) entries="$2"; shift 2 ;;
      -of|-select_streams|-v) shift 2 ;;
      --) shift ;;
      -*) shift ;;
      *) target="$1"; shift ;;
    esac
  done
  [[ -n "$target" && -f "$target" ]] || return 1
  local first=""
  IFS= read -r first < "$target" || :
  # File rusak: ffprobe gagal membaca durasi maupun stream.
  [[ "$first" == "CORRUPT" ]] && return 1
  case "$entries" in
    format=duration)
      if [[ "$first" == "BAD_DURATION" ]]; then printf '0\n'; else printf '2.000000\n'; fi ;;
    stream=codec_type)
      [[ "$first" == "NO_AUDIO" ]] || printf 'audio\n' ;;
    stream=codec_name)
      case "$first" in AUDIO_DATA|SILENT|BAD_DURATION|QUOTA|SILENT_GEMINI) printf 'mp3\n' ;; esac ;;
  esac
  return 0
}

ffmpeg() {
  local src="" target="" key first=""
  printf '%s\n' "$*" >> "$FFMPEG_CALLS"
  while (($#)); do
    key="$1"
    case "$key" in
      -i) src="$2"; shift 2 ;;
      -c:a|-b:a|-q:a|-f) shift 2 ;;
      --) shift ;;
      -*) shift ;;
      *) target="$1"; shift ;;
    esac
  done
  [[ -n "$target" ]] || return 1
  if [[ -n "$src" && -f "$src" ]]; then IFS= read -r first < "$src" || :; fi
  [[ "$first" == "FAIL" ]] && return 1
  if [[ "$first" == SILENT* || "$first" == QUOTA ]]; then
    printf '%s\n' "$first" > "$target"
  else
    printf 'AUDIO_DATA\n' > "$target"
  fi
  return 0
}

proot_login() {
  printf '%s\n' "$*" >> "$PROOT_CALLS"
  local audio="" out="" model="" script="" key first=""
  while (($#)); do
    key="$1"
    case "$key" in
      --audio) audio="$2"; shift 2 ;;
      --out-txt) out="$2"; shift 2 ;;
      --model-dir) model="$2"; shift 2 ;;
      --model-size|--language) shift 2 ;;
      --timestamps) shift ;;
      --) shift ;;
      -*) shift ;;
      *) script="$1"; shift ;;
    esac
  done
  [[ "$script" == *transcribe.py && -n "$out" ]] || return 1
  if [[ -n "$audio" && -f "$audio" ]]; then IFS= read -r first < "$audio" || :; fi
  if [[ "$first" == "SILENT" ]]; then
    printf '%s\n' '{"ok": false, "reason": "NO_SPEECH", "language": "id", "duration": 2.0, "segments": 0, "text_chars": 0, "model": "base"}'
    return 0
  fi
  printf '%s\n' 'Halo dunia, ini contoh transkripsi.' '[tidak terdengar]' > "$out" || return 1
  printf '%s\n' '{"ok": true, "language": "id", "duration": 2.0, "segments": 2, "text_chars": 55, "model": "base"}'
  return 0
}

# Stub backend Gemini: key dibaca dari file, tidak pernah dari argv.
python3() {
  printf '%s\n' "$*" >> "$GEMINI_CALLS"
  local audio="" keyfile="" out="" keyval="" first=""
  while (($#)); do
    case "$1" in
      --audio) audio="$2"; shift 2 ;;
      --key-file) keyfile="$2"; shift 2 ;;
      --out-txt) out="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  [[ -n "$keyfile" && -r "$keyfile" ]] || return 1
  IFS= read -r keyval < "$keyfile" || :
  printf '%s' "$keyval" > "$GEMINI_KEY_USED"
  [[ -n "$audio" && -f "$audio" ]] && IFS= read -r first < "$audio" || :
  case "$first" in
    QUOTA)
      printf '%s\n' '{"ok": false, "reason": "QUOTA_EXHAUSTED", "message": "Kuota Gemini habis. Tempel API key lain saat prompt muncul."}'
      return 1 ;;
    BAD_KEY)
      printf '%s\n' '{"ok": false, "reason": "INVALID_KEY", "message": "API key Gemini tidak valid."}'
      return 1 ;;
    SILENT_GEMINI)
      printf '%s\n' '{"ok": false, "reason": "NO_SPEECH", "language": "", "duration": 0.0, "segments": 0, "text_chars": 0, "model": "gemini-4-hydrogen"}'
      return 0 ;;
  esac
  printf '%s\n' 'Hasil transkripsi Gemini.' '[tidak terdengar]' > "$out" || return 1
  printf '%s\n' '{"ok": true, "language": "", "duration": 0.0, "segments": 2, "text_chars": 26, "model": "gemini-4-hydrogen"}'
  return 0
}

ui_header() { :; }
ui_section() { :; }
ui_item() { :; }
ui_line() { :; }
ui_error() { printf 'ERROR: %s\n' "$*" >&2; }
ui_warn() { printf 'PERINGATAN: %s\n' "$*"; }
ui_ok() { :; }
ui_pause() { :; }
log_info() { :; }
log_error() { :; }

# shellcheck source=/dev/null
source "$DL_DIR/modules/audio_extractor.sh"

fails=0
ok() { printf 'OK: %s\n' "$1"; }
bad() {
  printf 'FAIL: %s\n' "$1"
  [[ -n "${2:-}" ]] && printf '     %s\n' "$2"
  fails=$((fails + 1))
}
counters() { printf '%s/%s/%s/%s/%s/%s' "$AE_TOTAL" "$AE_MP3_OK" "$AE_TXT_OK" "$AE_NO_SPEECH" "$AE_SKIP" "$AE_FAIL"; }
reset_state() {
  if declare -F ae_reset_state >/dev/null 2>&1; then ae_reset_state; fi
  : > "$FFMPEG_CALLS"
  : > "$PROOT_CALLS"
  : > "$GEMINI_CALLS"
  : > "$GEMINI_KEY_USED"
}
make_video() { printf '%s\n' "${2:-VIDEO}" > "$TMP/in/$1"; printf '%s' "$TMP/in/$1"; }
# Jalankan fungsi di shell saat ini (bukan subshell) agar counter tetap terbaca.
run_ae() {
  : > "$TMP/ae.out"
  "$@" > "$TMP/ae.out" 2>&1
  AE_LAST_RC=$?
}

# --- 1: video tanpa stream audio ---
test_no_audio_stream() {
  reset_state
  local v out
  v=$(make_video no_audio.mp4 NO_AUDIO)
  run_ae ae_process "$v" both no
  out=$(<"$TMP/ae.out")
  if [[ "$out" == *'tidak memiliki stream audio'* ]] \
    && (( AE_FAIL == 1 && AE_MP3_OK == 0 && AE_TXT_OK == 0 && AE_NO_SPEECH == 0 )) \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/no_audio.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/no_audio.txt" ]]; then
    ok test_no_audio_stream
  else
    bad test_no_audio_stream "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 2: audio hening masuk bucket TANPA_UCAPAN ---
test_no_speech_bucket() {
  reset_state
  local v out
  v=$(make_video silent.mp4 SILENT)
  run_ae ae_process "$v" both no
  out=$(<"$TMP/ae.out")
  if (( AE_MP3_OK == 1 && AE_TXT_OK == 0 && AE_NO_SPEECH == 1 && AE_FAIL == 0 )) \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/silent.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/silent.txt" ]] \
    && [[ "$out" == *'Tidak ada ucapan'* ]]; then
    ok test_no_speech_bucket
  else
    bad test_no_speech_bucket "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 3: output valid dilewati tanpa memanggil backend ---
test_skip_valid_output() {
  reset_state
  local v out
  v=$(make_video skip.mp4 VIDEO)
  ae_process "$v" both no >/dev/null 2>&1
  cp -- "$AUDIO_EXTRACTOR_ROOT/skip.mp3" "$TMP/skip.mp3.before"
  cp -- "$AUDIO_EXTRACTOR_ROOT/skip.txt" "$TMP/skip.txt.before"
  reset_state
  run_ae ae_process "$v" both no
  out=$(<"$TMP/ae.out")
  if (( AE_SKIP == 1 && AE_MP3_OK == 0 && AE_TXT_OK == 0 && AE_FAIL == 0 )) \
    && cmp -s "$TMP/skip.mp3.before" "$AUDIO_EXTRACTOR_ROOT/skip.mp3" \
    && cmp -s "$TMP/skip.txt.before" "$AUDIO_EXTRACTOR_ROOT/skip.txt" \
    && [[ ! -s "$FFMPEG_CALLS" && ! -s "$PROOT_CALLS" ]]; then
    ok test_skip_valid_output
  else
    bad test_skip_valid_output "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 4: output invalid tidak ditimpa diam-diam ---
test_invalid_output_not_overwritten() {
  reset_state
  local v out
  v=$(make_video invalid.mp4 VIDEO)
  printf 'INVALID\n' > "$AUDIO_EXTRACTOR_ROOT/invalid.mp3"
  run_ae ae_process "$v" mp3 no
  out=$(<"$TMP/ae.out")
  if [[ "$out" == *'tidak valid'* ]] \
    && (( AE_SKIP == 1 && AE_MP3_OK == 0 && AE_FAIL == 0 )) \
    && [[ "$(<"$AUDIO_EXTRACTOR_ROOT/invalid.mp3")" == 'INVALID' ]] \
    && [[ ! -s "$FFMPEG_CALLS" ]]; then
    ok test_invalid_output_not_overwritten
  else
    bad test_invalid_output_not_overwritten "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 5: proses ulang mem-backup file lama ---
test_reprocess_backup() {
  reset_state
  local v out backup
  v=$(make_video reproc.mp4 VIDEO)
  printf 'OLD_MP3\n' > "$AUDIO_EXTRACTOR_ROOT/reproc.mp3"
  run_ae ae_process "$v" mp3 yes
  out=$(<"$TMP/ae.out")
  backup=$(find "$AUDIO_EXTRACTOR_ROOT" -maxdepth 1 -name 'reproc.mp3.bak.*' -print -quit)
  if [[ -n "$backup" && "$(<"$backup")" == 'OLD_MP3' ]] \
    && [[ "$(<"$AUDIO_EXTRACTOR_ROOT/reproc.mp3")" == 'AUDIO_DATA' ]] \
    && (( AE_MP3_OK == 1 && AE_SKIP == 0 && AE_FAIL == 0 )); then
    ok test_reprocess_backup
  else
    bad test_reprocess_backup "counters=$(counters) backup=$backup out=$(printf '%q' "$out")"
  fi
}

# --- 6: nama file dengan spasi dan tanda kutip ---
test_filename_with_spaces() {
  reset_state
  local name="video dengan spasi's.mp4" v out mp3 txt
  v=$(make_video "$name" VIDEO)
  run_ae ae_process "$v" both no
  out=$(<"$TMP/ae.out")
  mp3="$AUDIO_EXTRACTOR_ROOT/video dengan spasi's.mp3"
  txt="$AUDIO_EXTRACTOR_ROOT/video dengan spasi's.txt"
  if [[ -s "$mp3" && -s "$txt" ]] \
    && [[ "$out" == *"$mp3"* && "$out" == *"$txt"* ]] \
    && grep -Fq -- "$v" "$FFMPEG_CALLS" \
    && (( AE_MP3_OK == 1 && AE_TXT_OK == 1 && AE_FAIL == 0 )); then
    ok test_filename_with_spaces
  else
    bad test_filename_with_spaces "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 7: satu file gagal, batch tetap lanjut ---
test_batch_continue_on_failure() {
  reset_state
  local dir="$TMP/batchin" out
  mkdir -p "$dir"
  printf 'VIDEO\n' > "$dir/aa_good.mp4"
  printf 'FAIL\n' > "$dir/bb_fail.mp4"
  printf 'VIDEO\n' > "$dir/cc_good.mp4"
  run_ae ae_batch "$dir" mp3 no
  out=$(<"$TMP/ae.out")
  if [[ "$out" == *'[1/3] aa_good.mp4'* && "$out" == *'[2/3] bb_fail.mp4'* \
    && "$out" == *'[3/3] cc_good.mp4'* ]] \
    && [[ "$out" == *'TOTAL=3'* && "$out" == *'BERHASIL_MP3=2'* && "$out" == *'GAGAL=1'* ]] \
    && [[ "$out" == *'GAGAL: '*"bb_fail.mp4"* ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/aa_good.mp3" && -s "$AUDIO_EXTRACTOR_ROOT/cc_good.mp3" ]] \
    && (( AE_TOTAL == 3 && AE_MP3_OK == 2 && AE_FAIL == 1 )); then
    ok test_batch_continue_on_failure
  else
    bad test_batch_continue_on_failure "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 8: temp lama dibersihkan dan tidak ada sisa setelah job ---
test_temp_cleanup() {
  reset_state
  local stale="$AUDIO_EXTRACTOR_ROOT/temp/ae.stale.lama" v leftovers
  mkdir -p "$stale"
  printf 'x\n' > "$stale/leftover.txt"
  ae_cleanup_stale_temps
  v=$(make_video cleanup.mp4 VIDEO)
  ae_process "$v" mp3 no >/dev/null 2>&1
  leftovers=$(find "$AUDIO_EXTRACTOR_ROOT/temp" -maxdepth 1 -name 'ae.*' -print 2>/dev/null)
  if [[ ! -e "$stale" && -z "$leftovers" && -d "$AUDIO_EXTRACTOR_ROOT/temp" ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/cleanup.mp3" ]]; then
    ok test_temp_cleanup
  else
    bad test_temp_cleanup "stale=$stale leftovers=$(printf '%q' "$leftovers")"
  fi
}

# --- 9: prompt ask ke stderr, stdout hanya satu token bersih ---
test_ask_existing_stdout_contract() {
  reset_state
  local input expected out err pass=1
  while IFS='|' read -r input expected; do
    [[ -n "$input" ]] || continue
    out=$(printf '%s\n' "$input" | _ae_ask_existing "$TMP/ask.mp3" "$TMP/ask.txt" 0 2>"$TMP/ask.err")
    err=$(<"$TMP/ask.err")
    if [[ "$out" != "$expected" ]]; then
      pass=0
      printf '     stdout=%q expected=%q (input=%q)\n' "$out" "$expected" "$input"
    fi
    if [[ "$err" != *'Output sudah ada'* || "$err" != *'Pilih [1/2/3]:'* ]]; then
      pass=0
      printf '     prompt tidak ada di stderr (input=%q, stderr=%q)\n' "$input" "$err"
    fi
  done <<'EOF'
1|no
2|yes
3|cancel
EOF
  if ((pass)); then
    ok test_ask_existing_stdout_contract
  else
    bad test_ask_existing_stdout_contract
  fi
}

# --- 10: bahasa hasil deteksi ditampilkan per file ---
test_detected_language_displayed() {
  reset_state
  local v out
  v=$(make_video lang.mp4 VIDEO)
  run_ae ae_process "$v" both no
  out=$(<"$TMP/ae.out")
  if [[ "$out" == *'bahasa=id'* ]] \
    && (( AE_TXT_OK == 1 && AE_FAIL == 0 )); then
    ok test_detected_language_displayed
  else
    bad test_detected_language_displayed "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 11: file rusak dibedakan dari file tanpa stream audio ---
test_corrupt_video_message() {
  reset_state
  local v out
  v=$(make_video corrupt.mp4 CORRUPT)
  run_ae ae_process "$v" both no
  out=$(<"$TMP/ae.out")
  if [[ "$out" == *'Gagal membaca video'* ]] \
    && [[ "$out" != *'tidak memiliki stream audio'* ]] \
    && (( AE_FAIL == 1 && AE_MP3_OK == 0 && AE_TXT_OK == 0 )) \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/corrupt.mp3" ]]; then
    ok test_corrupt_video_message
  else
    bad test_corrupt_video_message "counters=$(counters) out=$(printf '%q' "$out")"
  fi
}

# --- 12: single video, tepat satu video → Enter langsung memakainya ---
test_single_autopick_one_video() {
  reset_state
  local old_input="$AE_INPUT_DIR" v out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  v=$(make_video auto.mp4 VIDEO)
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n1\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" != *'Pilih video'* ]] \
    && [[ -f "$AUDIO_EXTRACTOR_ROOT/auto.mp3" ]] \
    && (( AE_TOTAL == 1 )); then
    ok test_single_autopick_one_video
  else
    bad test_single_autopick_one_video "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 13: single video, beberapa video → daftar bernomor, Enter pilih 1 ---
test_single_list_default_choice() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  make_video a.mp4 VIDEO >/dev/null
  make_video b.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n1\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'Pilih video [1-2]'* ]] \
    && [[ "$out" == *'a.mp4'* && "$out" == *'b.mp4'* ]] \
    && [[ -f "$AUDIO_EXTRACTOR_ROOT/a.mp3" ]] \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/b.mp3" ]] \
    && (( AE_TOTAL == 1 )); then
    ok test_single_list_default_choice
  else
    bad test_single_list_default_choice "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 14: single video, folder kosong → error jelas, tanpa ffmpeg ---
test_single_empty_folder_error() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n1\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'Tidak ada video'* ]] \
    && [[ "$out" == *"$TMP/in"* ]] \
    && [[ ! -s "$FFMPEG_CALLS" ]] \
    && (( AE_TOTAL == 0 )); then
    ok test_single_empty_folder_error
  else
    bad test_single_empty_folder_error "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 15: daftar bernomor tetap benar untuk nama ber-spasi ---
test_single_list_with_spaces() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  make_video a.mp4 VIDEO >/dev/null
  make_video 'copy dengan spasi.mp4' VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n1\n\n2\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'copy dengan spasi.mp4'* ]] \
    && [[ -f "$AUDIO_EXTRACTOR_ROOT/copy dengan spasi.mp3" ]] \
    && (( AE_TOTAL == 1 )); then
    ok test_single_list_with_spaces
  else
    bad test_single_list_with_spaces "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 16: video di dalam folder output tetap ditolak ---
test_single_inside_output_rejected() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  mkdir -p "$AUDIO_EXTRACTOR_ROOT/in"
  printf 'VIDEO\n' > "$AUDIO_EXTRACTOR_ROOT/in/inside.mp4"
  AE_INPUT_DIR="$AUDIO_EXTRACTOR_ROOT/in"
  printf '1\n1\n1\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  rm -rf -- "$AUDIO_EXTRACTOR_ROOT/in"
  if { [[ "$out" == *'Tidak ada video'* ]] || [[ "$out" == *'berada di dalam folder output'* ]]; } \
    && [[ ! -s "$FFMPEG_CALLS" ]] \
    && (( AE_TOTAL == 0 )); then
    ok test_single_inside_output_rejected
  else
    bad test_single_inside_output_rejected "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 17: mengetik path lengkap tetap bekerja ---
test_single_typed_path_still_works() {
  reset_state
  local manual out
  rm -f -- "$TMP"/*.mp4 "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf 'VIDEO\n' > "$TMP/manual.mp4"
  manual="$TMP/manual.mp4"
  printf '1\n1\n1\n%s\n' "$manual" > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  if [[ -f "$AUDIO_EXTRACTOR_ROOT/manual.mp3" ]] \
    && [[ "$out" != *'Pilih video'* ]] \
    && (( AE_TOTAL == 1 )); then
    ok test_single_typed_path_still_works
  else
    bad test_single_typed_path_still_works "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 18: pilihan di luar rentang ditolak tanpa memproses ---
test_single_invalid_choice() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  make_video a.mp4 VIDEO >/dev/null
  make_video b.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n1\n\n9\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'Pilihan video tidak valid'* ]] \
    && [[ ! -s "$FFMPEG_CALLS" ]] \
    && (( AE_TOTAL == 0 )); then
    ok test_single_invalid_choice
  else
    bad test_single_invalid_choice "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 19: pilihan dengan leading zero dibaca desimal, bukan oktal ---
test_single_leading_zero_choice() {
  reset_state
  local old_input="$AE_INPUT_DIR" out i
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  for i in $(seq -w 1 10); do make_video "v$i.mp4" VIDEO >/dev/null; done
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n1\n\n08\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ -f "$AUDIO_EXTRACTOR_ROOT/v08.mp3" ]] \
    && [[ "$out" != *'Pilihan video tidak valid'* ]] \
    && (( AE_TOTAL == 1 )); then
    ok test_single_leading_zero_choice
  else
    bad test_single_leading_zero_choice "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 20: job MP3 saja tidak menampilkan prompt mesin/key ---
test_mp3_job_skips_engine_prompt() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  make_video mp3only.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n2\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" != *'Mesin transkripsi'* && "$out" != *'API key Google'* ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/mp3only.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/mp3only.txt" ]] \
    && [[ ! -s "$GEMINI_CALLS" ]] \
    && (( AE_MP3_OK == 1 && AE_TXT_OK == 0 && AE_FAIL == 0 )); then
    ok test_mp3_job_skips_engine_prompt
  else
    bad test_mp3_job_skips_engine_prompt "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 21: key baru disimpan 0600 dan tidak masuk argv ---
test_gemini_new_key_saved_and_used() {
  reset_state
  local old_input="$AE_INPUT_DIR" out call newkey='AIza-new-key-123'
  rm -f -- "$AE_GEMINI_KEY_FILE" "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  make_video gemnew.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n%s\n\n' "$newkey" > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  call=$(<"$GEMINI_CALLS")
  AE_INPUT_DIR="$old_input"
  if [[ -f "$AE_GEMINI_KEY_FILE" && "$(<"$AE_GEMINI_KEY_FILE")" == "$newkey" ]] \
    && [[ "$(stat -c '%a' "$AE_GEMINI_KEY_FILE")" == '600' ]] \
    && [[ "$call" == *'--key-file'* && "$call" != *"$newkey"* ]] \
    && [[ "$(<"$GEMINI_KEY_USED")" == "$newkey" ]] \
    && [[ "$out" == *'Transkripsi (Gemini API)'* && "$out" != *'model lokal'* ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/gemnew.txt" ]] \
    && (( AE_TXT_OK == 1 && AE_FAIL == 0 )); then
    ok test_gemini_new_key_saved_and_used
  else
    bad test_gemini_new_key_saved_and_used "key=$(<"$AE_GEMINI_KEY_FILE") mode=$(stat -c '%a' "$AE_GEMINI_KEY_FILE" 2>/dev/null) call=$call out=$(printf '%q' "$out")"
  fi
}

# --- 22: Enter memakai key tersimpan ---
test_gemini_enter_uses_stored_key() {
  reset_state
  local old_input="$AE_INPUT_DIR" out before='stored-key-old'
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf '%s\n' "$before" > "$AE_GEMINI_KEY_FILE"
  chmod 600 -- "$AE_GEMINI_KEY_FILE"
  make_video gemold.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$(<"$AE_GEMINI_KEY_FILE")" == "$before" ]] \
    && [[ "$(<"$GEMINI_KEY_USED")" == "$before" ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/gemold.txt" ]] \
    && (( AE_TXT_OK == 1 && AE_FAIL == 0 )); then
    ok test_gemini_enter_uses_stored_key
  else
    bad test_gemini_enter_uses_stored_key "used=$(<"$GEMINI_KEY_USED") out=$(printf '%q' "$out")"
  fi
}

# --- 23: key baru menimpa key lama ---
test_gemini_key_replacement() {
  reset_state
  local old_input="$AE_INPUT_DIR" out replacement='replacement-key-999'
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf 'old-key-111\n' > "$AE_GEMINI_KEY_FILE"
  make_video gemreplace.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n%s\n\n' "$replacement" > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$(<"$AE_GEMINI_KEY_FILE")" == "$replacement" ]] \
    && [[ "$(<"$GEMINI_KEY_USED")" == "$replacement" ]] \
    && (( AE_TXT_OK == 1 && AE_FAIL == 0 )); then
    ok test_gemini_key_replacement
  else
    bad test_gemini_key_replacement "key=$(<"$AE_GEMINI_KEY_FILE") out=$(printf '%q' "$out")"
  fi
}

# --- 24: tanpa key tersimpan, Gemini tidak dipanggil ---
test_gemini_missing_key_stops_before_upload() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$AE_GEMINI_KEY_FILE" "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  make_video gemnokey.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'Belum ada API key'* ]] \
    && [[ ! -s "$GEMINI_CALLS" ]] \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/gemnokey.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/gemnokey.txt" ]] \
    && (( AE_TOTAL == 0 && AE_FAIL == 0 )); then
    ok test_gemini_missing_key_stops_before_upload
  else
    bad test_gemini_missing_key_stops_before_upload "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 25: kuota habis menampilkan pesan ganti key ---
test_gemini_quota_error_message() {
  reset_state
  local old_input="$AE_INPUT_DIR" out low
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf 'stored-key\n' > "$AE_GEMINI_KEY_FILE"
  make_video gemquota.mp4 QUOTA >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  low="${out,,}"
  AE_INPUT_DIR="$old_input"
  if [[ "$low" == *'kuota'* && "$low" == *'key'* ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/gemquota.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/gemquota.txt" ]] \
    && (( AE_MP3_OK == 1 && AE_FAIL == 1 )); then
    ok test_gemini_quota_error_message
  else
    bad test_gemini_quota_error_message "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 26: batch Gemini tetap lanjut setelah kuota habis ---
test_gemini_batch_continues_on_quota() {
  reset_state
  local dir="$TMP/batchgemini" out
  rm -rf -- "$dir"
  mkdir -p "$dir"
  printf 'stored-key\n' > "$AE_GEMINI_KEY_FILE"
  printf 'VIDEO\n' > "$dir/aa_good.mp4"
  printf 'QUOTA\n' > "$dir/bb_quota.mp4"
  printf 'VIDEO\n' > "$dir/cc_good.mp4"
  printf '2\n1\n2\n\n%s\nn\n' "$dir" > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  if [[ "$out" == *'[1/3] aa_good.mp4'* && "$out" == *'[2/3] bb_quota.mp4'* \
    && "$out" == *'[3/3] cc_good.mp4'* ]] \
    && [[ "$out" == *'BERHASIL_TXT=2'* && "$out" == *'GAGAL=1'* ]] \
    && [[ "$out" == *'GAGAL: '*'bb_quota.mp4'* ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/aa_good.txt" && -s "$AUDIO_EXTRACTOR_ROOT/cc_good.txt" ]] \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/bb_quota.txt" ]]; then
    ok test_gemini_batch_continues_on_quota
  else
    bad test_gemini_batch_continues_on_quota "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 27: NO_SPEECH Gemini tidak membuat TXT, MP3 tetap valid ---
test_gemini_no_speech_bucket() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf 'stored-key\n' > "$AE_GEMINI_KEY_FILE"
  make_video gemsilent.mp4 SILENT_GEMINI >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'TANPA_UCAPAN'* ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/gemsilent.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/gemsilent.txt" ]] \
    && (( AE_MP3_OK == 1 && AE_NO_SPEECH == 1 && AE_TXT_OK == 0 && AE_FAIL == 0 )); then
    ok test_gemini_no_speech_bucket
  else
    bad test_gemini_no_speech_bucket "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 28: key tersimpan yang dipakai ulang tetap di-chmod 600 ---
test_gemini_reused_key_chmod_600() {
  reset_state
  local old_input="$AE_INPUT_DIR" out mode
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf 'stored-key-0644\n' > "$AE_GEMINI_KEY_FILE"
  chmod 644 -- "$AE_GEMINI_KEY_FILE"
  make_video gemmode.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  mode=$(stat -c '%a' "$AE_GEMINI_KEY_FILE" 2>/dev/null)
  AE_INPUT_DIR="$old_input"
  if [[ "$mode" == '600' ]] \
    && [[ "$(<"$AE_GEMINI_KEY_FILE")" == 'stored-key-0644' ]] \
    && [[ -s "$AUDIO_EXTRACTOR_ROOT/gemmode.txt" ]] \
    && (( AE_TXT_OK == 1 && AE_FAIL == 0 )); then
    ok test_gemini_reused_key_chmod_600
  else
    bad test_gemini_reused_key_chmod_600 "mode=$mode out=$(printf '%q' "$out")"
  fi
}

# --- 29: key tersimpan hanya whitespace dianggap tidak ada ---
test_gemini_whitespace_key_aborts() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf '   \n' > "$AE_GEMINI_KEY_FILE"
  make_video gemspace.mp4 VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n1\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ "$out" == *'API key Gemini tersimpan kosong'* ]] \
    && [[ ! -s "$GEMINI_CALLS" ]] \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/gemspace.mp3" && ! -e "$AUDIO_EXTRACTOR_ROOT/gemspace.txt" ]] \
    && (( AE_TOTAL == 0 && AE_FAIL == 0 )); then
    ok test_gemini_whitespace_key_aborts
  else
    bad test_gemini_whitespace_key_aborts "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

# --- 30: Gemini job TXT saja dengan nama file berspasi ---
test_gemini_txt_only_with_spaces() {
  reset_state
  local old_input="$AE_INPUT_DIR" out
  rm -f -- "$TMP/in"/* "$AUDIO_EXTRACTOR_ROOT"/*.mp3 "$AUDIO_EXTRACTOR_ROOT"/*.txt 2>/dev/null
  printf 'stored-key\n' > "$AE_GEMINI_KEY_FILE"
  make_video 'gem txt space.mp4' VIDEO >/dev/null
  AE_INPUT_DIR="$TMP/in"
  printf '1\n3\n2\n\n\n' > "$TMP/stdin"
  module_audio_extractor < "$TMP/stdin" > "$TMP/ae.out" 2>&1
  out=$(<"$TMP/ae.out")
  AE_INPUT_DIR="$old_input"
  if [[ -s "$AUDIO_EXTRACTOR_ROOT/gem txt space.txt" ]] \
    && [[ ! -e "$AUDIO_EXTRACTOR_ROOT/gem txt space.mp3" ]] \
    && (( AE_TXT_OK == 1 && AE_MP3_OK == 0 && AE_FAIL == 0 )); then
    ok test_gemini_txt_only_with_spaces
  else
    bad test_gemini_txt_only_with_spaces "out=$(printf '%q' "$out") counters=$(counters)"
  fi
}

test_no_audio_stream
test_no_speech_bucket
test_skip_valid_output
test_invalid_output_not_overwritten
test_reprocess_backup
test_filename_with_spaces
test_batch_continue_on_failure
test_temp_cleanup
test_ask_existing_stdout_contract
test_detected_language_displayed
test_corrupt_video_message
test_single_autopick_one_video
test_single_list_default_choice
test_single_empty_folder_error
test_single_list_with_spaces
test_single_inside_output_rejected
test_single_typed_path_still_works
test_single_invalid_choice
test_single_leading_zero_choice
test_mp3_job_skips_engine_prompt
test_gemini_new_key_saved_and_used
test_gemini_enter_uses_stored_key
test_gemini_key_replacement
test_gemini_missing_key_stops_before_upload
test_gemini_quota_error_message
test_gemini_batch_continues_on_quota
test_gemini_no_speech_bucket
test_gemini_reused_key_chmod_600
test_gemini_whitespace_key_aborts
test_gemini_txt_only_with_spaces

if ((fails == 0)); then
  printf '\nSemua test lolos.\n'
  exit 0
fi
printf '\n%d test gagal.\n' "$fails"
exit 1
