#!/usr/bin/env bash
# Instalasi eksplisit dependency + model STT lokal untuk menu Audio Extractor + Transcriber.
# Skrip ini TIDAK dipanggil otomatis; jalankan manual dari Termux bila dibutuhkan.
# Semua operasi pip/python terjadi di dalam Debian PRoot memakai venv khusus,
# bukan Python Termux dan bukan sistem Debian.
set -euo pipefail

VENV="/opt/media-downloader-venv"
VENV_PIP="$VENV/bin/pip"
VENV_PYTHON="$VENV/bin/python"
PROOT_DISTRO="${PROOT_DISTRO:-debian}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/storage/7544-8C33/output}"
MODEL_SIZE="base"

usage() {
  cat <<'EOF'
Penggunaan: bash downloader/backend/install_whisper_model.sh [--model-size SIZE]

Opsi:
  --model-size SIZE  Ukuran model faster-whisper (default: base).
  -h, --help         Tampilkan bantuan ini.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-size)
      [[ $# -ge 2 ]] || { echo "Error: --model-size butuh nilai." >&2; exit 2; }
      MODEL_SIZE="$2"
      shift 2
      ;;
    --model-size=*)
      MODEL_SIZE="${1#*=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: argumen tidak dikenal: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

# Batasi nama agar repo/path tetap aman dan sesuai pola Systran/faster-whisper-<size>.
if [[ ! "$MODEL_SIZE" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "Error: --model-size tidak valid: $MODEL_SIZE" >&2
  exit 2
fi

MODEL_REPO="Systran/faster-whisper-${MODEL_SIZE}"
MODEL_DIR="$OUTPUT_ROOT/audio-extractor/models/faster-whisper-${MODEL_SIZE}"

# Cetak estimasi SEBELUM melakukan pekerjaan apa pun.
printf 'Estimasi unduhan: ~90 MB wheel + ~138 MB model = ~230 MB total.\n'
printf 'Repo model : %s\n' "$MODEL_REPO"
printf 'Lokasi model: %s\n' "$MODEL_DIR"
printf 'Venv       : %s\n\n' "$VENV"

# PRoot-Distro tidak membawa SD card secara default; bind eksplisit seperti lib/proot.sh.
proot_run() {
  proot-distro login --bind "$OUTPUT_ROOT:$OUTPUT_ROOT" "$PROOT_DISTRO" -- "$@"
}

# Siapkan direktori tujuan dengan aman (host + mount point di Debian).
mkdir -p "$MODEL_DIR"
proot-distro login "$PROOT_DISTRO" -- mkdir -p "$OUTPUT_ROOT"

printf '==> Memasang dependency Python di %s ...\n' "$VENV"
proot_run "$VENV_PIP" install \
  "faster-whisper==1.2.1" \
  "ctranslate2<5" \
  "onnxruntime<2" \
  "tokenizers<1" \
  "av>=11" \
  huggingface-hub \
  tqdm \
  numpy

printf '\n==> Mengunduh model %s ke %s ...\n' "$MODEL_REPO" "$MODEL_DIR"
# SD card (exFAT/FUSE) tidak mendukung flock; filelock fallback (SoftFileLock)
# macet saat acquire di mount ini, dan backend hf_xet juga mandek di PRoot.
# Matikan keduanya untuk satu proses ini; snapshot_download tetap dipakai.
proot_run env HF_HUB_DISABLE_XET=1 "$VENV_PYTHON" -c '
import contextlib
import sys

import huggingface_hub.file_download as hf_download
import huggingface_hub._local_folder as hf_local

# Tidak ada proses paralel yang memakai cache installer ini, jadi lock boleh no-op.
_no_lock = lambda *args, **kwargs: contextlib.nullcontext()
hf_download.WeakFileLock = _no_lock
hf_local.WeakFileLock = _no_lock

from huggingface_hub import snapshot_download

repo_id, local_dir = sys.argv[1], sys.argv[2]
path = snapshot_download(repo_id=repo_id, local_dir=local_dir)
print("MODEL_DOWNLOADED", path)
' "$MODEL_REPO" "$MODEL_DIR"

printf '\nSelesai. Model tersedia di: %s\n' "$MODEL_DIR"
