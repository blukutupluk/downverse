#!/usr/bin/env python3
"""Collect video/reel URLs from a Facebook profile with Playwright.

Facebook's weblite profile renders posts as JS buttons without hrefs. This
script opens the profile's Reels tab, removes the fixed bottom banner that
intercepts clicks, scrolls until every reel tile is loaded, then force-clicks
each tile and records the canonical /reel/<id>/ URL from its permalink.
"""
import argparse
import http.cookiejar
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

REEL_SELECTOR = '[aria-label^="Reel "]'
ID_RE = re.compile(r"/(?:reel|videos)/(?:[^/]+/)?(\d+)")
PERMALINK_RE = re.compile(r"facebook\.com/(?:reel|videos)/")
BANNER_JS = "document.querySelectorAll('.fixed-container.bottom').forEach(e=>e.remove())"


def load_cookies(path: Path):
    jar = http.cookiejar.MozillaCookieJar(str(path))
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
    return cookies


def canonical(url: str):
    match = ID_RE.search(urlsplit(url).path)
    if not match:
        return None
    return "https://www.facebook.com/reel/" + match.group(1) + "/"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cookie", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-scroll", type=int, default=50)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--append", action="store_true")
    args = ap.parse_args()

    cookies = load_cookies(Path(args.cookie))
    reels_url = args.url.rstrip("/") + "/reels/"

    urls = []
    seen = set()
    diagnostics = {
        "cookies_loaded": len(cookies),
        "scrolls": 0,
        "tiles": 0,
        "opened": 0,
        "missed": 0,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        try:
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0 Mobile Safari/537.36"
                ),
                viewport={"width": 412, "height": 915},
                device_scale_factor=1,
                locale="en-US",
            )
            if cookies:
                context.add_cookies(cookies)
            page = context.new_page()
            page.goto(reels_url, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(3500)
            page.evaluate(BANNER_JS)

            previous = -1
            empty = 0
            for _ in range(args.max_scroll):
                count = page.locator(REEL_SELECTOR).count()
                diagnostics["scrolls"] += 1
                if count == previous:
                    empty += 1
                else:
                    empty = 0
                previous = count
                if empty >= 4:
                    break
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1800)

            diagnostics["tiles"] = page.locator(REEL_SELECTOR).count()

            end = args.end or diagnostics["tiles"]
            for i in range(args.start, min(end, diagnostics["tiles"])):
                try:
                    page.goto(reels_url, wait_until="domcontentloaded", timeout=90000)
                    page.wait_for_timeout(2500)
                    page.evaluate(BANNER_JS)
                    # A fresh load only renders the first batch; scroll until the
                    # requested tile exists before clicking it.
                    for _ in range(args.max_scroll):
                        if page.locator(REEL_SELECTOR).count() > i:
                            break
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(900)
                    page.locator(REEL_SELECTOR).nth(i).click(force=True, timeout=10000)
                    try:
                        page.wait_for_url(PERMALINK_RE, timeout=12000)
                    except Exception:
                        page.wait_for_timeout(1500)
                    diagnostics["opened"] += 1
                    clean = canonical(page.url)
                    if clean and clean not in seen:
                        seen.add(clean)
                        urls.append(clean)
                    elif not clean:
                        diagnostics["missed"] += 1
                except Exception as exc:
                    diagnostics["missed"] += 1
                    print(f"Gagal reel #{i}: {exc}", file=sys.stderr)
        finally:
            browser.close()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if args.append and out_path.is_file():
        existing = [line.strip() for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for item in existing:
            if item not in seen:
                seen.add(item)
                urls.append(item)
    out_path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")

    print(json.dumps({"count": len(urls), "diagnostics": diagnostics}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
