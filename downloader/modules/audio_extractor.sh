#!/data/data/com.termux/files/usr/bin/bash
# Audio Extractor + Transcriber: video → MP3 tervalidasi + transkripsi TXT.
# Ekstraksi memakai FFmpeg Termux; transkripsi memakai transcribe_gemini.py
# dengan python3 Termux + key 0600. Modul di-source oleh launcher, jangan
# aktifkan set -u.

AE_MODULE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_ROOT="${AUDIO_EXTRACTOR_ROOT:-${OUTPUT_ROOT:-/storage/7544-8C33/output}/audio-extractor}"
TEMP_ROOT="$OUT_ROOT/temp"
AE_LOG_DIR="${LOG_DIR:-$AE_MODULE_ROOT/logs}"
AE_INPUT_DIR="${OUTPUT_ROOT:-/storage/7544-8C33/output}/input"
AE_GEMINI_SRC="$AE_MODULE_ROOT/backend/transcribe_gemini.py"
AE_GEMINI_KEY_FILE="${AE_GEMINI_KEY_FILE:-$HOME/.config/media-downloader/gemini.key}"

AE_TOTAL=0
AE_MP3_OK=0
AE_TXT_OK=0
AE_NO_SPEECH=0
AE_SKIP=0
AE_FAIL=0
AE_VIDEO_FILES=()
AE_DURATION=""
AE_HAS_AUDIO=0
declare -A AE_OUTPUT_OWNER=()
declare -a AE_BATCH_FAILED=()
declare -a _AE_SCRATCH_DIRS=()
_AE_TRAP_ARMED=0
_AE_SAVED_EXIT=""
_AE_SAVED_INT=""
_AE_SAVED_TERM=""
_AE_HAD_EXIT=0
_AE_HAD_INT=0
_AE_HAD_TERM=0

ae_reset_state() {
  AE_TOTAL=0
  AE_MP3_OK=0
  AE_TXT_OK=0
  AE_NO_SPEECH=0
  AE_SKIP=0
  AE_FAIL=0
  AE_OUTPUT_OWNER=()
  AE_BATCH_FAILED=()
}

_ae_cleanup_all() {
  local d
  for d in "${_AE_SCRATCH_DIRS[@]}"; do
    if [[ -n "$d" && -d "$d" ]]; then rm -rf -- "$d"; fi
  done
  _AE_SCRATCH_DIRS=()
}

