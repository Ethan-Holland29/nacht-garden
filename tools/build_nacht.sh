#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "$0")/.." && pwd)"
python3 "$repo/tools/preflight.py"
bash "$repo/mod/build.sh"
bash "$repo/cloud/build_game_test.sh"
printf '%s\n' 'Built comparison: cloud/game-test/dist/garden_amd_test/' 'The mod/dist/nacht_garden package is a baseline intermediate; use the comparison package.'
