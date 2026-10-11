# Nacht Garden

A project using AI assisted reverse engineering to combine Plants vs. Zombies with Nacht Der Untoten zombies.

**Plants vs. Zombies mechanics inside Call of Duty: World at War, with original animations processed on AMD Radeon cloud hardware.**

Nacht Garden is a solo proof of concept on **Nacht der Untoten**, running in the original World at War engine. It combines placeable plants, sun, a seed bank and pea attacks with first-person Zombies gameplay. Players place plants using the original Bouncing Betty hand animation.

The project has two equal parts: **AI-assisted game integration** and **AMD ROCm cloud animation processing**. Original game artwork and sounds are used locally; no replacement artwork or audio is generated.

## The demo

The recorded comparison places the previous mod's Peashooter beside the AMD-enhanced version. The accepted animation has smoother idle motion, a continuous body cycle and original eyelids attached to the moving face. Its 125 samples play at 60 animation samples per second inside the existing engine.

| Control | Action |
| --- | --- |
| H | Cycle plants and None |
| J, then left-click | Hold and plant using the Betty animation |
| K / L | Shovel / select None |
| B | Place the comparison pair on clear, level floor |
| N | Toggle shooting for the comparison pair |

Left/right are relative to the placement view. The comparison starts with shooting paused and 2,000 sun; zombies remain active.

## AMD's role

PyTorch/ROCm on a Radeon Pro W7900D interpolates original animation transforms and composites original sprite layers. The cloud exports assets for local playback. This is **cloud asset processing**, not FSR, live game-frame generation or remote gameplay streaming.

The initial controlled renderer benchmark measured **35.4× GPU/CPU rendering speedup**: 0.03919 s versus 1.38819 s for a 16-frame batch. This is not a game-FPS or end-to-end result. See [measurements and limitations](evidence/README.md).

The final idle atlas is uncompressed and uses 3.125 MiB. Only empty margins were trimmed. Shooting uses a separate, locally rendered attachment correction; the AMD claim covers the idle animation.

## Repository contents

```text
cloud/       ROCm renderer, clean notebook and comparison builder
mod/         Gameplay integration and original-asset conversion code
tools/       Extraction, build, installation and repository checks
evidence/    Numeric measurements, quality checks and accepted demo hashes
docs/        Build requirements, architecture, demo and contribution notes
```

Start with [the cloud experiment](docs/CLOUD.md) or [the game build requirements](docs/BUILD.md). Run `python3 tools/check_repo.py` to check the source folder without either game or a GPU.

This is a **source-only research repository**, not a ready-to-install game download. Game assets, extracted stock scripts, native mod tools, compiled packages, recordings and executed notebook outputs are excluded. The cloud experiment can be reproduced with a local PvZ copy and a compatible ROCm environment. Building the game demo additionally requires a prepared private WaW/OAT toolchain; that setup is not automated from a fresh clone.

## Current scope

The final Nacht comparison was visually accepted and recorded. Work on other maps is paused. Custom maps, co-op and exhaustive combat/balance testing are outside this proof of concept. The full roster animation expansion is described below. We used AI-assisted analysis and integration; we did not fully decompile or rebuild either entire game engine.

See [demo steps](docs/DEMO.md), [third-party components](THIRD_PARTY.md) and [contribution guidance](CONTRIBUTING.md). This repository does not grant rights to the original games or their assets. No project-wide code license has been selected yet.

## Three-plant AMD expansion

A separate Nacht test now includes GPU-rendered Sunflower idle/blink, Repeater idle/blink and shooting, and Wall-nut healthy/damaged loops. All 606 packed frames passed pixel-preservation and connectivity checks. The replacement textures use 17.223 MiB versus 18 MiB previously, without downscaling or lossy compression. The separate profile reached active gameplay, and the user confirmed the three plants’ animations look good. Full combat and damage-state testing remains separate. The accepted recorded Peashooter demo remains unchanged. See [the expansion and test instructions](docs/THREE-PLANTS.md).


## Full roster test and Doom-shroom

The separate `garden_amd_full` Nacht profile extends the AMD pipeline to the remaining existing plant animations and adds Doom-shroom: 500 sun, original swelling and DOOM particle artwork, original sound, Betty planting, and the stock Nacht nuke power-up. Squash now rises above its target and slams down with the existing Chomper blood effects; area damage still targets enemy AI only. Wall-nut no longer forces the twitch every loop or restarts a blink on each bite. Potato Mine's packet and held sprite use its emerged pose. Pea projectiles use the Peashooter's original source-pixel scale, increasing their diameter about 2.52 times.

All 1,358 newly exported frames passed lossless packing checks. The private native build passed, and the separate profile reached active Nacht gameplay. The follow-up build fixes oversized Doom/Potato weapon text and enables independent sprite width/height to prevent stretching and floor clipping. All 11 packaged weapon definitions pass the text limit, and all new frames pass cell-border checks. On 2026-10-10, the user confirmed Doom-shroom and Potato Mine plant correctly, Chomper looks whole, and accepted this version. Detailed nuke/slam behavior and every damage state were not separately confirmed. The accepted recorded Peashooter profile and prior three-plant test remain separate. Water-plant assets are processed, but other-map gameplay remains deferred. See [full roster build and test instructions](docs/FULL-ROSTER.md) and the [manual push checklist](docs/MANUAL-PUSH.md).
