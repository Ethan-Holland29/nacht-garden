# Build the Nacht comparison locally

The validated game build used Linux, Steam Proton, the original WaW mod tools and OpenAssetTools (OAT). The clean repository excludes all game content and tool binaries. Native toolchain preparation remains a manual prerequisite; a new clone is not a one-command game installer.

## Configure paths

Copy `.env.example` to `.env.local`, fill in your own absolute paths, then load your local configuration:

```bash
set -a
source .env.local
set +a
python3 tools/preflight.py
```

`WAW_GAME_DIR` and `PVZ_GAME_DIR` point to installed game folders. `WAW_WINE` and `WAW_WINEPREFIX` select the dedicated mod-tools Wine environment. `WAW_RUNTIME` optionally wraps it with a compatibility runtime. OAT can be selected through `OAT_BIN_DIR` or an `OAT_RUNNER` wrapper for the platform's loader. Use Python with Pillow and FFmpeg for conversion.

## Private preparation

Keep all prepared game-derived files and binaries under the ignored `work/` directory. Use your local WaW files and mod tools to prepare the inputs listed by `tools/preflight.py`:

- Native mod tools at `work/modtools`, including their normal runtime data and GDT definitions.
- Original material templates at `work/waw-materials/materials/` and `work/sumpf-materials/materials/`.
- Original Betty model export and weapon definition at `work/betty-export/` and `work/factory-weapons/`.
- Original sprite effect template `work/stock-sprite.efx` and sound-alias header `work/reference/sumpf-sounds.csv`.
- Native atlas-material and held-material-property seed files in the mod-tools raw directory.
- Original common client callbacks extracted as `work/common-callbacks.csc`.

These are private inputs from the development toolchain, not downloadable files in this repository. Preflight checks their presence; it does not certify their formats or native tool compatibility. The pipeline loads common, Nacht, Shi No Numa and Der Riese stock fastfiles as asset dependencies even though only Nacht is built for play.

Complete [the cloud experiment](CLOUD.md) to supply `cloud/peashooter-source.zip` and `cloud/amd-attached-eyelids.zip`.

## Build and install

```bash
bash tools/build_nacht.sh
python3 tools/install_demo.py
bash tools/launch_nacht.sh
```

Close WaW before installation. The installer writes only `garden_amd_test` under `WAW_MODS_DIR` and backs up preceding files under ignored `private/backups/`. Steam may show a launch confirmation.

The build first creates a private baseline under `mod/dist/nacht_garden`, then compiles the corrected comparison under `cloud/game-test/dist/garden_amd_test`. **Install the comparison package.** The baseline is an intermediate for the before/after demonstration and retains earlier animation/audio behavior.

The accepted local demo used T4M Enhanced r48 for increased asset limits and a large-address-aware game executable. These runtime prerequisites are not bundled or installed by this source repository. The original CoD engine is retained. Keep your own game backups before configuring that runtime.

The folder reorganization, notebook cleanup and path configuration have been checked statically. The accepted game runtime came from the original private workspace; this exported repository has not had a fresh native end-to-end build. Check build logs, source-image preservation, in-engine loading, placement, sounds and animation before replacing an accepted demo.
