#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "$0")" && pwd)"
task="$(cd -- "$root/.." && pwd)"
game="${WAW_GAME_DIR:?Set WAW_GAME_DIR}"
export NG_BUILD_HELD=1
python3 "$root/prepare_world.py"
if [[ "${NG_BUILD_HELD:-0}" == 1 ]]; then
for plant in peashooter sunflower wallnut cherrybomb potatomine chomper repeater squash lilypad tanglekelp; do
    bash "$task/tools/waw-tool.sh" converter -single xmodel "ng_held_$plant" -nopause > "$task/work/convert-$plant.log" 2>&1
    if rg -qi 'error:|aborting' "$task/work/convert-$plant.log"; then cat "$task/work/convert-$plant.log"; exit 1; fi
done
fi
bash "$task/tools/waw-tool.sh" linker_pc -nopause -language english ng_world > "$task/work/world-effects-build.log" 2>&1
cat "$task/work/world-effects-build.log"
# The original linker can return zero even after reporting asset errors.
if rg -qi 'error:' "$task/work/world-effects-build.log"; then
    echo 'World-effect compilation failed; existing package preserved.' >&2
    exit 1
fi
python3 "$root/prepare_maps.py"
for profile in nacht_garden; do
    "$task/tools/oat-run.sh" Linker --base-folder "$root" --asset-search-path "$root/map-profiles/$profile;$root/raw" --load "$game/zone/english/code_post_gfx.ff" --load "$game/zone/english/common.ff" --load "$game/zone/english/nazi_zombie_sumpf.ff" --load "$game/zone/english/nazi_zombie_factory.ff" --load "$task/work/modtools/zone/english/ng_world.ff" --output-folder "$root/build/$profile" "$profile"
done
python3 "$root/package.py"
