#!/usr/bin/env python3
"""Transkripsi audio lewat OpenRouter Speech-to-Text API.

Backend ini memakai Python Termux dan stdlib saja. API key dibaca dari file
0600 yang ditentukan lewat --key-file; key tidak pernah masuk argv, env, atau
log. Satu baris JSON ditulis ke stdout.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/audio/transcriptions"
DEFAULT_MODEL = "openai/whisper-1"
MAX_ATTEMPTS = 3
RETRY_DELAYS = (2, 5)
PLACEHOLDERS = {"[tidak terdengar]", "[no speech]", "no speech", "no_speech", "no_speech."}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe audio via OpenRouter STT")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--out-txt", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    return parser.parse_args()


def _read_key(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError("key file tidak ditemukan")
    key = p.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError("key kosong")
    if "\n" in key or "\r" in key:
        raise ValueError("key multi-baris tidak didukung")
    return key


def _is_no_speech(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    if not lines:
        return True
    if all(ln.lower().strip(" .:*_[]") in PLACEHOLDERS or ln.lower() in PLACEHOLDERS for ln in lines):
        return True
    return False


def _build_multipart(audio_path: str, model: str, boundary: str) -> tuple[bytes, str]:
    audio_bytes = Path(audio_path).read_bytes()
    mime = mimetypes.guess_type(audio_path)[0] or "audio/mpeg"
    filename = Path(audio_path).name
    parts: list[bytes] = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="model"\r\n\r\n')
    parts.append(model.encode() + b"\r\n")
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    parts.append(f"Content-Type: {mime}\r\n\r\n".encode())
    parts.append(audio_bytes)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _http_error_message(code: int, body: str) -> str:
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        data = {}
    err = data.get("error") if isinstance(data, dict) else None
    msg = ""
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("detail") or "")
    elif isinstance(err, str):
        msg = err
    if not msg:
        msg = body.strip()[:200]
    return msg


def _request_once(audio: str, key: str, model: str) -> dict:
    boundary = uuid.uuid4().hex
    body, content_type = _build_multipart(audio, model, boundary)
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": content_type,
            "HTTP-Referer": "https://termux-media-downloader",
            "X-OpenRouter-Title": "Termux Media Downloader",
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
        msg = _http_error_message(exc.code, err_body)
        if exc.code == 401:
            raise RuntimeError(f"INVALID_KEY: {msg or 'API key OpenRouter tidak valid.'}")
        if exc.code in (402, 429):
            raise RuntimeError(f"QUOTA_EXHAUSTED: {msg or 'Kuota OpenRouter habis.'}")
        if exc.code == 503:
            raise RuntimeError(f"SERVICE_UNAVAILABLE: {msg or 'Layanan OpenRouter sibuk.'}")
        raise RuntimeError(f"HTTP_{exc.code}: {msg or 'Permintaan OpenRouter gagal.'}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"NETWORK_ERROR: {exc.reason}")
    except TimeoutError:
        raise RuntimeError("NETWORK_ERROR: waktu habis saat menghubungi OpenRouter.")
    except Exception as exc:  # noqa: BLE001
        # Redaksi key bila muncul di pesan
        text = str(exc)
        if key and key in text:
            text = text.replace(key, "[REDACTED]")
        raise RuntimeError(f"ERROR: {text}")

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        raise RuntimeError("BAD_RESPONSE: OpenRouter mengembalikan respons yang bukan JSON.")

    if not isinstance(data, dict):
        raise RuntimeError("BAD_RESPONSE: Bentuk respons OpenRouter tidak dikenal.")
    text = data.get("text")
    if not isinstance(text, str):
        # Beberapa provider mungkin mengembalikan field lain
        text = data.get("transcription") or data.get("output") or ""
        if not isinstance(text, str):
            text = ""
    text = text.strip()
    if _is_no_speech(text):
        return {"ok": False, "reason": "NO_SPEECH", "language": "", "duration": 0.0,
                "segments": 0, "text_chars": 0, "model": model}
    # Tulis TXT
    return {"ok": True, "text": text, "language": "", "duration": 0.0,
            "segments": 1, "text_chars": len(text), "model": model}


def main() -> int:
    args = _parse_args()
    args_out_txt = args.out_txt
    audio = args.audio
    key_file = args.key_file
    out_txt = args.out_txt
    model = args.model

    try:
        key = _read_key(key_file)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "reason": "INVALID_KEY",
                          "message": f"API key OpenRouter tidak bisa dibaca: {exc}"}))
        return 1

    last_exc: Exception | None = None
    result = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = _request_once(audio, key, model)
            break
        except RuntimeError as exc:
            last_exc = exc
            msg = str(exc)
            # Retry hanya untuk 503 / service unavailable
            if msg.startswith("SERVICE_UNAVAILABLE") and attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAYS[attempt - 1])
                continue
            # Tidak retry untuk kuota/key/jaringan
            break
    else:
        result = None

    if result is None:
        exc = last_exc
        msg = str(exc) if exc else "Permintaan OpenRouter gagal."
        if msg.startswith("INVALID_KEY:"):
            reason = "INVALID_KEY"
            user_msg = msg.split(":", 1)[1].strip() or "API key OpenRouter tidak valid."
        elif msg.startswith("QUOTA_EXHAUSTED:"):
            reason = "QUOTA_EXHAUSTED"
            user_msg = msg.split(":", 1)[1].strip() or "Kuota OpenRouter habis."
        elif msg.startswith("SERVICE_UNAVAILABLE:"):
            reason = "SERVICE_UNAVAILABLE"
            user_msg = msg.split(":", 1)[1].strip() or "Layanan OpenRouter sibuk."
        elif msg.startswith("NETWORK_ERROR:"):
            reason = "NETWORK_ERROR"
            user_msg = msg.split(":", 1)[1].strip() or "Tidak bisa terhubung ke OpenRouter."
        elif msg.startswith("BAD_RESPONSE:"):
            reason = "BAD_RESPONSE"
            user_msg = msg.split(":", 1)[1].strip() or "Respons OpenRouter tidak bisa dibaca."
        else:
            reason = "ERROR"
            user_msg = msg
        if key and key in user_msg:
            user_msg = user_msg.replace(key, "[REDACTED]")
        print(json.dumps({"ok": False, "reason": reason, "message": user_msg,
                          "model": model}))
        return 1

    if not result.get("ok"):
        print(json.dumps({"ok": False, "reason": result.get("reason", "NO_SPEECH"),
                          "language": result.get("language", ""),
                          "duration": result.get("duration", 0.0),
                          "segments": result.get("segments", 0),
                          "text_chars": result.get("text_chars", 0),
                          "model": model}))
        return 0

    text = result["text"]
    # Tulis TXT secara atomik
    tmp = out_txt + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        os.replace(tmp, out_txt)
    except OSError as exc:
        try:
            os.remove(tmp)
        except OSError:
            pass
        print(json.dumps({"ok": False, "reason": "ERROR",
                          "message": f"Gagal menulis TXT: {exc}", "model": model}))
        return 1

    print(json.dumps({"ok": True, "language": result.get("language", ""),
                      "duration": result.get("duration", 0.0),
                      "segments": result.get("segments", 1),
                      "text_chars": result.get("text_chars", len(text)),
                      "model": model}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())