#!/usr/bin/env bash
set -euo pipefail
tool="${1:?Expected Linker, Unlinker or ImageConverter}"; shift
case "$tool" in Linker|Unlinker|ImageConverter) ;; *) exit 2;; esac
if [[ -n "${OAT_RUNNER:-}" ]]; then exec "$OAT_RUNNER" "$tool" "$@"; fi
exec "${OAT_BIN_DIR:?Set OAT_BIN_DIR or OAT_RUNNER}/$tool" "$@"
