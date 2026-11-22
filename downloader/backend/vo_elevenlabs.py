#!/usr/bin/env python3
"""Ubah transkrip .txt menjadi skrip voiceover ElevenLabs v4 dengan tag ekspresi.

Memakai Gemini (text generation) lewat API key yang sama seperti transkripsi.
Tag [whisper]/bisik tidak digunakan.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "gemini-3.5-flash"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

PROMPT = """Kamu adalah editor naskah voiceover untuk ElevenLabs v4.

Tugas: ubah transkrip berikut menjadi skrip voiceover ElevenLabs v4.
Aturan:
- Jangan menerjemahkan; pertahankan bahasa asli.
- Jangan mengarang fakta baru; hanya tambahkan tag ekspresi dan pemenggalan.
- Tag ekspresi diletakkan di awal segmen yang relevan, dalam tanda kurung siku, contoh: [excited], [sad], [angry], [curious], [surprised], [calm], [serious], [emphasis], [pause], [shouting].
- JANGAN gunakan tag bisik/whisper (seperti [whispers], [whisper], [bisik]).
- Maksimal 1-2 kalimat per baris/blok.
- Jangan tambahkan penjelasan, markdown, atau komentar; output hanya naskah VO.
- Jika transkrip kosong atau hanya placeholder, kembalikan teks aslinya tanpa tag.

Transkrip:
{transcript}
"""


def read_key(path: str) -> str:
    p = Path(path)
    key = p.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError("key kosong")
    return key


def call_gemini(key: str, transcript: str) -> str:
    url = ENDPOINT.format(model=MODEL)
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(transcript=transcript)}]}],
        "generationConfig": {"temperature": 0.4},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise RuntimeError(f"HTTP {exc.code}: {err_body[:300]}")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(str(exc))

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        raise RuntimeError("Respons bukan JSON")
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Respons Gemini tidak berisi teks")
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    key = read_key(args.key_file)
    in_dir = Path(args.input_dir)
    files = sorted(in_dir.glob("*.txt"))
    # Skip backup files
    files = [f for f in files if not f.name.endswith(".bak") and ".bak." not in f.name]

    if args.limit and args.limit > 0:
        files = files[: args.limit]

    print(f"Memproses {len(files)} file .txt")
    for i, f in enumerate(files, 1):
        try:
            original = f.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[{i}/{len(files)}] GAGAL baca {f.name}: {exc}")
            continue
        if not original.strip():
            print(f"[{i}/{len(files)}] LEWATI (kosong): {f.name}")
            continue
        if ("[" in original) and not args.force:
            print(f"[{i}/{len(files)}] LEWATI (sudah ada tag): {f.name}")
            continue
        # Backup
        backup = f.with_name(f.name + f".bak.vo-{int(time.time())}")
        try:
            backup.write_text(original, encoding="utf-8")
        except OSError as exc:
            print(f"[{i}/{len(files)}] GAGAL backup {f.name}: {exc}")
            continue
        try:
            vo = call_gemini(key, original)
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}/{len(files)}] GAGAL Gemini {f.name}: {exc}")
            # restore? leave backup; do not overwrite
            continue
        # Hapus tag whisper/bisik jika model bandel
        for bad in ("[whispers]", "[whisper]", "[bisik]", "[bisik-bisik]"):
            vo = vo.replace(bad, "")
        try:
            f.write_text(vo + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"[{i}/{len(files)}] GAGAL tulis {f.name}: {exc}")
            continue
        print(f"[{i}/{len(files)}] OK: {f.name} ({len(vo)} char)")
        # Jeda kecil agar tidak kena rate limit
        time.sleep(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())