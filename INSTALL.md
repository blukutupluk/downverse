# ⚡ Cara Install Downverse

Panduan lengkap memasang **Downverse** di Termux (Android).

> 💡 Setup backend cukup dilakukan **sekali**. Setelah selesai, kamu tinggal menjalankan `bash downloader.sh`.

---

## 📋 Yang Dibutuhkan

| Kebutuhan | Keterangan |
|-----------|------------|
| 📱 **Termux** | Disarankan dari [F-Droid](https://f-droid.org/packages/com.termux/) atau [GitHub](https://github.com/termux/termux-app/releases), **bukan** Play Store |
| 💾 **Storage** | Izin akses file Android + folder output yang bisa ditulis |
| 🌐 **Internet** | Untuk mengunduh paket dan dependency |
| 📦 **Ruang kosong** | Kurang lebih **1–2 GB** untuk Debian, Chromium, dan Python venv |

---

## ⚡ Cara Tercepat (Installer Otomatis)

```bash
git clone https://github.com/blukutupluk/downverse.git
cd downverse
bash install.sh
```

Installer akan melakukan semuanya:

- 📦 memasang paket Termux + dependency,
- 🐧 menyiapkan Debian proot + Python venv,
- 💾 mendeteksi SD card dan menulis konfigurasi,
- 🔗 membuat shortcut `downverse`,
- ✅ memvalidasi yt-dlp, FFmpeg, dan bind mount output.

Setelah selesai:

```bash
downverse
```

### Opsi Installer

| Opsi | Fungsi |
|------|--------|
| `bash install.sh` | Install interaktif (disarankan) |
| `bash install.sh --yes` | Non-interaktif, jawab "ya" otomatis |
| `bash install.sh --output PATH` | Tentukan folder output manual |
| `bash install.sh --dry-run` | Tampilkan langkah tanpa mengubah sistem |
| `bash install.sh --help` | Tampilkan bantuan |

> ⏱️ Proses ini bisa memakan waktu 10–30 menit tergantung koneksi dan perangkat.
> 🔁 Aman dijalankan ulang — installer bersifat idempotent.

---

## 🛠️ Instalasi Manual (Alternatif)

### 1️⃣ Clone repo

```bash
git clone https://github.com/blukutupluk/downverse.git
cd downverse
```

### 2️⃣ Pasang dependency Termux

```bash
pkg update && pkg upgrade -y
pkg install -y bash fish python proot-distro proot ffmpeg curl wget git termux-tools
termux-setup-storage
```

> Setujui dialog izin storage yang muncul di Android.

### 3️⃣ Siapkan Debian + tool media

```bash
proot-distro install debian
```

```bash
proot-distro login debian -- bash -lc \
  'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ca-certificates curl wget ffmpeg python3 python3-venv python3-pip \
  chromium fonts-liberation'
```

```bash
proot-distro login debian -- bash -lc \
  'python3 -m venv /opt/media-downloader-venv && \
   /opt/media-downloader-venv/bin/pip install -U pip setuptools wheel \
   yt-dlp gallery-dl spotdl playwright requests'
```

### 4️⃣ Sesuaikan konfigurasi

```bash
nano downloader/config.sh
```

Sesuaikan minimal `SDCARD_ROOT` dengan path SD card kamu. Cek path yang tersedia:

```bash
ls /storage/
```

Contoh:

```bash
SDCARD_ROOT="/storage/7544-8C33"
OUTPUT_ROOT="$SDCARD_ROOT/output"
```

### 5️⃣ Tandai setup selesai

```bash
touch ~/.media-downloader-ready
```

### 6️⃣ Cek & jalankan

```bash
bash downloader.sh --check
bash downloader.sh
```

Kalau `--check` menampilkan `OK: config & dependencies`, berarti Downverse siap dipakai. 🎉

---

## 🔧 Konfigurasi

Semua pengaturan ada di `downloader/config.sh`:

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `PROOT_DISTRO` | `debian` | Nama distro proot |
| `PROOT_VENV` | `/opt/media-downloader-venv` | Lokasi Python venv di Debian |
| `SDCARD_ROOT` | `/storage/7544-8C33` | Path SD card kamu |
| `OUTPUT_ROOT` | `$SDCARD_ROOT/output` | Folder hasil download |
| `COOKIE_DIR` | `$HOME/cookies` | Folder file cookie Netscape |
| `INSTALLER` | path skrip setup | Skrip setup/perbaikan milikmu |

Konfigurasi juga bisa di-override lewat environment variable, misalnya:

```bash
SDCARD_ROOT=/storage/ABCD-1234 bash downloader.sh
```

---

## 🔗 Bikin Shortcut `downverse`

> 💡 `install.sh` sudah membuat shortcut ini otomatis. Langkah di bawah hanya untuk instalasi manual.

Biar tidak perlu mengetik path panjang:

```bash
chmod +x downloader.sh
ln -sf "$PWD/downloader.sh" "$PREFIX/bin/downverse"
```

Sekarang cukup jalankan:

```bash
downverse
```

---

## 🍪 Cookie (Opsional)

Untuk konten yang membutuhkan login, ekspor cookie format **Netscape `cookies.txt`** lalu letakkan di:

```text
~/cookies/threads.txt
~/cookies/instagram.txt
~/cookies/facebook.txt
~/cookies/youtube.txt
```

> ⚠️ Cookie adalah kredensial akun. Jangan dibagikan dan jangan di-commit ke Git. Folder `cookies/` sudah otomatis diabaikan.

---

## 🔄 Update Downverse

```bash
cd ~/downverse
git pull origin master
bash install.sh
```

`install.sh` akan memperbarui dependency dan konfigurasi tanpa menghapus hasil download.

---

## 🗑️ Uninstall

Hapus project, venv Debian, dan marker:

```bash
# Hapus project
rm -rf ~/downverse

# Hapus venv di Debian
proot-distro login debian -- rm -rf /opt/media-downloader-venv

# Hapus marker & shortcut
rm -f ~/.media-downloader-ready
rm -f "$PREFIX/bin/downverse"
```

> File hasil download di SD card **tidak** ikut terhapus. Hapus manual jika tidak diperlukan.

---

## 🧰 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `install.sh` gagal saat `pkg update` | Jalankan `termux-change-repo`, pilih mirror resmi, lalu ulangi. |
| Installer berhenti saat `pkg upgrade` | Jalankan `pkg update && pkg upgrade -y` manual, lalu ulangi `bash install.sh`. |
| Ingin cek langkah tanpa mengubah sistem | `bash install.sh --dry-run`. |
| `downverse: command not found` | Jalankan ulang `bash install.sh`, atau cek `ls -l "$PREFIX/bin/downverse"`. |
| `DEPENDENSI HILANG` | Jalankan `pkg install` sesuai daftar di langkah 2️⃣, atau ulangi `bash install.sh`. |
| `SETUP BELUM SELESAI` | Buat marker: `touch ~/.media-downloader-ready`, atau ulangi `bash install.sh`. |
| SD card tidak terlihat | Jalankan `termux-setup-storage`, lalu sesuaikan `SDCARD_ROOT`. |
| Output tidak writable | Periksa izin Android dan pastikan folder output bisa ditulis. |
| Bind mount tidak cocok | Jangan pakai mode proot isolated; path output harus sama di Termux dan Debian. |
| FFmpeg gagal dijalankan | `pkg update && pkg upgrade -y`, lalu cek `ffmpeg -version`. |
| Konten minta login | Tambahkan file cookie Netscape yang sesuai. |
| Chromium/Playwright error | Pastikan `chromium` terpasang di Debian dan `playwright` ada di venv. |
| Cek cepat semua dependency | `bash downloader.sh --check`. |

Log error tersimpan di `downloader/logs/`.

---

## ❓ FAQ

**Apakah harus pakai SD card?**  
Tidak wajib. Kamu bisa mengarahkan `SDCARD_ROOT`/`OUTPUT_ROOT` ke folder lain yang bisa ditulis, misalnya `$HOME/storage/shared/Download`.

**Apakah bisa tanpa Debian proot?**  
Tidak untuk setup bawaan ini. `yt-dlp`, `gallery-dl`, `SpotDL`, Chromium, dan Playwright dijalankan di dalam Debian proot.

**Kenapa butuh Chromium?**  
Untuk modul Threads dan web scraper yang membutuhkan browser headless (Playwright).

**Di mana hasil download?**  
Secara default di `/storage/XXXX-XXXX/output/`, dengan subfolder per platform (`YouTube/`, `Instagram/`, `TikTok/`, dst).

**Apakah API key aman?**  
API key Gemini disimpan di `~/.config/media-downloader/gemini.key` dengan permission `0600` dan tidak ditulis ke source code.

---

<div align="center">

**[⬅️ Kembali ke README](README.md)**

Selamat mengunduh! 🌌

</div>
