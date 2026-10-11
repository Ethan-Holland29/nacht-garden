#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "$0")/.." && pwd)"
base="$repo/mod"
accepted="${NG_ACCEPTED_DEMO:-$repo/cloud/game-test}"
test="$repo/cloud/three-plants-test"
native="$repo/work/modtools"
game="${WAW_GAME_DIR:?Set WAW_GAME_DIR}"
accepted_native="${NG_ACCEPTED_NATIVE:-$native/zone/english/ng_amd_test.ff}"
python3 "$repo/cloud/build_three_plants.py" --base "$base" --accepted "$accepted" --native "$native" --output "$test" --cloud "$repo/cloud/amd-three-plants.zip" --source "$repo/cloud/three-plants-source.zip"
bash "$repo/tools/waw-tool.sh" linker_pc -nopause -language english ng_three_plants > "$repo/work/three-plants-native-build.log" 2>&1
if rg -qi 'error:|aborting' "$repo/work/three-plants-native-build.log"; then cat "$repo/work/three-plants-native-build.log"; exit 1; fi
bash "$repo/tools/oat-run.sh" Linker --base-folder "$test" --asset-search-path "$test/raw;$accepted/raw;$base/map-profiles/nacht_garden;$base/raw" --load "$game/zone/english/code_post_gfx.ff" --load "$game/zone/english/common.ff" --load "$game/zone/english/nazi_zombie_sumpf.ff" --load "$game/zone/english/nazi_zombie_factory.ff" --load "$native/zone/english/ng_world.ff" --load "$accepted_native" --load "$native/zone/english/ng_three_plants.ff" --output-folder "$test/build" garden_amd_plants
python3 "$repo/cloud/package_three_plants.py" --accepted "$accepted" --test "$test"
python3 "$repo/cloud/verify_three_plants.py" --cloud "$repo/cloud/amd-three-plants.zip" --test "$test"
