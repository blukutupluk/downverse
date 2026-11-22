<div align="center">

# 🌌 Downverse

**🎬 Downloader media all-in-one untuk Termux (Android) 📱**

![Platform](https://img.shields.io/badge/Platform-Termux%20%7C%20Android-000000?style=for-the-badge&logo=android&logoColor=3DDC84)
![Bash](https://img.shields.io/badge/Bash-4EAA25?style=for-the-badge&logo=gnubash&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
[![Cara Install](https://img.shields.io/badge/Cara_Install-INSTALL.md-2ea44f?style=for-the-badge&logo=gnubash&logoColor=white)](INSTALL.md)

</div>

Downverse menyatukan berbagai alat downloader populer — `yt-dlp`, `gallery-dl`, `SpotDL`, `FFmpeg`, dan Playwright — ke dalam satu menu terminal yang sederhana. Unduh video, audio, dan gambar dari banyak platform, simpan langsung ke SD card, lalu olah hasilnya tanpa perlu aplikasi tambahan yang berat.

> Sebelumnya proyek ini bernama **Termux Media Downloader** (`downloader.sh`).

---

## 📖 Apa itu Downverse?

Downverse adalah aplikasi berbasis **Bash + Python** yang berjalan di Termux. Launcher dan pengelolaan file ada di Termux, sedangkan proses download dan konversi dijalankan di dalam **Debian proot** agar tool seperti `yt-dlp`, `gallery-dl`, `SpotDL`, Chromium, dan Playwright bisa bekerja dengan stabil.

Hasil download ditulis langsung ke folder SD card melalui **bind mount**, jadi file tidak menumpuk di penyimpanan internal Android.

Cocok untuk kamu yang ingin:

- mengunduh video/audio dari YouTube, Instagram, Facebook, TikTok, dan Threads;
- menyimpan lagu dari Spotify (track, album, playlist);
- mengekstrak audio dari video ke MP3/WAV;
- memecah video menjadi klip 10 detik;
- membuat transkrip otomatis dari video (MP3 + TXT);
- mengunduh banyak URL sekaligus dari file `.txt`;
- mengambil video dari situs yang tidak didukung `yt-dlp` lewat web scraper.

---

## ✨ Fitur

| # | Modul | Kemampuan | Output default |
|---|-------|-----------|----------------|
| 1 | ▶️ **YouTube** | Video tunggal & playlist | `YouTube/` |
| 2 | 📸 **Instagram** | Video, audio, dan post | `Instagram/` |
| 3 | 📘 **Facebook** | Video, audio, dan post | `Facebook/` |
| 4 | 🎵 **TikTok** | Video dan media | `TikTok/` |
| 5 | 🧵 **Threads** | Video, carousel, dan semua media (Playwright) | `Threads/` |
| 6 | 🎧 **Spotify / SpotDL** | Track, album, dan playlist | `Spotify/` |
| 7 | 🖼️ **Carousel** | Downloader galeri gambar | `Carousel/` |
| 8 | 🎼 **Extract Audio** | Konversi video ke MP3 / WAV | `Audio/MP3/`, `Audio/WAV/` |
| 9 | ✂️ **Video Splitter 10s** | Pecah video menjadi klip 10 detik tanpa audio | `audio/` |
| 10 | 📦 **Download Massal** | Banyak URL dari file `.txt` (FB, IG, YT, TikTok) | folder platform |
| 11 | 🎙️ **Audio Extractor + Transcriber** | MP3 tervalidasi + transkrip TXT via Gemini API | `audio-extractor/hasil-extract/` |
| 12 | 🌐 **Web Scraper / Downloader** | Scrape URL video dari situs bandel | `WebScraper/` |

### Fitur pendukung

- 🎛️ Menu interaktif dengan tampilan warna dan status progres.
- 🔗 Dukungan **cookie Netscape** untuk konten yang membutuhkan login.
- 💾 Output langsung ke SD card — tidak memenuhi storage internal.
- 🧪 Pemeriksaan dependency bawaan (`--check`).
- 📝 Log per sesi di folder `downloader/logs/`.
- 🔐 File cookie dan API key tidak pernah ikut ter-commit.

---

## ⚙️ Cara Kerja

```
Termux (launcher Bash)
   │
   ├── downloader.sh          menu & validasi dependency
   ├── downloader/modules/    modul per platform
   └── proot-distro Debian
         ├── yt-dlp           YouTube, IG, FB, TikTok, audio
         ├── gallery-dl       carousel / galeri
         ├── SpotDL           Spotify
         ├── Chromium + Playwright  Threads & situs dinamis
         └── FFmpeg           konversi & pemrosesan media
   │
   └── bind mount SD card  →  /storage/XXXX-XXXX/output/
```

1. `downloader.sh` menampilkan menu dan memeriksa dependency.
2. Modul memanggil tool yang sesuai di dalam Debian proot.
3. Folder output di SD card di-bind mount ke Debian.
4. File selesai ditulis langsung ke SD card.
5. Cookie (jika ada) dipakai untuk konten yang butuh login.

---

## 📋 Prasyarat

- **Termux** (disarankan dari F-Droid atau GitHub, bukan Play Store).
- Izin akses storage Android (`termux-setup-storage`).
- SD card atau folder yang bisa ditulis. Default: `/storage/7544-8C33/output`.
- Koneksi internet.
- Ruang kosong kurang lebih **1–2 GB** untuk Debian, Chromium, dan Python venv.

Dependency utama:

| Di Termux | Di Debian proot |
|-----------|-----------------|
| `bash`, `fish`, `python` | `ffmpeg`, `python3`, `python3-venv`, `python3-pip` |
| `proot-distro`, `proot` | `chromium`, `fonts-liberation` |
| `ffmpeg`, `ffprobe`, `curl`, `wget`, `git` | `yt-dlp`, `gallery-dl`, `spotdl`, `playwright`, `requests` |

---

## ⚡ Cara Install

**Cara tercepat — satu perintah:**

```bash
git clone https://github.com/blukutupluk/downverse.git
cd downverse
bash install.sh
```

`install.sh` otomatis:

- 📦 memasang paket Termux + dependency,
- 🐧 menyiapkan Debian proot + Python venv,
- 💾 mendeteksi SD card dan menulis konfigurasi,
- 🔗 membuat shortcut `downverse`,
- ✅ memvalidasi yt-dlp, FFmpeg, dan bind mount output.

Setelah selesai, jalankan:

```bash
downverse
```

> ⏱️ Butuh koneksi internet dan ruang ~1–2 GB.
> 🔍 Cek dulu tanpa mengubah apa pun: `bash install.sh --dry-run`
> ⚙️ Pilih folder output manual: `bash install.sh --output /storage/XXXX-XXXX/output`

📖 **Langkah manual, konfigurasi, update, uninstall, dan troubleshooting:** **[INSTALL.md](INSTALL.md)**

---

## 🎮 Cara Pakai

```bash
bash downloader.sh            # buka menu interaktif
bash downloader.sh --check    # cek config & dependency
bash downloader.sh --version  # tampilkan versi
```

Di menu utama, pilih nomor modul `1`–`12`, lalu masukkan URL saat diminta. Tekan `0` untuk kembali atau keluar.

### Contoh alur

1. Jalankan `bash downloader.sh`.
2. Pilih `1` untuk YouTube.
3. Pilih video tunggal atau playlist.
4. Tempel URL, tunggu proses selesai.
5. Hasil tersimpan di `$OUTPUT_ROOT/YouTube/`.

### Download massal

Siapkan file teks berisi satu URL per baris, lalu pilih menu `10`:

```text
https://www.youtube.com/watch?v=xxxxxxxx
https://www.instagram.com/reel/xxxxxxxx/
https://www.tiktok.com/@user/video/xxxxxxxx
```

---

## 🍪 Cookie (opsional)

Untuk konten yang membutuhkan login, ekspor cookie dalam format **Netscape `cookies.txt`** dan letakkan di:

```text
~/cookies/threads.txt
~/cookies/instagram.txt
~/cookies/facebook.txt
~/cookies/youtube.txt
```

> ⚠️ Cookie adalah kredensial akun. Jangan pernah membagikan isinya, dan jangan commit ke Git. Folder `cookies/` sudah dikecualikan oleh `.gitignore`.

---

## 📁 Struktur Proyek

```text
downverse/
├── install.sh                 # installer otomatis (satu perintah)
├── downloader.sh              # launcher utama
├── README.md                  # dokumentasi utama
├── INSTALL.md                 # panduan install lengkap
├── downloader/
│   ├── config.sh              # konfigurasi path, distro, cookie
│   ├── lib/                   # UI, logging, proot, validasi
│   ├── modules/               # 12 modul downloader
│   ├── backend/               # Python: Threads, Gemini, ElevenLabs
│   ├── logs/                  # log runtime
│   └── tests/                 # tes modul
├── bin/                       # utilitas & CLI pendukung
├── src/                       # API Key Manager untuk OpenCode
├── public/                    # dashboard API Key Manager
├── tests/                     # tes API Key Manager
└── docs/                      # catatan desain & rencana
```

---

## 🧰 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `DEPENDENSI HILANG` | Jalankan `pkg install` sesuai daftar prasyarat. |
| SD card tidak terlihat | Jalankan `termux-setup-storage`, lalu sesuaikan `SDCARD_ROOT` di `config.sh`. |
| Output tidak writable | Periksa izin Android dan pastikan folder output bisa ditulis. |
| Bind mount tidak cocok | Jangan gunakan mode proot isolated; pastikan path output sama di Termux dan Debian. |
| FFmpeg gagal dijalankan | `pkg update && pkg upgrade -y`, lalu cek `ffmpeg -version`. |
| Konten minta login | Tambahkan file cookie Netscape yang sesuai. |
| Chromium/Playwright error | Pastikan `chromium` terpasang di Debian dan venv berisi `playwright`. |
| Cek cepat semua dependency | `bash downloader.sh --check`. |

Log error tersimpan di `downloader/logs/` dan bisa dibuka untuk melihat detail.

---

## 🔐 Keamanan

- `.gitignore` memakai pola **default-deny**: seluruh isi home diabaikan kecuali file proyek yang di-whitelist.
- File cookie, API key, log, dan media tidak ikut ter-commit.
- API key Gemini disimpan di `~/.config/media-downloader/gemini.key` dengan permission `0600` dan tidak pernah dikirim lewat argumen atau environment variable.
- Tidak ada kredensial yang ditulis ke dalam source code.

---

## ⚠️ Disclaimer

Downverse hanya alat bantu download. Gunakan untuk konten yang kamu miliki haknya atau yang lisensinya mengizinkan. Patuhi Terms of Service masing-masing platform dan hukum yang berlaku.

---

## 🗂 Catatan Repo

Selain Downverse, repo ini juga menyimpan **API Key Manager untuk OpenCode** — server lokal untuk mengelola banyak API key dengan auto-failover. Komponennya ada di `src/`, `public/`, `bin/`, dan `tests/`, dengan dokumentasi di [KEYMANAGER.md](KEYMANAGER.md).

---

<div align="center">

Dibuat untuk Termux. Selamat mengunduh! 🌌

</div>
