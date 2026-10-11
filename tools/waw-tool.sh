#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "$0")/.." && pwd)"
tool="${1:?Expected converter or linker_pc}"; shift
case "$tool" in converter|linker_pc) ;; *) echo 'Unsupported native tool' >&2; exit 2;; esac
: "${WAW_WINE:?Set WAW_WINE to a Wine executable}"
: "${WAW_WINEPREFIX:?Set a dedicated private mod-tools prefix}"
cd "$repo/work/modtools/bin"
args=(env "WINEPREFIX=$WAW_WINEPREFIX" 'WINEDLLOVERRIDES=d3dx9_37=n' 'WINEDEBUG=-all' "$WAW_WINE" "$PWD/$tool.exe" "$@")
if [[ -n "${WAW_RUNTIME:-}" ]]; then exec "$WAW_RUNTIME" -- "${args[@]}"; fi
exec "${args[@]}"