# Ubah baris "trap -p" menjadi string perintah asli tanpa eval.
# Keluaran Bash: trap -- 'perintah' EXIT|SIGINT|SIGTERM
_ae_trap_command() {
  local line="$1" label="$2" code
  [[ -n "$line" ]] || { printf 'NONE'; return 0; }
  code="${line#trap -- }"
  code="${code% "$label"}"
  [[ "$code" == \'*\' ]] || { printf 'NONE'; return 0; }
  code="${code#\'}"
  code="${code%\'}"
  code="${code//\'\\\'\'/\'}"
  printf '%s' "$code"
}

_ae_arm_trap() {
  local line saved
  ((_AE_TRAP_ARMED == 1)) && return 0

  line=$(trap -p EXIT)
  _AE_HAD_EXIT=0; [[ -n "$line" ]] && _AE_HAD_EXIT=1
  saved=$(_ae_trap_command "$line" EXIT)
  [[ "$saved" == "NONE" ]] && saved=""
  _AE_SAVED_EXIT="$saved"

  line=$(trap -p INT)
  _AE_HAD_INT=0; [[ -n "$line" ]] && _AE_HAD_INT=1
  saved=$(_ae_trap_command "$line" SIGINT)
  [[ "$saved" == "NONE" ]] && saved=""
  _AE_SAVED_INT="$saved"

  line=$(trap -p TERM)
  _AE_HAD_TERM=0; [[ -n "$line" ]] && _AE_HAD_TERM=1
  saved=$(_ae_trap_command "$line" SIGTERM)
  [[ "$saved" == "NONE" ]] && saved=""
  _AE_SAVED_TERM="$saved"

  # Bersihkan scratch lebih dulu, kembalikan status exit caller, lalu jalankan
  # handler caller apa adanya. INT/TERM diakhiri exit agar job tidak dilanjutkan.
  local prefix='__ae_saved_rc=$?; _ae_cleanup_all; (exit "$__ae_saved_rc")'
  if ((_AE_HAD_EXIT)); then
    trap "$prefix; $_AE_SAVED_EXIT" EXIT
  else
    trap "$prefix" EXIT
  fi

  if ((_AE_HAD_INT)) && [[ -z "$_AE_SAVED_INT" ]]; then
    trap '' INT
  elif ((_AE_HAD_INT)); then
    trap "$prefix; $_AE_SAVED_INT; exit 130" INT
  else
    trap "$prefix; exit 130" INT
  fi

  if ((_AE_HAD_TERM)) && [[ -z "$_AE_SAVED_TERM" ]]; then
    trap '' TERM
  elif ((_AE_HAD_TERM)); then
    trap "$prefix; $_AE_SAVED_TERM; exit 143" TERM
  else
    trap "$prefix; exit 143" TERM
  fi
  _AE_TRAP_ARMED=1
}

_ae_disarm_trap() {
  if ((_AE_TRAP_ARMED == 1)); then
    if ((_AE_HAD_EXIT)); then trap "$_AE_SAVED_EXIT" EXIT; else trap - EXIT; fi
    if ((_AE_HAD_INT)); then trap "$_AE_SAVED_INT" INT; else trap - INT; fi
    if ((_AE_HAD_TERM)); then trap "$_AE_SAVED_TERM" TERM; else trap - TERM; fi
    _AE_TRAP_ARMED=0
  fi
  _AE_SAVED_EXIT=""
  _AE_SAVED_INT=""
  _AE_SAVED_TERM=""
  _AE_HAD_EXIT=0
  _AE_HAD_INT=0
  _AE_HAD_TERM=0
  _ae_cleanup_all
}

_ae_ensure_dirs() {
  local d
  for d in "$OUT_ROOT" "$TEMP_ROOT" "$OUT_ROOT/models" "$OUT_ROOT/logs" "$AE_LOG_DIR"; do
    if ! mkdir -p -- "$d" 2>/dev/null; then
      ui_error "Gagal membuat folder: $d"
      return 1
    fi
    if [[ ! -w "$d" ]]; then
      ui_error "Folder tidak bisa ditulis: $d"
      return 1
    fi
  done
  return 0
}

ae_cleanup_stale_temps() {
  [[ -d "$TEMP_ROOT" ]] || return 0
  local d
  while IFS= read -r -d '' d; do
    rm -rf -- "$d"
  done < <(find "$TEMP_ROOT" -mindepth 1 -maxdepth 1 -type d -name 'ae.*' -print0 2>/dev/null)
  return 0
}

_ae_new_scratch() {
  local d
  d=$(mktemp -d "$TEMP_ROOT/ae.XXXXXX" 2>/dev/null) || return 1
  _AE_SCRATCH_DIRS+=("$d")
  printf '%s' "$d"
}

_ae_release_scratch() {
  local d="$1" i
  rm -rf -- "$d" 2>/dev/null
  for i in "${!_AE_SCRATCH_DIRS[@]}"; do
    if [[ "${_AE_SCRATCH_DIRS[$i]}" == "$d" ]]; then
      unset "_AE_SCRATCH_DIRS[$i]"
    fi
  done
  return 0
}

_ae_abspath() {
  local p="$1" base_dir
  local b=$(basename -- "$p")
  local d=$(dirname -- "$p")
  base_dir=$(cd -P -- "$d" 2>/dev/null && pwd -P) || base_dir="$d"
  printf '%s/%s' "$base_dir" "$b"
}

_ae_inside_out() {
  local p
  p=$(_ae_abspath "$1")
  [[ "$p" == "$OUT_ROOT" || "$p" == "$OUT_ROOT"/* ]]
}

_ae_supported_ext() {
  local name="${1##*/}" ext
  [[ "$name" == *.* ]] || return 1
  ext="${name##*.}"
  case "${ext,,}" in
    mp4|mkv|mov|avi|webm|flv|wmv|m4v|3gp|ts|mts|m2ts) return 0 ;;
    *) return 1 ;;
  esac
}

ae_probe() {
  local video="$1" streams
  AE_DURATION=""
  AE_HAS_AUDIO=0
  AE_DURATION_OK=0
  [[ -f "$video" && -r "$video" ]] || return 1
  AE_DURATION=$(ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 -- "$video" 2>/dev/null | head -n 1)
  streams=$(ffprobe -v error -select_streams a -show_entries stream=codec_type \
    -of csv=p=0 -- "$video" 2>/dev/null)
  if printf '%s\n' "$streams" | grep -qi '^audio$'; then AE_HAS_AUDIO=1; fi
  [[ -n "$AE_DURATION" && "$AE_DURATION" != "N/A" ]] || return 1
  awk -v d="$AE_DURATION" 'BEGIN { exit !(d > 0) }' || return 1
  # Durasi terbaca: bedakan file rusak/tidak bisa dibaca dari file tanpa audio.
  AE_DURATION_OK=1
  [[ "$AE_HAS_AUDIO" -eq 1 ]]
}

ae_valid_mp3() {
  local file="$1" codec duration
  [[ -f "$file" && -s "$file" ]] || return 1
  codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name \
    -of default=noprint_wrappers=1:nokey=1 -- "$file" 2>/dev/null | head -n 1)
  [[ "$codec" == "mp3" ]] || return 1
  duration=$(ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 -- "$file" 2>/dev/null | head -n 1)
  [[ -n "$duration" && "$duration" != "N/A" ]] || return 1
  awk -v d="$duration" 'BEGIN { exit !(d > 0) }'
}

