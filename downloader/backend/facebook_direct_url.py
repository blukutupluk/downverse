#!/usr/bin/python3
"""Ambil URL MP4 langsung dari halaman reel/post Facebook.

Dipakai fallback ketika yt-dlp gagal mem-parse payload video Facebook
("Cannot parse data") karena Facebook mengubah struktur data internalnya.
Halaman reel tetap berisi URL progresif di dalam blob Relay `data-sjs`.

Usage:
    python3 facebook_direct_url.py URL COOKIE_FILE

Stdout: satu baris URL MP4 langsung (hanya URL, tanpa teks lain).
Stderr: pesan error.
"""

import json
import re
import sys


def load_cookies(path):
    """Baca cookie Netscape (Format Mozilla) jadi dict nama->nilai."""
    cookies = {}
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
    except OSError as exc:
        print(f"Gagal membaca cookie: {exc}", file=sys.stderr)
    return cookies


def find_fragment(node):
    """Cari videoDeliveryResponseFragment secara rekursif di JSON Relay."""
    if isinstance(node, dict):
        fragment = node.get("videoDeliveryResponseFragment")
        if isinstance(fragment, dict):
            return fragment
        for value in node.values():
            found = find_fragment(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_fragment(value)
            if found:
                return found
    return None


def collect_results(html):
    """Kumpulkan semua videoDeliveryResponseResult dari script data-sjs."""
    results = []
    for blob in re.findall(r"<script[^>]*data-sjs[^>]*>(.*?)</script>", html, re.S):
        try:
            data = json.loads(blob)
        except ValueError:
            continue
        fragment = find_fragment(data)
        if not fragment:
            continue
        result = fragment.get("videoDeliveryResponseResult")
        if isinstance(result, dict):
            results.append(result)
    return results


def choose_url(result):
    """Pilih URL progresif terbaik (HD lebih diutamakan)."""
    candidates = []
    for item in result.get("progressive_urls") or []:
        url = item.get("progressive_url")
        if not url:
            continue
        quality = str((item.get("metadata") or {}).get("quality") or "").upper()
        candidates.append((1 if quality == "HD" else 0, url))
    if candidates:
        return max(candidates, key=lambda pair: pair[0])[1]
    return None


def main():
    if len(sys.argv) != 3:
        print("Usage: facebook_direct_url.py URL COOKIE_FILE", file=sys.stderr)
        return 2

    url, cookie_file = sys.argv[1], sys.argv[2]

    try:
        from curl_cffi import requests as browser
    except ImportError:
        print("curl_cffi tidak tersedia di venv Debian", file=sys.stderr)
        return 3

    try:
        response = browser.get(
            url,
            impersonate="chrome",
            cookies=load_cookies(cookie_file),
            timeout=60,
            allow_redirects=True,
        )
        response.raise_for_status()
        html = response.text
    except Exception as exc:
        print(f"Gagal mengambil halaman Facebook: {exc}", file=sys.stderr)
        return 4

    for result in collect_results(html):
        direct = choose_url(result)
        if direct:
            print(direct)
            return 0

    print("URL video tidak ditemukan di halaman Facebook", file=sys.stderr)
    return 5


if __name__ == "__main__":
    sys.exit(main())
