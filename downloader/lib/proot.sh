# Host-side preflight and PRoot entrypoint.
# Android's default PRoot-Distro binds do not include every removable SD volume.
# Bind only the configured output directory explicitly for every Debian session.

proot_bind_target_prepare() {
  [[ -d "$SDCARD_ROOT" ]] || {
    ui_error "SD card tidak terlihat dari Termux: $SDCARD_ROOT"
    return 1
  }
  # Ensure the mount point exists in Debian's rootfs before applying the bind.
  proot-distro login "$PROOT_DISTRO" -- mkdir -p "$OUTPUT_ROOT" >/dev/null 2>&1 || {
    ui_error "Tidak bisa menyiapkan mount point output di Debian: $OUTPUT_ROOT"
    return 1
  }
  return 0
}

proot_login() {
  proot-distro login --bind "$OUTPUT_ROOT:$OUTPUT_ROOT" "$PROOT_DISTRO" -- "$@"
}

proot_require() {
  if ! command -v proot-distro >/dev/null 2>&1; then
    ui_error "PRoot-Distro belum terpasang di Termux. Jalankan: pkg install -y proot-distro"
    ui_error "Lalu selesaikan fondasi Debian: fish $INSTALLER"
    return 127
  fi
  if [[ ! -d "$SDCARD_ROOT" || ! -d "$OUTPUT_ROOT" || ! -w "$OUTPUT_ROOT" ]]; then
    ui_error "SD card/output tidak tersedia atau tidak writable: $OUTPUT_ROOT"
    ui_error "Periksa izin Android dan akses kartu SD. Tidak ada fallback ke storage internal."
    return 125
  fi
  proot_bind_target_prepare || return 125

  local host_id guest_id
  host_id=$(stat -c '%d:%i' "$OUTPUT_ROOT" 2>/dev/null) || {
    ui_error "Gagal membaca identitas filesystem output Termux."
    return 125
  }
  guest_id=$(proot-distro login --bind "$OUTPUT_ROOT:$OUTPUT_ROOT" "$PROOT_DISTRO" -- stat -c '%d:%i' "$OUTPUT_ROOT" 2>/dev/null) || {
    ui_error "Debian gagal melihat output SD card melalui bind mount."
    return 125
  }
  if [[ "$host_id" != "$guest_id" ]]; then
    ui_error "Bind mount SD card TIDAK cocok. Termux=$host_id Debian=$guest_id"
    ui_error "Download diblokir agar file tidak masuk ke filesystem internal Debian."
    return 125
  fi
  return 0
}

proot_run() {
  proot_require || return $?
  proot_login "$@"
}

proot_shell() {
  proot_require || return $?
  proot-distro login --bind "$OUTPUT_ROOT:$OUTPUT_ROOT" "$PROOT_DISTRO"
}