ae_valid_txt() {
  local file="$1" line trimmed count=0 real=0
  [[ -f "$file" && -s "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    trimmed="${line#"${line%%[![:space:]]*}"}"
    trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
    [[ -z "$trimmed" ]] && continue
    ((count++))
    [[ "$trimmed" == "[tidak terdengar]" ]] || real=1
  done < "$file"
  ((count > 0 && real == 1))
}

_ae_extract_audio() {
  local video="$1" dest="$2"
  if ffmpeg -nostdin -i "$video" -vn -c:a libmp3lame -b:a 192k "$dest" \
    >/dev/null 2>&1 && ae_valid_mp3 "$dest"; then
    return 0
  fi
  log_info "AE fallback bitrate q:a 2 video=$video"
  rm -f -- "$dest"
  if ffmpeg -nostdin -i "$video" -vn -c:a libmp3lame -q:a 2 "$dest" \
    >/dev/null 2>&1 && ae_valid_mp3 "$dest"; then
    return 0
  fi
  return 1
}

_ae_json_value() {
  local json="$1" key="$2" value=""
  if [[ "$json" =~ \"$key\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    value="${BASH_REMATCH[1]}"
  elif [[ "$json" =~ \"$key\"[[:space:]]*:[[:space:]]*(true|false|[0-9]+) ]]; then
    value="${BASH_REMATCH[1]}"
  fi
  printf '%s' "$value"
}

_ae_output_stem() {
  local video="$1" base stem candidate n=2 key ext owner
  base=$(basename -- "$video")
  stem="${base%.*}"
  candidate="$OUT_ROOT/$stem"
  while :; do
    local taken=0
    for ext in mp3 txt; do
      key="$candidate.$ext"
      owner="${AE_OUTPUT_OWNER[$key]:-}"
      if [[ -n "$owner" && "$owner" != "$video" ]]; then taken=1; break; fi
    done
    ((taken == 0)) && break
    candidate="$OUT_ROOT/${stem}_$n"
    ((n++))
  done
  printf '%s' "$candidate"
}

_ae_backup_file() {
  local file="$1" ts backup n=1
  [[ -e "$file" ]] || return 0
  ts=$(date '+%Y%m%d%H%M%S')
  backup="$file.bak.$ts"
  while [[ -e "$backup" ]]; do
    backup="$file.bak.${ts}_$n"
    ((n++))
  done
  if mv -- "$file" "$backup"; then
    printf 'Backup: %s\n' "$backup"
    log_info "AE backup $file -> $backup"
    return 0
  fi
  ui_error "Gagal membackup output lama: $file"
  return 1
}

_ae_ask_existing() {
  local mp3="$1" txt="$2" invalid="$3" answer
  # Prompt harus ke stderr: caller menangkap stdout lewat $(...) sebagai jawaban.
  printf '\n%s\n' 'Output sudah ada. Pilih tindakan:' >&2
  printf '%s\n' '1) Lewati' '2) Proses ulang (backup dulu)' '3) Batal' >&2
  if ((invalid)); then
    ui_warn "Ada output lama yang tidak valid; tidak akan ditimpa tanpa proses ulang." >&2
  fi
  printf 'Pilih [1/2/3]: ' >&2
  IFS= read -r answer
  case "$answer" in
    1|l|L|lewati|Lewati) printf 'no' ;;
    2|u|U|y|Y|ya|Ya|proses|Proses) printf 'yes' ;;
    3|b|B|batal|Batal|cancel) printf 'cancel' ;;
    *) printf 'no' ;;
  esac
}

_ae_stored_key_usable() {
  local key
  [[ -f "$AE_GEMINI_KEY_FILE" && -r "$AE_GEMINI_KEY_FILE" ]] || return 1
  key=$(<"$AE_GEMINI_KEY_FILE") || return 1
  [[ -n "${key//[[:space:]]/}" ]]
}

_ae_save_key() {
  local key="$1" key_dir key_tmp
  key_dir=$(dirname -- "$AE_GEMINI_KEY_FILE")
  if ! mkdir -p -- "$key_dir"; then
    ui_error "Gagal membuat folder API key Gemini: $key_dir" >&2
    return 1
  fi
  if [[ -d "$AE_GEMINI_KEY_FILE" ]]; then
    ui_error "Path API key Gemini adalah folder, bukan file: $AE_GEMINI_KEY_FILE" >&2
    return 1
  fi
  if ! key_tmp=$(mktemp "$AE_GEMINI_KEY_FILE.tmp.XXXXXX"); then
    ui_error "Gagal membuat file sementara API key Gemini." >&2
    return 1
  fi
  if ! (umask 077; printf '%s\n' "$key" > "$key_tmp") \
    || ! chmod 600 -- "$key_tmp" \
    || ! mv -f -- "$key_tmp" "$AE_GEMINI_KEY_FILE"; then
    rm -f -- "$key_tmp" 2>/dev/null || :
    ui_error "Gagal menyimpan API key Gemini." >&2
    return 1
  fi
}

_ae_prompt_new_key() {
  local key=""
  printf '%s\n' 'API key Google AI Studio: ' >&2
  IFS= read -rs key
  printf '\n' >&2
  # Spasi saja dianggap kosong: jangan pernah memakai key tak berguna.
  if [[ -z "${key//[[:space:]]/}" ]]; then
    key=""
  fi
  if [[ -n "$key" ]]; then
    _ae_save_key "$key"
    return
  fi
  if _ae_stored_key_usable; then
    chmod 600 -- "$AE_GEMINI_KEY_FILE" 2>/dev/null || :
    return 0
  fi
  if [[ -s "$AE_GEMINI_KEY_FILE" ]]; then
    ui_error "API key Gemini tersimpan kosong. Tempel key baru di prompt." >&2
  else
    ui_error "Belum ada API key Gemini. Tempel key di prompt atau jalankan ulang menu 12." >&2
  fi
  return 1
}

_ae_prompt_engine() {
  local choice key=""
  printf '\n%s\n' 'Mesin transkripsi: 1) Gemini API  2) Gemini API (ganti key)' >&2
  printf 'Pilih mesin [1]: ' >&2
  IFS= read -r choice
  [[ -z "$choice" ]] && choice=1
  case "$choice" in
    1)
      if _ae_stored_key_usable; then
        if ! chmod 600 -- "$AE_GEMINI_KEY_FILE"; then
          ui_error "Gagal mengamankan izin API key Gemini (0600)." >&2
          return 1
        fi
        printf '%s\n' 'Memakai API key Gemini tersimpan.' >&2
        printf 'gemini'
        return 0
      fi
      _ae_prompt_new_key || return 1
      ;;
    2)
      printf '%s\n' 'API key Google AI Studio baru [Enter = batal]: ' >&2
      IFS= read -rs key
      printf '\n' >&2
      if [[ -z "${key//[[:space:]]/}" ]]; then
        ui_error "Ganti key dibatalkan; key lama tidak diubah." >&2
        unset key
        return 1
      fi
      _ae_save_key "$key" || { unset key; return 1; }
      unset key
      ;;
    *)
      ui_error "Pilihan mesin tidak valid: $choice" >&2
      return 1
      ;;
  esac
  printf 'gemini'
}

