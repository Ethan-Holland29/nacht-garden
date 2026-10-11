#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "$0")" && pwd)"
task="$(cd -- "$root/.." && pwd)"
base="$task/mod"
game="${WAW_GAME_DIR:?Set WAW_GAME_DIR}"
python3 "$root/build_game_test.py"
bash "$task/tools/waw-tool.sh" linker_pc -nopause -language english ng_amd_test > "$task/work/amd-test-native-build.log" 2>&1
if rg -qi 'error:|aborting' "$task/work/amd-test-native-build.log"; then cat "$task/work/amd-test-native-build.log"; exit 1; fi
bash "$task/tools/oat-run.sh" Linker --base-folder "$root/game-test" --asset-search-path "$root/game-test/raw;$base/map-profiles/nacht_garden;$base/raw" --load "$game/zone/english/code_post_gfx.ff" --load "$game/zone/english/common.ff" --load "$game/zone/english/nazi_zombie_sumpf.ff" --load "$game/zone/english/nazi_zombie_factory.ff" --load "$task/work/modtools/zone/english/ng_world.ff" --load "$task/work/modtools/zone/english/ng_amd_test.ff" --output-folder "$root/game-test/build" garden_amd_test
python3 "$root/package_game_test.py"
