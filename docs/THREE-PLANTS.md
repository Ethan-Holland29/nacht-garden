# AMD expansion: Sunflower, Wall-nut and Repeater

This is a separate Nacht test profile, `garden_amd_plants`. It leaves the accepted recorded Peashooter demo and normal profiles unchanged. All source updates are local for manual review and push.

## What changed

| Clip | Animation samples/sec | Frames | Texture memory |
| --- | ---: | ---: | ---: |
| Sunflower idle/blink | 60 | 125 | 3.125 MiB |
| Repeater idle/blink | 60 | 125 | 3.773 MiB |
| Repeater shooting | 48 | 50 | 1.887 MiB |
| Wall-nut healthy loop | 24 | 102 | 2.813 MiB |
| Wall-nut cracked stage 1 | 24 | 102 | 2.813 MiB |
| Wall-nut cracked stage 2 | 24 | 102 | 2.813 MiB |

All six clips were rendered on the Radeon Pro W7900D through ROCm. These rates are animation samples, not gameplay FPS. Wall-nut uses twice the previous sampling rate while retaining original image resolution and all three original blink/twitch sequences. Its body continues through those events instead of restarting between them. Its new loop lasts 4,250 ms; Sunflower and Repeater idle last 2,083 ms. Repeater shooting preserves the existing 1,042 ms duration and game attack timing.

Sunflower's original eyelids follow its moving head. Repeater eyelids follow the face, and shooting tracks follow the original stem attachment. Wall-nut overlays follow the face/body through both damage appearances. No artwork or sound was synthesized.

Combined replacement textures use **17.223 MiB versus 18 MiB previously**. Each sheet is under 4 MiB. Transparent padding was removed without downscaling or lossy compression. World scale and anchor offsets are derived from the original source-pixel coordinates. The final effect count remains 30, matching the accepted comparison package.

## Reproduce

1. Extract the 50 original source files locally:

   ```bash
   python3 tools/extract_three_plants.py --pak "/path/to/Plants Vs Zombies/main.pak"
   ```

2. In your private AMD workspace, place the ZIP, `cloud/animation_lab.py` and `cloud/three_plants_cloud.py` beside `cloud/AMD_Three_Plants.ipynb`. Run the notebook. Download `amd-three-plants.zip` into local `cloud/`. The original source and generated frames remain excluded from Git.

3. Prepare the private toolchain and Peashooter comparison build described in `BUILD.md`. Then run:

   ```bash
   bash tools/build_three_plants.sh
   python3 tools/install_three_plants.py --test cloud/three-plants-test --mods "$WAW_MODS_DIR"
   bash tools/launch_three_plants.sh
   ```

   Close WaW before installation. `NG_ACCEPTED_DEMO` may point to a preserved accepted snapshot with `raw/`, `zone_source/` and `dist/`; `NG_ACCEPTED_NATIVE` may point to its preserved `ng_amd_test.ff`. Defaults use the private comparison build in `cloud/game-test` and the native zone in `work/modtools`.

## Test and evidence

The six-clip package built with zero linker warnings/errors. All 606 packed frames matched the GPU-rendered pixel data; the connectivity check found no large disconnected components. CPU/GPU numerical and attachment checks passed. All 86 accepted image files remain byte-identical; six new images are added. The game reached active Nacht gameplay in its log. **The user visually accepted the three plants on 2026-10-10 (“They look good”), including the question about Repeater shooting and attachment. Exhaustive combat and all Wall-nut damage-state tests remain unverified.**

Use H to select each plant, J to hold and left-click to place. Check several idle loops, blinking, Repeater shooting and Wall-nut's damaged appearances. Check floor alignment and sound. B/N still control the original Peashooter comparison; they are not a before/after comparison for these three plants. Other plants are unchanged.

Reports in `evidence/three-plants-*.json` distinguish cloud, packing and runtime checks. The previous 35.4× benchmark applies only to its original Peashooter workload; no speedup claim was measured for this expansion. Frame rendering/readback timings in the new cloud report exclude later PNG/WebP packing.

The repository export was checked for syntax and clean notebooks. Actual native build and runtime checks used the private development workspace; portable fresh-clone toolchain setup still requires the documented private inputs.