_ae_transcribe() {
  local engine="$1" scratch="$2" audio="$3" txt_tmp="$4" json raw rc ok_val reason msg
  if [[ "$engine" != "gemini" ]]; then
    ui_error "Mesin transkripsi tidak didukung: $engine"
    log_error "AE unsupported engine=$engine"
    return 2
  fi
  if [[ ! -f "$AE_GEMINI_SRC" ]]; then
    ui_error "Backend transcribe_gemini.py tidak ditemukan: $AE_GEMINI_SRC"
    log_error "AE backend missing $AE_GEMINI_SRC"
    return 2
  fi
  # Key dibaca backend dari file 0600; jangan pernah lewat argv/env.
  raw=$(python3 "$AE_GEMINI_SRC" --audio "$audio" \
    --key-file "$AE_GEMINI_KEY_FILE" --out-txt "$txt_tmp" \
    2>"$scratch/stderr.log")
  rc=$?
  json="${raw##*$'\n'}"
  if ((rc != 0)); then
    msg=$(_ae_json_value "$json" message)
    ui_error "Transkripsi gagal (exit $rc): ${msg:-lihat logs untuk detail}."
    log_error "AE transcribe rc=$rc json=$json"
    return 2
  fi
  ok_val=$(_ae_json_value "$json" ok)
  reason=$(_ae_json_value "$json" reason)
  if [[ "$ok_val" == "true" ]]; then
    msg=$(_ae_json_value "$json" message)
    if [[ -n "$msg" ]]; then
      printf '  CATATAN: %s\n' "$msg" >&2
    fi
    if [[ -f "$txt_tmp" ]] && ae_valid_txt "$txt_tmp"; then
      printf '%s' "$txt_tmp"
      return 0
    fi
    ui_error "Hasil transkripsi kosong atau hanya placeholder; TXT tidak disimpan."
    log_error "AE invalid txt json=$json"
    return 2
  fi
  if [[ "$reason" == "NO_SPEECH" ]]; then
    printf 'NO_SPEECH'
    return 0
  fi
  msg=$(_ae_json_value "$json" message)
  ui_error "Transkripsi gagal (${reason:-ERROR}): ${msg:-status tidak dikenal}."
  log_error "AE transcribe error json=$json"
  return 2
}

