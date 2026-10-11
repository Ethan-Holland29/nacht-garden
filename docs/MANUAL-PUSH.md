# Manual commit: accepted AMD full roster version

The user accepted the current Nacht proof of concept on 2026-10-10, specifically confirming Doom-shroom and Potato Mine planting and Chomper's complete sprite. Detailed nuke/slam behavior and every damage state were not separately confirmed. The earlier recorded Peashooter demo remains unchanged.

All 45 files below are updated locally. The assistant has not staged, committed or pushed them. This list includes the previous three-plant expansion because it is still uncommitted, plus the full roster pipeline and final repairs.

## Review these files

- `.gitignore`
- `README.md`
- `cloud/AMD_Full_Roster.ipynb`
- `cloud/AMD_Three_Plants.ipynb`
- `cloud/all_plants_cloud.py`
- `cloud/apply_doom_gameplay.py`
- `cloud/apply_roster_gameplay.py`
- `cloud/build_all_plants.py`
- `cloud/build_three_plants.py`
- `cloud/doomshroom_cloud.py`
- `cloud/package_all_plants.py`
- `cloud/package_three_plants.py`
- `cloud/prepare_doomshroom.py`
- `cloud/prepare_potato_surface.py`
- `cloud/three_plants_cloud.py`
- `cloud/verify_all_plants.py`
- `cloud/verify_doomshroom.py`
- `cloud/verify_three_plants.py`
- `docs/FULL-ROSTER.md`
- `docs/MANUAL-PUSH.md`
- `docs/THREE-PLANTS.md`
- `evidence/all-plants-build.json`
- `evidence/all-plants-cloud-report.json`
- `evidence/all-plants-frame-validation.json`
- `evidence/all-plants-validation.json`
- `evidence/doomshroom-build.json`
- `evidence/doomshroom-cloud-report.json`
- `evidence/doomshroom-frame-validation.json`
- `evidence/plant-weapon-validation.json`
- `evidence/potato-surface.json`
- `evidence/three-plants-build.json`
- `evidence/three-plants-cloud-report.json`
- `evidence/three-plants-frame-validation.json`
- `evidence/three-plants-validation.json`
- `mod/prepare_world.py`
- `mod/raw/maps/_nacht_garden.gsc`
- `tools/build_all_plants.sh`
- `tools/build_three_plants.sh`
- `tools/extract_all_plants.py`
- `tools/extract_doomshroom.py`
- `tools/extract_three_plants.py`
- `tools/install_all_plants.py`
- `tools/install_three_plants.py`
- `tools/launch_all_plants.sh`
- `tools/launch_three_plants.sh`

## Check the source package

Run from the repository folder:

```bash
python3 tools/check_repo.py
git diff --check
git status --short
```

## Stage the files individually

Run the following lines one at a time or paste the whole block. Each command stages one named file, so unrelated files are not included.

```bash
git add -- .gitignore
git add -- README.md
git add -- cloud/AMD_Full_Roster.ipynb
git add -- cloud/AMD_Three_Plants.ipynb
git add -- cloud/all_plants_cloud.py
git add -- cloud/apply_doom_gameplay.py
git add -- cloud/apply_roster_gameplay.py
git add -- cloud/build_all_plants.py
git add -- cloud/build_three_plants.py
git add -- cloud/doomshroom_cloud.py
git add -- cloud/package_all_plants.py
git add -- cloud/package_three_plants.py
git add -- cloud/prepare_doomshroom.py
git add -- cloud/prepare_potato_surface.py
git add -- cloud/three_plants_cloud.py
git add -- cloud/verify_all_plants.py
git add -- cloud/verify_doomshroom.py
git add -- cloud/verify_three_plants.py
git add -- docs/FULL-ROSTER.md
git add -- docs/MANUAL-PUSH.md
git add -- docs/THREE-PLANTS.md
git add -- evidence/all-plants-build.json
git add -- evidence/all-plants-cloud-report.json
git add -- evidence/all-plants-frame-validation.json
git add -- evidence/all-plants-validation.json
git add -- evidence/doomshroom-build.json
git add -- evidence/doomshroom-cloud-report.json
git add -- evidence/doomshroom-frame-validation.json
git add -- evidence/plant-weapon-validation.json
git add -- evidence/potato-surface.json
git add -- evidence/three-plants-build.json
git add -- evidence/three-plants-cloud-report.json
git add -- evidence/three-plants-frame-validation.json
git add -- evidence/three-plants-validation.json
git add -- mod/prepare_world.py
git add -- mod/raw/maps/_nacht_garden.gsc
git add -- tools/build_all_plants.sh
git add -- tools/build_three_plants.sh
git add -- tools/extract_all_plants.py
git add -- tools/extract_doomshroom.py
git add -- tools/extract_three_plants.py
git add -- tools/install_all_plants.py
git add -- tools/install_three_plants.py
git add -- tools/launch_all_plants.sh
git add -- tools/launch_three_plants.sh
```

## Review, commit and push

Review what will be committed:

```bash
git diff --cached --stat
git diff --cached --check
```

Then create and push your commit:

```bash
git commit -m "Add AMD full-roster animation pipeline and repair plant sprites"
git push origin main
```

If Git reports new remote work, stop and integrate it before retrying; do not force-push. Git pushes commits rather than loose files. For GitHub website uploads, preserve the relative folder paths listed above and include the related source files together.

Only source, clean notebooks, documentation and text evidence are included. Original artwork, sounds, private source ZIPs, rendered sprite ZIPs and compiled game packages remain excluded. The source allows the animation processing and mod to be rebuilt with the documented private inputs; GitHub does not receive the rendered game assets. See `FULL-ROSTER.md` for prerequisites and the test scope.
