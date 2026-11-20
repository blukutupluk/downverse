#!/usr/bin/env bash
# Unit test modul audio_extractor dengan stub ffmpeg/ffprobe/proot_login.
# Fixture per-file: baris pertama menentukan perilaku (VIDEO, NO_AUDIO,
# SILENT, FAIL). Tidak menyentuh backend, model, atau SD card asli.

DL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d /data/data/com.termux/files/usr/tmp/ae-test.XXXXXX)"
trap 'rm -rf -- "$TMP"' EXIT

AUDIO_EXTRACTOR_ROOT="$TMP/out"
OUTPUT_ROOT="$TMP/output"
LOG_DIR="$TMP/logs"
PROOT_PYTHON=/venv/python
FFMPEG_CALLS="$TMP/ffmpeg.calls"
PROOT_CALLS="$TMP/proot.calls"
mkdir -p "$AUDIO_EXTRACTOR_ROOT" "$OUTPUT_ROOT" "$LOG_DIR" \
  "$TMP/in" "$AUDIO_EXTRACTOR_ROOT/temp"
: > "$FFMPEG_CALLS"
: > "$PROOT_CALLS"

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
  case "$entries" in
    format=duration)
      if [[ "$first" == "BAD_DURATION" ]]; then printf '0\n'; else printf '2.000000\n'; fi ;;
    stream=codec_type)
      [[ "$first" == "NO_AUDIO" ]] || printf 'audio\n' ;;
    stream=codec_name)
      case "$first" in AUDIO_DATA|SILENT|BAD_DURATION) printf 'mp3\n' ;; esac ;;
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
  if [[ "$first" == "SILENT" ]]; then
    printf 'SILENT\n' > "$target"
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

test_no_audio_stream
test_no_speech_bucket
test_skip_valid_output
test_invalid_output_not_overwritten
test_reprocess_backup
test_filename_with_spaces
test_batch_continue_on_failure
test_temp_cleanup

if ((fails == 0)); then
  printf '\nSemua test lolos.\n'
  exit 0
fi
printf '\n%d test gagal.\n' "$fails"
exit 1
