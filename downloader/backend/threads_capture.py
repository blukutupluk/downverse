#!/usr/bin/env python3
"""Capture only the requested Threads post media with Playwright.

Default mode is `video`: do not traverse carousel items and do not collect images.
`carousel` is an explicit separate mode for users who intentionally want all assets.
Only content accessible to the authenticated account is handled.
"""
import argparse
import base64
import http.cookiejar
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

MEDIA_HOST_MARKERS = ("cdninstagram.com", "fbcdn.net")
AVATAR_MARKERS = ("profile_pic", "profile", "avatar", "s150x150", "s320x320", "p50x50", "p100x100")


def normalize_url(url: str) -> str:
    p = urlsplit(url)
    # Keep signed query parameters intact; only remove byte-range selectors.
    kept = []
    for part in p.query.split("&"):
        key = unquote(part.split("=", 1)[0]).lower()
        if key not in ("bytestart", "byteend"):
            kept.append(part)
    return urlunsplit((p.scheme, p.netloc, p.path, "&".join(kept), ""))


def decode_vencode_tag(url: str) -> str:
    try:
        query = dict(parse_qsl(urlsplit(url).query, keep_blank_values=True))
        efg = query.get("efg", "")
        if not efg:
            return ""
        raw = base64.urlsafe_b64decode(efg + "=" * (-len(efg) % 4))
        obj = json.loads(raw.decode("utf-8", "replace"))
        return str(obj.get("vencode_tag", "")).lower()
    except Exception:
        return ""


def classify(url: str, mime: str) -> str:
    path = urlsplit(url).path.lower()
    mime = (mime or "").lower()
    if path.endswith(".mp4") or mime.startswith("video/"):
        tag = decode_vencode_tag(url)
        if "audio" in tag or "heaac" in tag or "aac" in tag:
            return "audio"
        if "baseline" in tag or "video" in tag or "h264" in tag or "h265" in tag:
            return "video"
        return "unknown"  # MP4 stream; Termux ffprobe identifies the track.
    if mime.startswith("image/") or re.search(r"\.(jpe?g|png|webp)(?:$|\?)", url, re.I):
        if any(marker in url.lower() for marker in AVATAR_MARKERS):
            return "skip"
        return "image"
    return "skip"


def response_size(headers: dict) -> int:
    """Estimate total response size, preferring Content-Range total when present."""
    content_range = headers.get("content-range", "")
    match = re.search(r"/([0-9]+)$", content_range)
    if match:
        return int(match.group(1))
    try:
        return int(headers.get("content-length", "0"))
    except (TypeError, ValueError):
        return 0