ae_process() {
  local video="$1" job="${2:-both}" reprocess="${3:-ask}" engine="${4:-gemini}"
  local name base stem scratch mp3_tmp audio_tmp txt_tmp
  local final_mp3 final_txt need_mp3=0 need_txt=0
  local existing=0 invalid=0 choice mp3_ok=0 fail_before=$AE_FAIL

  AE_TOTAL=$((AE_TOTAL + 1))
  _ae_ensure_dirs || { AE_FAIL=$((AE_FAIL + 1)); return 1; }

  name=$(basename -- "$video")
  base="${name%.*}"
  if ! ae_probe "$video"; then
    if [[ "${AE_DURATION_OK:-0}" -eq 1 && "${AE_HAS_AUDIO:-0}" -eq 0 ]]; then
      ui_error "Video tidak memiliki stream audio: $name"
    else
      ui_error "Gagal membaca video: $name"
    fi
    AE_FAIL=$((AE_FAIL + 1))
    log_error "AE probe failed video=$video"
    return 1
  fi
  printf '\n%s\n' "Memproses: $name (durasi ${AE_DURATION}s)"

  case "$job" in
    both) need_mp3=1; need_txt=1 ;;
    mp3) need_mp3=1 ;;
    txt) need_txt=1 ;;
    *) ui_error "Jenis pekerjaan tidak valid: $job"; AE_FAIL=$((AE_FAIL + 1)); return 1 ;;
  esac

  stem=$(_ae_output_stem "$video")
  final_mp3="$stem.mp3"
  final_txt="$stem.txt"

  if ((need_mp3)) && [[ -e "$final_mp3" ]]; then
    existing=1
    if ae_valid_mp3 "$final_mp3"; then
      printf '  %bMP3 sudah ada dan valid: %s%b\n' "$DIM" "$final_mp3" "$RESET"
    else
      invalid=1
      ui_warn "Output MP3 tidak valid: $final_mp3"
    fi
  fi
  if ((need_txt)) && [[ -e "$final_txt" ]]; then
    existing=1
    if ae_valid_txt "$final_txt"; then
      printf '  %bTXT sudah ada dan valid: %s%b\n' "$DIM" "$final_txt" "$RESET"
    else
      invalid=1
      ui_warn "Output TXT tidak valid: $final_txt"
    fi
  fi

  if ((existing)); then
    choice="$reprocess"
    case "$choice" in
      ask|'') choice=$(_ae_ask_existing "$final_mp3" "$final_txt" "$invalid") ;;
      y|Y|ya|Ya|1|true) choice='yes' ;;
      n|N|tidak|Tidak|0|false) choice='no' ;;
      3|batal|Batal) choice='cancel' ;;
    esac
    case "$choice" in
      yes)
        if ((need_mp3)) && [[ -e "$final_mp3" ]]; then _ae_backup_file "$final_mp3" || { AE_FAIL=$((AE_FAIL + 1)); return 1; }; fi
        if ((need_txt)) && [[ -e "$final_txt" ]]; then _ae_backup_file "$final_txt" || { AE_FAIL=$((AE_FAIL + 1)); return 1; }; fi
        ;;
      cancel)
        printf '  Dibatalkan pengguna: %s\n' "$name"
        AE_SKIP=$((AE_SKIP + 1))
        return 0
        ;;
      *)
        printf '  Dilewati: %s\n' "$name"
        AE_SKIP=$((AE_SKIP + 1))
        log_info "AE skip video=$video"
        return 0
        ;;
    esac
  fi

  scratch=$(_ae_new_scratch) || {
    ui_error "Gagal membuat folder temp di $TEMP_ROOT"
    AE_FAIL=$((AE_FAIL + 1))
    return 1
  }

  if ((need_mp3)); then
    mp3_tmp="$scratch/$base.mp3"
    rm -f -- "$mp3_tmp"
    printf '  Ekstraksi MP3... '
    if _ae_extract_audio "$video" "$mp3_tmp" \
      && mv -f -- "$mp3_tmp" "$final_mp3"; then
      AE_MP3_OK=$((AE_MP3_OK + 1))
      mp3_ok=1
      AE_OUTPUT_OWNER["$final_mp3"]="$video"
      printf '%bOK%b\n' "$GREEN" "$RESET"
      printf '  MP3: %s\n' "$final_mp3"
      log_info "AE mp3 ok path=$final_mp3"
    else
      printf '%bGAGAL%b\n' "$RED" "$RESET"
      ui_error "Ekstraksi MP3 gagal: $name"
      AE_FAIL=$((AE_FAIL + 1))
      log_error "AE mp3 failed video=$video"
    fi
  fi

  if ((need_txt)); then
    local audio_for_txt="" json_result txt_tmp
    if ((mp3_ok)); then
      audio_for_txt="$final_mp3"
    else
      audio_tmp="$scratch/$base.audio.mp3"
      rm -f -- "$audio_tmp"
      printf '  Menyiapkan audio sementara untuk transkripsi... '
      if _ae_extract_audio "$video" "$audio_tmp"; then
        printf '%bOK%b\n' "$GREEN" "$RESET"
        audio_for_txt="$audio_tmp"
      else
        printf '%bGAGAL%b\n' "$RED" "$RESET"
      fi
    fi

    if [[ -z "$audio_for_txt" ]]; then
      ui_error "Tidak ada audio untuk ditranskripsi: $name"
      AE_FAIL=$((AE_FAIL + 1))
    else
      printf '  Transkripsi (Gemini API)... '
      # --out-txt harus fresh: backend tidak menimpa file yang sudah ada.
      txt_tmp="$scratch/$base.$RANDOM.$RANDOM.txt"
      rm -f -- "$txt_tmp"
      json_result=$(_ae_transcribe "$engine" "$scratch" "$audio_for_txt" "$txt_tmp")
      case "$json_result" in
        NO_SPEECH)
          AE_NO_SPEECH=$((AE_NO_SPEECH + 1))
          printf '%bTANPA_UCAPAN%b\n' "$YELLOW" "$RESET"
          printf '  Tidak ada ucapan yang terdeteksi; TXT tidak dibuat: %s\n' "$name"
          log_info "AE no_speech video=$video"
          ;;
        "$txt_tmp")
          if mv -f -- "$txt_tmp" "$final_txt"; then
            AE_TXT_OK=$((AE_TXT_OK + 1))
            AE_OUTPUT_OWNER["$final_txt"]="$video"
            printf '%bOK%b\n' "$GREEN" "$RESET"
            printf '  TXT: %s\n' "$final_txt"
            log_info "AE txt ok path=$final_txt"
          else
            printf '%bGAGAL%b\n' "$RED" "$RESET"
            ui_error "Gagal memindahkan TXT ke output: $final_txt"
            AE_FAIL=$((AE_FAIL + 1))
          fi
          ;;
        *)
          printf '%bGAGAL%b\n' "$RED" "$RESET"
          AE_FAIL=$((AE_FAIL + 1))
          ;;
      esac
    fi
  fi

  if ((need_mp3 && mp3_ok == 0)) && [[ "$job" == "both" ]]; then
    printf '  MP3 gagal tetapi transkripsi tetap diproses.\n'
  fi

  _ae_release_scratch "$scratch"
  ((AE_FAIL > fail_before)) && return 1
  return 0
}

