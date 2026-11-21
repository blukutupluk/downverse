# OpenCode Account Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Skrip `opencode-account` untuk menambah, melihat, dan berpindah akun OpenCode lewat CLI resmi.

**Architecture:** Node module `src/opencode-accounts.js` untuk parsing/formatting credential (testable) + runner perintah `opencode auth`. Dispatcher `bin/opencode-account` (Node shebang) sebagai CLI.

**Tech Stack:** Node.js ESM, `/bin/sh` launcher, python3 untuk SQLite read-only, `node:test`.

**Spec:** `docs/superpowers/specs/2026-11-21-opencode-account-switcher-design.md`

## Global Constraints
- Jangan pernah menampilkan access/refresh token ke stdout.
- Semua mutasi via `opencode auth ...`, bukan SQLite write.
- Backup export chmod 0600.

## Review Focus
1. Token bocor di `list`/log → formatters harus menyaring field sensitif.
2. Duplicate label saat switch → gunakan credential ID bila tersedia.
3. DB terkunci saat OpenCode berjalan → baca SQLite mode read-only.
4. Export file permissions → 0600.

---

### Task 1: Credential parser & formatter (`src/opencode-accounts.js`)

**Files:** Create `src/opencode-accounts.js`, `tests/opencode-accounts.test.js`

**Interfaces:**
- Produces: `parseCredentialValue(rawJson)`, `sanitizeCredential(row)`, `formatCredentialTable(rows)`

- [ ] **Step 1: Tulis test gagal** — parser ekstrak email/orgName/accountID, sanitize menghapus token, formatter tidak mengandung kata "access".
- [ ] **Step 2: Jalankan** `node --test tests/opencode-accounts.test.js` → FAIL module not found.
- [ ] **Step 3: Implementasi** fungsi pure di `src/opencode-accounts.js`.
- [ ] **Step 4: Jalankan** → PASS.
- [ ] **Step 5: Commit** `feat(opencode-accounts): add credential parser and sanitizer`

---

### Task 2: CLI dispatcher (`bin/opencode-account`)

**Files:** Create `bin/opencode-account`, modify `KEYMANAGER.md`

**Interfaces:**
- Consumes: parser/formatter Task 1
- Produces: `opencode-account add|add-import|list|switch|export|remove`

- [ ] **Step 1: Tulis test gagal** — `tests/opencode-account-cli.test.js` cek help/usage menjalankan subcommand dengan argumen salah tanpa crash.
- [ ] **Step 2: Jalankan** → FAIL.
- [ ] **Step 3: Implementasi** dispatcher + `runAuthCommand`, `listCredentials` via python3 read-only, export chmod 0600.
- [ ] **Step 4: Jalankan** → PASS.
- [ ] **Step 5: Commit** `feat(opencode-account): add CLI dispatcher wrapping opencode auth`
