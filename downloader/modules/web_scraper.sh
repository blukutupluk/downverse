#!/data/data/com.termux/files/usr/bin/bash
# Web Scraper / Downloader: ekstrak video dari situs bandel (jav.guru, dsb).
# Alur: ambil HTML → cari URL video (mp4/m3u8/ts) → download via yt-dlp atau curl.

module_web_scraper() {
  local url out_dir choice
  ui_header
  ui_section "WEB SCRAPER / DOWNLOADER"
  ui_item "1" "Scrape & Download" "Ambil semua video dari satu halaman"
  ui_item "2" "Download URL langsung" "Download satu URL video/gambar"
  ui_item "0" "Kembali" ""
  printf '\nPilih: '; IFS= read -r choice
  case "$choice" in
    1) _ws_scrape_page ;;
    2) _ws_download_direct ;;
    0) return 0 ;;
    *) ui_error "Pilihan tidak valid."; sleep 1 ;;
  esac
}

_ws_scrape_page() {
  local url out_dir
  out_dir="$OUTPUT_ROOT/WebScraper"
  mkdir -p "$out_dir"
  ui_header; ui_section "SCRAPE & DOWNLOAD"
  ask_url "URL halaman" || { ui_pause; return 1; }
  check_host || { ui_pause; return 1; }
  url="$URL"

  printf '\n%b\n' "${DIM}Mengambil halaman...${RESET}"
  local html_file="$out_dir/.page.html"
  if ! curl -sSL -A "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" \
       --max-time 30 -o "$html_file" "$url"; then
    ui_error "Gagal mengambil halaman: $url"
    rm -f "$html_file"
    ui_pause; return 1
  fi

  printf '%b\n' "${DIM}Mencari URL video...${RESET}"
  # Ekstrak URL video dari HTML (mp4, m3u8, webm, ts, ogg)
  local urls_file="$out_dir/.urls.txt"
  python3 - "$html_file" "$urls_file" "$url" <<'PY'
import sys, re, urllib.parse
html_path, out_path, base_url = sys.argv[1], sys.argv[2], sys.argv[3]
with open(html_path, encoding="utf-8", errors="ignore") as f:
    html = f.read()

# Pola URL video
patterns = [
    r'(https?://[^\s"\'<>]+?\.(?:mp4|m3u8|webm|ts|ogg|mov|avi|flv|mkv)(?:\?[^\s"\'<>]*)?)',
    r'(https?://[^\s"\'<>]+?(?:video|stream|media|cdn)[^\s"\'<>]*)',
    r'src=["\']([^"\']+?\.(?:mp4|m3u8|webm|ts|ogg|mov|avi|flv|mkv)(?:\?[^\s"\'<>]*)?)["\']',
    r'href=["\']([^"\']+?\.(?:mp4|m3u8|webm|ts|ogg|mov|avi|flv|mkv)(?:\?[^\s"\'<>]*)?)["\']',
    r'data-src=["\']([^"\']+)["\']',
    r'data-video=["\']([^"\']+)["\']',
    r'file:\s*["\']([^"\']+)["\']',
    r'source:\s*["\']([^"\']+)["\']',
]
found = set()
for pat in patterns:
    for m in re.finditer(pat, html, re.IGNORECASE):
        u = m.group(1)
        if not u.startswith("http"):
            u = urllib.parse.urljoin(base_url, u)
        # bersihkan trailing quote/bracket
        u = u.rstrip('"\'<> ')
        if len(u) > 10 and "javascript" not in u.lower():
            found.add(u)

# Dedup berdasarkan basename
unique = []
seen = set()
for u in found:
    key = u.split("?")[0].rsplit("/", 1)[-1]
    if key not in seen:
        seen.add(key)
        unique.append(u)

# Filter hanya URL yang benar-benar video
VIDEO_EXTS = ("mp4","m3u8","webm","ts","ogg","mov","avi","flv","mkv","mpd","m4v","3gp","m3u8")
filtered = []
for u in unique:
    base = u.split("?")[0].lower()
    ext = base.rsplit(".", 1)[-1] if "." in base else ""
    if ext in VIDEO_EXTS and len(u) > 10 and "javascript" not in u.lower():
        filtered.append(u)

with open(out_path, "w", encoding="utf-8") as f:
    for u in filtered:
        f.write(u + "\n")
print(len(filtered))
PY
  local count
  count=$(wc -l < "$urls_file" 2>/dev/null || echo 0)
  if [[ "$count" -eq 0 ]]; then
    ui_error "Tidak ditemukan URL video di halaman."
    rm -f "$html_file" "$urls_file"
    ui_pause; return 1
  fi

  printf '\n%b\n' "${GREEN}Ditemukan $count URL video.${RESET}"
  cat -n "$urls_file"
  printf '\n%b\n' "${DIM}Download semua? [y/N]${RESET}"
  printf 'Pilih: '; IFS= read -r confirm
  [[ "$confirm" != "y" && "$confirm" != "Y" ]] && { rm -f "$html_file" "$urls_file"; ui_pause; return 0; }

  local i=0
  while IFS= read -r vurl; do
    [[ -z "$vurl" ]] && continue
    i=$((i + 1))
    printf '\n%b\n' "${CYAN}[$i/$count] $vurl${RESET}"
    # Coba yt-dlp dulu, fallback ke curl
    local rc=0
    if proot_run "$YTDLP_BIN" --newline --ignore-errors --retries 2 --socket-timeout 30 \
       -f 'bv*+ba/b' --merge-output-format mp4 \
       -o "$out_dir/%(title).100B [%(id)s].mp4" "$vurl" 2>/dev/null; then
      rc=0
    else
      # fallback curl
      local fname
      fname="$out_dir/video_$(date +%s)_$i.mp4"
      if curl -sSL -A "Mozilla/5.0" --max-time 120 -o "$fname" -w '%{content_type}' "$vurl" > /tmp/ws_ct.txt; then
        local c2
        c2=$(cat /tmp/ws_ct.txt)
        if [[ "$c2" == text/html* ]]; then
          rc=1
        else
          rc=0
        fi
      else
        rc=1
      fi
      rm -f /tmp/ws_ct.txt
    fi
    if [[ $rc -eq 0 ]]; then
      ui_ok "Download selesai"
    else
      ui_error "Download gagal: $vurl"
    fi
  done < "$urls_file"

  rm -f "$html_file" "$urls_file"
  ui_ok "Semua selesai. Hasil di: $out_dir"
  ui_pause
}

_ws_download_direct() {
  local url out_dir
  out_dir="$OUTPUT_ROOT/WebScraper"
  mkdir -p "$out_dir"
  ui_header; ui_section "DOWNLOAD URL LANGSUNG"
  ask_url "URL video/gambar" || { ui_pause; return 1; }
  url="$URL"
  local fname="$out_dir/direct_$(date +%s).mp4"
  printf '\n%b\n' "${DIM}Mengunduh...${RESET}"
  local ct
  ct=$(curl -sSL -A "Mozilla/5.0" --max-time 300 -o "$fname" -w '%{content_type}' "$url")
  case "$ct" in
    text/html*)
      ui_error "URL ini ternyata HALAMAN HTML, bukan file video langsung."
      ui_error "Cek isi respons Content-Type: $ct"
      ui_error "Pakai fitur 'Scrape & Download' dengan URL halaman: $url"
      rm -f "$fname"
      ui_pause; return 1
      ;;
    video/*|application/x-matroska|audio/*|application/octet-stream*)
      ui_ok "Selesai: $fname"
      ;;
    *)
      ui_error "Download gagal. Content-Type tidak didukung: $ct"
      rm -f "$fname"
      ui_pause; return 1
      ;;
  esac
  ui_pause
}