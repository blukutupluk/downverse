# Design: OpenCode Account Switcher Script

## Intent & Why
User memiliki beberapa akun OpenCode Console di perangkat dan ingin cara cepat untuk menambah, melihat, dan berpindah akun tanpa mengedit SQLite/`opencode.json` manual.

## Goals
1. Skrip `~/bin/opencode-account` dengan subcommand: `add`, `add-import`, `list`, `switch`, `export`, `remove`.
2. `list` menampilkan email, org, label, dan status aktif tanpa membocorkan token.
3. Semua mutasi credential memakai CLI resmi `opencode auth ...` (bukan SQL manual).
4. Backup credential tersimpan dengan izin `0600`.

## Non-Goals
- Tidak menyimpan/menampilkan access token secara plain di layar/log.
- Tidak mengubah `opencode.json` (model/provider) — itu urusan fitur terpisah.

## Constraints
- Termux / Android, shell POSIX (`/bin/sh`), Python3 untuk baca SQLite read-only.
- `opencode` CLI tersedia di PATH.

## Approaches
1. **Wrapper CLI resmi (dipilih)** — aman, OpenCode yang mengelola state & active flag.
2. **Tulis langsung ke `opencode.db`** — ditolak: raw OAuth token, risiko korupsi state dan active-account bookkeeping.

## Design
- `src/opencode-accounts.js`: `listCredentials()`, `parseCredentialValue()`, `formatCredentialTable()` (pure), plus runner `runAuthCommand()`.
- `bin/opencode-account`: dispatcher shell/Node ke subcommand.
- `tests/opencode-accounts.test.js`: test parser & formatter dengan credential JSON contoh (tanpa token asli).
