#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "$0")/.." && pwd)"
base="$repo/mod"
accepted="${NG_ACCEPTED_DEMO:-$repo/cloud/game-test}"
test="$repo/cloud/all-plants-test"
native="$repo/work/modtools"
game="${WAW_GAME_DIR:?Set WAW_GAME_DIR}"
accepted_native="${NG_ACCEPTED_NATIVE:-$native/zone/english/ng_amd_test.ff}"
python3 "$repo/cloud/build_all_plants.py" --base "$base" --accepted "$accepted" --native "$native" --output "$test" --cloud "$repo/cloud/amd-all-plants.zip" --source "$repo/cloud/all-plants-source.zip"
python3 "$repo/cloud/prepare_potato_surface.py" --base "$base" --native "$native" --output "$test" --source "$repo/cloud/all-plants-source.zip"
python3 "$repo/cloud/prepare_doomshroom.py" --base "$base" --native "$native" --output "$test" --cloud "$repo/cloud/amd-doomshroom.zip" --source "$repo/cloud/doomshroom-source.zip" --ui-source "$repo/cloud/all-plants-source.zip"
for model in ng_held_potatomine_surface ng_held_doomshroom; do
    bash "$repo/tools/waw-tool.sh" converter -single xmodel "$model" -nopause > "$repo/work/convert-$model.log" 2>&1
    if rg -qi 'error:|aborting' "$repo/work/convert-$model.log"; then cat "$repo/work/convert-$model.log"; exit 1; fi
done
bash "$repo/tools/waw-tool.sh" linker_pc -nopause -language english ng_full_plants > "$repo/work/all-plants-native-build.log" 2>&1
if rg -qi 'error:|aborting' "$repo/work/all-plants-native-build.log"; then cat "$repo/work/all-plants-native-build.log"; exit 1; fi
bash "$repo/tools/oat-run.sh" Linker --base-folder "$test" --asset-search-path "$test/raw;$accepted/raw;$base/map-profiles/nacht_garden;$base/raw" --load "$game/zone/english/code_post_gfx.ff" --load "$game/zone/english/common.ff" --load "$game/zone/english/nazi_zombie_sumpf.ff" --load "$game/zone/english/nazi_zombie_factory.ff" --load "$native/zone/english/ng_world.ff" --load "$accepted_native" --load "$native/zone/english/ng_full_plants.ff" --output-folder "$test/build" garden_amd_full
python3 "$repo/cloud/package_all_plants.py" --accepted "$accepted" --test "$test"
python3 "$repo/cloud/verify_all_plants.py" --cloud "$repo/cloud/amd-all-plants.zip" --test "$test"
python3 "$repo/cloud/verify_doomshroom.py" --cloud "$repo/cloud/amd-doomshroom.zip" --test "$test"
