log_info() { printf '[%s] INFO %s\n' "$(date '+%F %T')" "$*" >> "$LOG_DIR/downloader.log"; }
log_error() { printf '[%s] ERROR %s\n' "$(date '+%F %T')" "$*" >> "$LOG_DIR/downloader.log"; }