_ae_collect_videos() {
  local dir="$1" f
  AE_VIDEO_FILES=()
  while IFS= read -r -d '' f; do
    if _ae_supported_ext "$f" && ! _ae_inside_out "$f"; then AE_VIDEO_FILES+=("$f"); fi
  done < <(find "$dir" -maxdepth 1 -type f \( \
    -iname '*.mp4' -o -iname '*.mkv' -o -iname '*.mov' -o -iname '*.avi' -o \
    -iname '*.webm' -o -iname '*.flv' -o -iname '*.wmv' -o -iname '*.m4v' -o \
    -iname '*.3gp' -o -iname '*.ts' -o -iname '*.mts' -o -iname '*.m2ts' \) \
    -print0 2>/dev/null | sort -z)
}

ae_batch() {
  local dir="${1:-$AE_INPUT_DIR}" job="${2:-both}" reprocess="${3:-ask}" engine="${4:-gemini}"
  local answer batch_reprocess="$reprocess" f i=0 n before

  if [[ ! -d "$dir" ]]; then
    ui_error "Folder input tidak ditemukan: $dir"
    return 1
  fi
  if _ae_inside_out "$dir"; then
    ui_error "Folder input berada di dalam folder output: $dir"
    return 1
  fi

  _ae_collect_videos "$dir"

  if [[ ${#AE_VIDEO_FILES[@]} -eq 0 ]]; then
    ui_warn "Tidak ada file video yang didukung di: $dir"
    return 0
  fi

  if [[ "$batch_reprocess" == "ask" ]]; then
    printf '\nProses ulang semua output yang ada? [y/N]: '
    IFS= read -r answer
    case "$answer" in
      y|Y|ya|Ya) batch_reprocess='yes' ;;
      *) batch_reprocess='no' ;;
    esac
  fi

  n=${#AE_VIDEO_FILES[@]}
  printf '\nDitemukan %d file video.\n' "$n"
  for f in "${AE_VIDEO_FILES[@]}"; do
    i=$((i + 1))
    printf '\n[%d/%d] %s\n' "$i" "$n" "$(basename -- "$f")"
    before=$AE_FAIL
    ae_process "$f" "$job" "$batch_reprocess" "$engine"
    if ((AE_FAIL > before)); then AE_BATCH_FAILED+=("$f"); fi
  done
  _ae_print_summary
  return 0
}

_ae_print_summary() {
  local f
  printf '\n%s\n' '=== RINGKASAN ==='
  printf 'TOTAL=%d BERHASIL_MP3=%d BERHASIL_TXT=%d TANPA_UCAPAN=%d DILEWATI=%d GAGAL=%d\n' \
    "$AE_TOTAL" "$AE_MP3_OK" "$AE_TXT_OK" "$AE_NO_SPEECH" "$AE_SKIP" "$AE_FAIL"
  if [[ ${#AE_BATCH_FAILED[@]} -gt 0 ]]; then
    printf 'DAFTAR_GAGAL:\n'
    for f in "${AE_BATCH_FAILED[@]}"; do printf 'GAGAL: %s\n' "$f"; done
  fi
}

_ae_module_body() {
  local mode="" job_choice="" job="" video="" input_dir="" engine="" rc n=0 i=0 pil="" pil_num=0
  ui_header
  ui_section "AUDIO EXTRACTOR + TRANSCRIBER"
  printf '\n%s\n' 'Pilih mode: 1) Single Video  2) Batch Folder  0) Kembali'
  printf 'Pilih mode: '
  IFS= read -r mode
  case "$mode" in
    0) return 0 ;;
    1|2) ;;
    *) ui_error "Pilihan mode tidak valid."; return 1 ;;
  esac

  printf '\n%s\n' 'Pilih pekerjaan: 1) MP3 + TXT  2) MP3 saja  3) TXT saja  0) Kembali'
  printf 'Pilih pekerjaan: '
  IFS= read -r job_choice
  case "$job_choice" in
    0) return 0 ;;
    1) job='both' ;;
    2) job='mp3' ;;
    3) job='txt' ;;
    *) ui_error "Pilihan pekerjaan tidak valid."; return 1 ;;
  esac

  if [[ "$job" != "mp3" ]]; then
    engine=$(_ae_prompt_engine) || return 1
  fi

  ae_reset_state
  if [[ "$mode" == "1" ]]; then
    printf '%b' "${CYAN}${BOLD}Path video [Enter = otomatis dari ${AE_INPUT_DIR}]: ${RESET}"
    IFS= read -r video
    if [[ -z "$video" ]]; then
      _ae_collect_videos "$AE_INPUT_DIR"
      n=${#AE_VIDEO_FILES[@]}
      if ((n == 0)); then
        ui_error "Tidak ada video di folder: $AE_INPUT_DIR"
        return 1
      elif ((n == 1)); then
        video="${AE_VIDEO_FILES[0]}"
      else
        printf '\nDitemukan %d video di: %s\n' "$n" "$AE_INPUT_DIR"
        for i in "${!AE_VIDEO_FILES[@]}"; do
          printf '  [%d] %s\n' "$((i + 1))" "$(basename -- "${AE_VIDEO_FILES[i]}")"
        done
        printf 'Pilih video [1-%d]: ' "$n"
        IFS= read -r pil
        [[ -z "$pil" ]] && pil=1
        if [[ ! "$pil" =~ ^[0-9]+$ ]]; then
          ui_error "Pilihan video tidak valid: $pil"
          return 1
        fi
        pil_num=$((10#$pil))
        if ((pil_num < 1 || pil_num > n)); then
          ui_error "Pilihan video tidak valid: $pil"
          return 1
        fi
        video="${AE_VIDEO_FILES[pil_num-1]}"
      fi
    fi
    if [[ ! -f "$video" || ! -r "$video" ]]; then
      ui_error "File video tidak ditemukan atau tidak bisa dibaca: $video"
      return 1
    fi
    if ! _ae_supported_ext "$video"; then
      ui_error "Ekstensi video tidak didukung: $video"
      return 1
    fi
    if _ae_inside_out "$video"; then
      ui_error "Video berada di dalam folder output audio-extractor: $video"
      return 1
    fi
    ae_process "$video" "$job" ask "$engine"
    rc=$?
  else
    printf '%b' "${CYAN}${BOLD}Folder video [${AE_INPUT_DIR}]: ${RESET}"
    IFS= read -r input_dir
    [[ -z "$input_dir" ]] && input_dir="$AE_INPUT_DIR"
    if [[ ! -d "$input_dir" ]]; then
      ui_error "Folder input tidak ditemukan: $input_dir"
      return 1
    fi
    if _ae_inside_out "$input_dir"; then
      ui_error "Folder input berada di dalam folder output audio-extractor: $input_dir"
      return 1
    fi
    ae_batch "$input_dir" "$job" ask "$engine"
    rc=$?
  fi
  _ae_print_summary
  return "$rc"
}

module_audio_extractor() {
  if ! _ae_ensure_dirs; then
    ui_error "Folder output tidak siap. Periksa izin akses: $OUT_ROOT"
    ui_pause
    return 1
  fi
  ae_cleanup_stale_temps
  _ae_arm_trap
  _ae_module_body
  local rc=$?
  _ae_disarm_trap
  ui_pause
  return "$rc"
}
