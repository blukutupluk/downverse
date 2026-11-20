#!/usr/bin/env python3
"""Transkripsi MP3 lewat Gemini Interactions API.

Backend ini memakai Python Termux dan stdlib saja. API key dibaca dari file
0600 yang ditentukan lewat --key-file; key tidak pernah masuk argv, env, atau
log. Satu baris JSON ditulis ke stdout dengan kontrak yang sama seperti
transcribe.py.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

MODEL = "gemini-4-hydrogen"
API_REVISION = "2026-05-20"
BASE_URL = "https://generativelanguage.googleapis.com"
INLINE_LIMIT_BYTES = 18 * 1024 * 1024
MIME = "audio/mp3"
MARKER = "[tidak terdengar]"
TIMEOUT = 180

PROMPT = (
    "Transkrip audio ini kata per kata dengan akurasi tinggi dalam bahasa aslinya.\n"
    "Tulis hanya ucapan yang terdengar, satu kalimat per baris, tanpa timestamp, "
    "nomor, markdown, atau komentar.\n"
    "Jika tidak ada ucapan yang jelas, balas persis: NO_SPEECH"
)


class GeminiError(Exception):
    """Galat yang sudah dipetakan ke reason kontrak JSON."""

    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason
        self.message = message


def load_key(path):
    try:
        with open(path, encoding="utf-8") as handle:
            key = handle.read().strip()
    except OSError:
        raise GeminiError(
            "NO_KEY",
            "API key Gemini belum tersedia. Tempel key dimenu 12 saat prompt muncul.",
        )
    if not key:
        raise GeminiError(
            "NO_KEY",
            "API key Gemini kosong. Tempel key di menu 12 saat prompt muncul.",
        )
    return key


def read_text_response(payload):
    if not isinstance(payload, dict):
        return ""
    for item in payload.get("outputs") or []:
        if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
            return item["text"]
    if payload.get("output_text"):
        return payload["output_text"]
    steps = payload.get("steps") or []
    if steps and isinstance(steps[-1], dict):
        content = steps[-1].get("content") or []
        if content and isinstance(content[0], dict) and content[0].get("text"):
            return content[0]["text"]
    return ""


def clean_transcript(text):
    lines = [line.strip() for line in (text or "").splitlines()]
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
        lines = lines[1:-1]
    lines = [line for line in lines if line]
    joined = "\n".join(lines).strip()
    if joined.upper() == "NO_SPEECH":
        return "no_speech", ""
    if not joined or all(line == MARKER for line in lines):
        return "empty", ""
    return "ok", joined


def _result(ok=False, reason=None, message=None, **extra):
    data = {"ok": bool(ok), "model": MODEL}
    if reason:
        data["reason"] = reason
    if message is not None:
        data["message"] = message
    data.update(extra)
    return data


def _http_error(status, body):
    detail = ""
    try:
        parsed = json.loads(body.decode("utf-8")) if body else {}
        detail = str(parsed.get("error", {}).get("message", ""))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        pass
    low = detail.lower()
    if status == 429 or "resource_exhausted" in low or "quota" in low:
        return GeminiError(
            "QUOTA_EXHAUSTED",
            "Kuota API Gemini habis. Jalankan ulang menu 12 dan tempel API key lain "
            "saat prompt muncul.",
        )
    if status in (400, 401, 403) or "api_key_invalid" in low or "invalid api key" in low:
        return GeminiError(
            "INVALID_KEY",
            "API key Google AI Studio tidak valid. Periksa key lalu jalankan ulang menu 12.",
        )
    if "model" in low:
        return GeminiError(
            "MODEL",
            "Model Gemini tidak tersedia untuk key ini. Sunting konstanta MODEL di "
            "downloader/backend/transcribe_gemini.py (mis. gemini-3.8-flash) lalu jalankan ulang.",
        )
    return GeminiError(
        "API_ERROR",
        "Gemini menolak permintaan (HTTP %s). Periksa koneksi lalu jalankan ulang." % status,
    )


def _request(url, payload, key, opener, method="POST", extra_headers=None, raw=None):
    headers = {
        "x-goog-api-key": key,
        "Content-Type": "application/json",
        "Api-Revision": API_REVISION,
    }
    if extra_headers:
        headers.update(extra_headers)
    data = raw if raw is not None else (json.dumps(payload).encode("utf-8") if payload is not None else None)
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        response = opener(request) if opener is not None else urllib.request.urlopen(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except OSError:
            body = b""
        raise _http_error(exc.code, body)
    except (urllib.error.URLError, OSError) as exc:
        raise GeminiError(
            "NETWORK",
            "Tidak bisa terhubung ke Gemini. Periksa koneksi internet lalu jalankan ulang. "
            "Detail: %s" % exc,
        )
    try:
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()
        body = response.read()
        if status and status >= 400:
            raise _http_error(status, body)
        parsed = json.loads(body.decode("utf-8")) if body else {}
    finally:
        close = getattr(response, "close", None)
        if close is not None:
            close()
    return parsed, response.headers


def upload_file(audio_path, key, opener):
    size = os.path.getsize(audio_path)
    _, headers = _request(
        BASE_URL + "/upload/v1beta/files",
        {"file": {"display_name": "audio-extractor"}},
        key,
        opener,
        extra_headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": MIME,
        },
    )
    upload_url = headers.get("x-goog-upload-url")
    if not upload_url:
        raise GeminiError("UPLOAD", "Gemini tidak memberikan URL upload Files API.")
    with open(audio_path, "rb") as handle:
        raw = handle.read()
    info, _ = _request(
        upload_url,
        None,
        key,
        opener,
        extra_headers={
            "X-Goog-Upload-Command": "upload, finalize",
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Protocol": "resumable",
            "Content-Length": str(len(raw)),
            "Content-Type": MIME,
        },
        raw=raw,
    )
    file_data = info.get("file") or {}
    uri = file_data.get("uri")
    if not uri:
        raise GeminiError("BAD_RESPONSE", "Upload Gemini selesai tetapi URI file tidak ada.")
    return uri, file_data.get("name")


def _delete_file(name, key, opener):
    if not name:
        return
    try:
        _request(BASE_URL + "/v1beta/" + name, None, key, opener, method="DELETE")
    except GeminiError:
        pass


def transcribe(audio_path, key_path, out_txt, opener=None):
    key = ""
    uploaded_name = ""
    try:
        key = load_key(key_path)
        if os.path.getsize(audio_path) < INLINE_LIMIT_BYTES:
            with open(audio_path, "rb") as handle:
                audio_input = {
                    "type": "audio",
                    "data": base64.b64encode(handle.read()).decode("ascii"),
                    "mime_type": MIME,
                }
        else:
            uri, uploaded_name = upload_file(audio_path, key, opener)
            audio_input = {"type": "audio", "uri": uri, "mime_type": MIME}

        body, _ = _request(
            BASE_URL + "/v1beta/interactions",
            {"model": MODEL, "input": [{"type": "text", "text": PROMPT}, audio_input]},
            key,
            opener,
        )
        status, text = clean_transcript(read_text_response(body))
        if status == "no_speech":
            return _result(reason="NO_SPEECH", message="Tidak ada ucapan yang jelas.")
        if status == "empty":
            return _result(reason="BAD_RESPONSE", message="Gemini mengembalikan teks kosong atau placeholder.")
        with open(out_txt, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        return _result(
            ok=True,
            language="",
            duration=0.0,
            segments=len(text.splitlines()),
            text_chars=len(text),
        )
    except GeminiError as exc:
        return _result(reason=exc.reason, message=exc.message)
    except OSError as exc:
        return _result(reason="IO", message="Gagal membaca atau menulis file: %s" % exc)
    finally:
        if uploaded_name:
            _delete_file(uploaded_name, key, opener)


def main(argv=None, opener=None):
    parser = argparse.ArgumentParser(description="Transkripsi audio dengan Gemini API.")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--out-txt", required=True)
    args = parser.parse_args(argv)
    result = transcribe(args.audio, args.key_file, args.out_txt, opener=opener)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") or result.get("reason") == "NO_SPEECH" else 1


if __name__ == "__main__":
    sys.exit(main())