def select_video_only(items: list[dict]) -> list[dict]:
    """Select no more than one video and one audio track for a single post.

    Explicitly tagged video/audio streams take priority. If Threads omits its
    tag, retain at most the two largest unknown MP4 candidates for ffprobe.
    """
    videos = [x for x in items if x["kind"] == "video"]
    audios = [x for x in items if x["kind"] == "audio"]
    unknown = [x for x in items if x["kind"] == "unknown"]
    selected = []

    if videos:
        selected.append(max(videos, key=lambda x: x.get("size", 0)))
    if audios:
        selected.append(max(audios, key=lambda x: x.get("size", 0)))

    missing_tracks = 2 - len(selected)
    if missing_tracks > 0 and unknown:
        unknown.sort(key=lambda x: x.get("size", 0), reverse=True)
        selected.extend(unknown[:missing_tracks])
    return selected


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cookie", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=("video", "carousel"), default="video")
    args = ap.parse_args()

    cookie_path = Path(args.cookie)
    jar = http.cookiejar.MozillaCookieJar(str(cookie_path))
    if not cookie_path.is_file():
        raise SystemExit("Cookie file tidak ditemukan: " + str(cookie_path))
    jar.load(ignore_discard=True, ignore_expires=True)
    cookies = []
    for item in jar:
        if not item.domain:
            continue
        cookie = {
            "name": item.name,
            "value": item.value,
            "domain": item.domain,
            "path": item.path or "/",
            "secure": bool(item.secure),
        }
        if item.expires:
            cookie["expires"] = int(item.expires)
        cookies.append(cookie)

    media = {}
    diagnostics = {
        "mode": args.mode,
        "responses": 0,
        "media_responses": 0,
        "ignored_images": 0,
        "carousel_clicks": 0,
    }
    final_url = args.url
    title = "Threads"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        try:
            context = browser.new_context(
                user_agent=("Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 "
                            "Chrome/131.0 Mobile Safari/537.36"),
                viewport={"width": 412, "height": 915},
                device_scale_factor=1,
                locale="en-US",
            )
            if cookies:
                context.add_cookies(cookies)
            page = context.new_page()

            def capture(response):
                diagnostics["responses"] += 1
                try:
                    u = response.url
                    host = urlsplit(u).netloc.lower()
                    if not any(marker in host for marker in MEDIA_HOST_MARKERS):
                        return
                    headers = response.headers
                    mime = headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    kind = classify(u, mime)
                    if kind == "skip":
                        return
                    if args.mode == "video" and kind == "image":
                        diagnostics["ignored_images"] += 1
                        return
                    clean = normalize_url(u)
                    candidate = {
                        "kind": kind,
                        "mime": mime,
                        "url": clean,
                        "size": response_size(headers),
                    }
                    if clean not in media:
                        media[clean] = candidate
                        diagnostics["media_responses"] += 1
                    elif candidate["size"] > media[clean].get("size", 0):
                        media[clean]["size"] = candidate["size"]
                    elif media[clean]["kind"] == "unknown" and kind != "unknown":
                        media[clean]["kind"] = kind
                except Exception:
                    return

            page.on("response", capture)
            try:
                page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
            except PlaywrightTimeoutError:
                pass
            try:
                page.wait_for_load_state("networkidle", timeout=18000)
            except PlaywrightTimeoutError:
                pass
            page.wait_for_timeout(9000)
            final_url = page.url
            title = page.title()

            # Only explicit carousel mode advances through items.
            if args.mode == "carousel":
                for _ in range(20):
                    clicked = False
                    selectors = [
                        'button[aria-label*="next" i]',
                        'button[aria-label*="selanjutnya" i]',
                        '[role="button"][aria-label*="next" i]',
                        '[role="button"][aria-label*="selanjutnya" i]',
                    ]
                    for selector in selectors:
                        try:
                            loc = page.locator(selector).first
                            if loc.count() and loc.is_visible():
                                loc.click(timeout=1500)
                                clicked = True
                                diagnostics["carousel_clicks"] += 1
                                page.wait_for_timeout(1100)
                                break
                        except Exception:
                            continue
                    if not clicked:
                        break

                # DOM image fallback is allowed only in carousel mode.
                try:
                    visible = page.locator("img").evaluate_all(
                        "els => els.map(e => ({src:e.currentSrc||e.src, alt:e.alt||''}))"
                    )
                    for item in visible:
                        u = item.get("src", "")
                        if not u:
                            continue
                        host = urlsplit(u).netloc.lower()
                        if not any(marker in host for marker in MEDIA_HOST_MARKERS):
                            continue
                        if any(marker in u.lower() for marker in AVATAR_MARKERS):
                            continue
                        clean = normalize_url(u)
                        if clean not in media:
                            media[clean] = {
                                "kind": "image",
                                "mime": "image/unknown",
                                "url": clean,
                                "size": 0,
                            }
                except Exception:
                    pass
        finally:
            browser.close()

    items = list(media.values())
    if args.mode == "video":
        items = select_video_only(items)

    payload = {
        "input_url": args.url,
        "final_url": final_url,
        "title": title,
        "mode": args.mode,
        "cookies_loaded": len(cookies),
        "diagnostics": diagnostics,
        "media": items,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MODE=" + args.mode)
    print("FINAL_URL=" + final_url)
    print("MEDIA_COUNT=" + str(len(items)))
    print("CAPTURE_FILE=" + str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
