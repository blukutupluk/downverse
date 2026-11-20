#!/usr/bin/env bash
# Test harness untuk modul download massal. Menjalankan fungsi dengan stub
# run_ytdlp/UI/logging agar tidak menyentuh backend atau cookies asli.

BASE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$BASE_DIR/modules/bulk.sh"

# --- stub ---
run_ytdlp() {
  printf '%s\n' "$*" >> "$CALLS"
  case " $* " in *FAIL*) return 1 ;; esac
  return 0
}
ui_header() { :; }
ui_section() { :; }
ui_item() { :; }
ui_error() { printf 'ERROR: %s\n' "$*" >&2; }
ui_ok() { :; }
ui_warn() { :; }
ui_pause() { :; }
log_info() { :; }
log_error() { :; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fails=0
ok() { printf 'OK: %s\n' "$1"; }
bad() {
  printf 'FAIL: %s\n' "$1"
  [[ -n "${2:-}" ]] && printf '     %s\n' "$2"
  fails=$((fails + 1))
}
line_count() { [[ -f "$1" ]] && wc -l < "$1" || printf '0\n'; }

# --- test 1: parsing daftar ---
test_parse_list() {
  local f="$TMP/list.txt" out expected
  cat > "$f" <<'EOF'
https://www.facebook.com/reel/111/

  # komentar dengan spasi
bukan-url
https://www.facebook.com/reel/111/
   https://www.youtube.com/watch?v=abc
EOF
  out="$(bulk_parse_list "$f")"
  expected=$'https://www.facebook.com/reel/111/\nhttps://www.youtube.com/watch?v=abc'
  if [[ "$out" != "$expected" ]]; then
    bad test_parse_list "dapat=$(printf '%q' "$out")"
    return
  fi
  # Pastikan baris invalid benar-benar tidak sampai ke backend.
  CALLS="$TMP/list.calls"
  : > "$CALLS"
  rm -f "$f.done"
  bulk_run 'Facebook' "$TMP/out" '' 1 "$f" > /dev/null
  if (( $(line_count "$CALLS") == 2 )) \
    && ! grep -q 'bukan-url' "$CALLS" \
    && ! grep -q -- '#' "$CALLS"; then
    ok test_parse_list
  else
    bad test_parse_list "argumen backend: $(printf '%q' "$(< "$CALLS")")"
  fi
}

# --- test 2: sukses ---
test_bulk_run_success() {
  local f="$TMP/success.txt" summary rc calls done
  printf '%s\n' \
    'https://www.facebook.com/reel/111/' \
    'https://www.youtube.com/watch?v=abc' > "$f"
  CALLS="$TMP/success.calls"
  : > "$CALLS"
  summary="$(bulk_run 'Facebook' "$TMP/out" '' 1 "$f")"
  rc=$?
  calls="$(line_count "$CALLS")"
  done="$(line_count "$f.done")"
  if ((rc == 0 && calls == 2 && done == 2)) \
    && grep -q 'TOTAL=2 BERHASIL=2 GAGAL=0 DILEWATI=0' <<< "$summary" \
    && grep -q -- '--no-playlist' "$CALLS" \
    && grep -Fq -- '-f bv*+ba/b --merge-output-format mp4' "$CALLS"; then
    ok test_bulk_run_success
  else
    bad test_bulk_run_success "rc=$rc calls=$calls done=$done summary=$(printf '%q' "$summary")"
  fi
}

# --- test 3: resume / skip ---
test_bulk_run_resume() {
  local f="$TMP/resume.txt" summary rc calls
  printf '%s\n' \
    'https://www.facebook.com/reel/111/' \
    'https://www.youtube.com/watch?v=abc' > "$f"
  printf '%s\n' \
    'https://www.facebook.com/reel/111/' \
    'https://www.youtube.com/watch?v=abc' > "$f.done"
  CALLS="$TMP/resume.calls"
  : > "$CALLS"
  summary="$(bulk_run 'Facebook' "$TMP/out" '' 1 "$f")"
  rc=$?
  calls="$(line_count "$CALLS")"
  if ((rc == 0 && calls == 0)) && grep -q 'DILEWATI=2' <<< "$summary"; then
    ok test_bulk_run_resume
  else
    bad test_bulk_run_resume "rc=$rc calls=$calls summary=$(printf '%q' "$summary")"
  fi
}

# --- test 4: lanjut setelah gagal ---
test_bulk_run_continue_on_failure() {
  local f="$TMP/fail.txt" summary rc calls done
  printf '%s\n' \
    'https://example.com/FAIL' \
    'https://example.com/ok' > "$f"
  CALLS="$TMP/fail.calls"
  : > "$CALLS"
  summary="$(bulk_run 'Facebook' "$TMP/out" '' 1 "$f")"
  rc=$?
  calls="$(line_count "$CALLS")"
  done="$(line_count "$f.done")"
  if ((rc == 1 && calls == 2 && done == 1)) \
    && grep -q 'GAGAL=1' <<< "$summary" \
    && grep -q 'GAGAL_URL=https://example.com/FAIL' <<< "$summary" \
    && grep -q 'https://example.com/ok' "$f.done"; then
    ok test_bulk_run_continue_on_failure
  else
    bad test_bulk_run_continue_on_failure \
      "rc=$rc calls=$calls done=$done summary=$(printf '%q' "$summary")"
  fi
}

# --- test 5: pemetaan format ---
test_bulk_run_format_mapping() {
  local f="$TMP/fmt.txt"
  printf '%s\n' 'https://example.com/x' > "$f"

  CALLS="$TMP/fmt2.calls"
  : > "$CALLS"
  rm -f "$f.done"
  bulk_run 'Facebook' "$TMP/out" '' 2 "$f" > /dev/null

  CALLS="$TMP/fmt3.calls"
  : > "$CALLS"
  rm -f "$f.done"
  bulk_run 'Facebook' "$TMP/out" '' 3 "$f" > /dev/null

  if grep -q -- '-x --audio-format mp3' "$TMP/fmt2.calls" \
    && grep -q -- '-f best/b' "$TMP/fmt3.calls"; then
    ok test_bulk_run_format_mapping
  else
    bad test_bulk_run_format_mapping \
      "fmt2=$(printf '%q' "$(< "$TMP/fmt2.calls")") fmt3=$(printf '%q' "$(< "$TMP/fmt3.calls")")"
  fi
}

# --- test 6: daftar tanpa URL valid ---
test_bulk_run_empty_list() {
  local f="$TMP/empty.txt" summary rc
  printf '%s\n' '# hanya komentar' '' 'bukan-url' > "$f"
  CALLS="$TMP/empty.calls"
  : > "$CALLS"
  summary="$(bulk_run 'Facebook' "$TMP/out" '' 1 "$f" 2>&1)"
  rc=$?
  if ((rc == 1)) && (( $(line_count "$CALLS") == 0 )) \
    && grep -qi 'tidak ada url valid' <<< "$summary"; then
    ok test_bulk_run_empty_list
  else
    bad test_bulk_run_empty_list "rc=$rc summary=$(printf '%q' "$summary")"
  fi
}

test_parse_list
test_bulk_run_success
test_bulk_run_resume
test_bulk_run_continue_on_failure
test_bulk_run_format_mapping
test_bulk_run_empty_list

if ((fails == 0)); then
  printf '\nSemua test lolos.\n'
  exit 0
fi
printf '\n%d test gagal.\n' "$fails"
exit 1
