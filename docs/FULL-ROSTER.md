# Full roster AMD test

`garden_amd_full` is a separate Nacht test profile. It preserves the accepted recorded Peashooter comparison. The previous test loaded, but Doom-shroom and Potato Mine displayed default weapons and Chomper clipped through the floor. On 2026-10-10, the user confirmed the repaired plants place correctly and Chomper looks whole, and accepted this version.

## Changes

The AMD cloud pipeline resamples original motion tracks and composites original artwork using PyTorch/ROCm. This is offline asset processing, not real-time frame generation or FSR. AI assistance supports reverse engineering and game integration; neither game has been fully decompiled.

Twenty clips cover Sunflower, Repeater, Wall-nut, Cherry Bomb, Potato Mine, Chomper, Squash, Lily Pad and Tangle Kelp. Four more cover Doom-shroom idle, swelling, sleep and its original particle explosion. The sleep clip is available but unused for awake Doom-shroom in Nacht. Water-plant animation assets are processed; gameplay work on other maps remains deferred.

- Wall-nut no longer forces the twitch sequence at each loop or restarts its animation on every bite. Original normal blinks and cracked appearances remain.
- Potato Mine's packet and held artwork show its emerged pose. A newly planted mine still starts buried and arms after eight seconds.
- Pea projectiles use the same world units per original source pixel as Peashooter: about 2.52 times the previous diameter. Plants and the modified Carbine share this effect.
- Squash uses its original attack and landing artwork while its visual rises, moves above a target and slams down. The impact uses the same stock blood effects as Chomper and damages enemy AI only. Ceiling and wall traces constrain the jump.
- Doom-shroom costs 500 sun, has a 50-second recharge, uses original swelling, sound and DOOM explosion artwork, and calls Nacht's original nuke power-up routine. The nuke supplies its stock full-screen flash. The particle renderer follows the original XML parameters with deterministic sampling.

## Private build prerequisites

This is not a fresh-clone, one-command build. Follow `BUILD.md` to prepare the owned game inputs, native Mod Tools, conversion tools, stock zones and accepted Peashooter comparison. The held plants also depend on the prepared Betty model skeleton and original packet UI assets. Keep extracted artwork, sounds, rendered atlases and compiled packages private.

Extract the additional original inputs locally:

```bash
python3 tools/extract_all_plants.py --pak "/path/to/Plants Vs Zombies/main.pak"
python3 tools/extract_doomshroom.py --pak "/path/to/Plants Vs Zombies/main.pak"
```

The extractors create new ZIPs and refuse to overwrite existing ones. The roster bundle contains 143 original files; the Doom bundle contains 12.

In the private AMD workspace, place both bundles alongside `animation_lab.py`, `all_plants_cloud.py`, `doomshroom_cloud.py` and the clean `AMD_Full_Roster.ipynb`. Run the notebook on the ROCm GPU and download `amd-all-plants.zip` and `amd-doomshroom.zip` into local `cloud/`.

With `WAW_GAME_DIR` and `WAW_MODS_DIR` configured as documented in `BUILD.md`, build and install:

```bash
bash tools/build_all_plants.sh
python3 tools/install_all_plants.py --test cloud/all-plants-test --mods "$WAW_MODS_DIR"
bash tools/launch_all_plants.sh
```

Close WaW before installing. `NG_ACCEPTED_DEMO` may point to a preserved accepted snapshot containing `raw/`, `zone_source/` and `dist/`. `NG_ACCEPTED_NATIVE` may point to its `ng_amd_test.ff`. Defaults use `cloud/game-test` and `work/modtools/zone/english/ng_amd_test.ff`.

## Verification and remaining tests

All 1,358 exported frames across 24 clips matched their packed pixels. Original image resolution is retained; transparent padding is cropped, with uncompressed BGRA textures. Updated roster and Doom animation sheets use 70.86 MiB total, with the largest individual texture at 7.22 MiB. These values are texture payloads, not total game memory. All 86 accepted comparison images remain byte-identical. Original separate Tangle Kelp tendrils are retained rather than forced into one connected shape.

The private native build completed without linker warnings or errors. Nacht reached active gameplay and the user confirmed the map loaded. The user accepted the repaired build after confirming Doom-shroom and Potato Mine planting and Chomper appearance. All 11 packaged planting definitions now fit the original 8192-byte text limit. New rectangular effects explicitly enable independent width and height, preventing square stretching and the resulting Chomper floor clipping. All 1,358 new frames retain at least two transparent pixels at cell boundaries and match the cloud pixels. Detailed Doom nuke behavior, Squash combat and every damage state were not separately confirmed; acceptance does not imply exhaustive testing. Static script parsing is only a grammar check, not proof of WaW runtime behavior.

Use H to select, J to hold and left-click to plant. Test several loops and blinks, hurt Wall-nut through both crack stages, and check Potato Mine's packet, held pose and arming transition. Check Squash in open space near a zombie for rise, slam and blood. Check Doom-shroom for a 500-sun deduction, swelling, DOOM artwork, nuke and survival of nearby players. Check repeated planting, cooldowns, sounds and the game log for runtime errors. B/N retain the original Peashooter comparison controls.

Evidence JSON files distinguish cloud checks, packing checks and gameplay status. The historical 35.4× Peashooter processing benchmark does not apply to this expanded workload; no new speedup benchmark was measured. Portable source checks do not establish that a fresh-clone private toolchain build has been reproduced.
