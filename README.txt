TERMUX MEDIA DOWNLOADER

PRASYARAT PROYEK (WAJIB)
Installer hanya mengonfigurasi backend Termux/Debian; installer TIDAK membuat
atau mengunduh file aplikasi. Sebelum menjalankan installer, proyek harus sudah
disalin lengkap ke:
  ~/downloader.sh
  ~/downloader/   (config.sh, lib/, modules/, backend/)
Jika salah satu komponen tidak ada, installer berhenti, menghapus marker lama,
dan TIDAK menulis ~/.media-downloader-ready.

Instalasi backend (proyek sudah ada):
1. Di Termux, beri izin storage saat Android memintanya.
2. Bootstrap akan memasang Fish, Python, PRoot-Distro, FFmpeg, dan tool dasar.
3. install.fish memasang Debian, Chromium, Playwright, yt-dlp, gallery-dl, SpotDL, dan FFmpeg di Debian.

Launcher:
  bash ~/downloader.sh
atau:
  downloader

Lokasi:
  Launcher : ~/downloader.sh
  Project  : ~/downloader/
  Cookies  : ~/cookies/
  Output   : /storage/7544-8C33/output/
  Threads  : /storage/7544-8C33/output/Threads/

Cookies:
Ekspor cookies dengan format Netscape cookies.txt. Letakkan file sesuai nama:
  ~/cookies/threads.txt
  ~/cookies/instagram.txt
  ~/cookies/facebook.txt
  ~/cookies/youtube.txt
Jangan membagikan isi file cookie; sessionid adalah kredensial akun.

Backend:
- yt-dlp, gallery-dl, SpotDL, Python venv, Chromium, Playwright dan FFmpeg berjalan di Debian/PRoot.
- Threads memakai Playwright untuk menangkap URL media browser. curl dan FFmpeg berjalan di Termux untuk menulis/memproses file di SD card.
- PRoot-Distro sesi normal membagikan path Android storage dan Termux home. Jangan gunakan mode isolated untuk workflow ini.

Batasan:
- Dukungan setiap extractor bergantung pada platform dan akses akun.
- Threads carousel adalah best-effort: browser mencoba klik kontrol Next dan menangkap aset yang dimuat. Carousel wajib diuji pada post nyata; jangan menganggap sudah tervalidasi hanya karena video tunggal berhasil.
- URL CDN bersifat sementara. Downloader selalu menangkap ulang URL ketika dijalankan.


Recovery jika muncul "PRoot-Distro belum tersedia":
Di Termux/Fish jalankan:
  pkg update -y; and pkg install -y proot-distro; and fish ~/install.fish
Installer akan memverifikasi executable, memasang Debian beserta backend, lalu mengetes Chromium + Playwright.
Jika `pkg install proot-distro` gagal, periksa repository/mirror dengan `termux-change-repo`; jangan jalankan launcher download sebelum installer selesai.

Repair kit lama (OBSOLETE - JANGAN DIJALANKAN)
Kit berikut sudah tidak dipakai dan entry point-nya dikarantina pada 2026-11-18
(Sprint 1 / AUD-02). Isinya dipertahankan hanya sebagai referensi:
  - ~/media-downloader-storage-fix/repair-current-install.fish.QUARANTINED
  - ~/media-downloader-threads-fix/repair-threads.fish.QUARANTINED
  - ~/media-downloader-gallerydl-fix/repair-gallerydl.fish.QUARANTINED
Kit storage-fix berisi common.sh lama dengan opsi `--timeout` yang tidak valid
dan menu carousel lama yang memakai rute Threads deprecated. Menjalankannya
bisa menimpa instalasi aktif (`--http-timeout` hilang). Jangan dijalankan,
jangan disalin manual ke ~/downloader.
