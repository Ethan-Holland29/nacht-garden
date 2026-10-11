# Reproduce the AMD experiment

1. Use your installed desktop Plants vs. Zombies `main.pak` to extract the minimal source bundle:

   ```bash
   python3 tools/extract_peashooter.py --pak "/path/to/Plants Vs Zombies/main.pak"
   ```

   This writes `cloud/peashooter-source.zip`, verifies the supported archive structure and includes SHA-256 provenance for 14 original files. It refuses to overwrite an existing bundle.

2. Use a ROCm-enabled PyTorch environment on an AMD GPU. Install the packages in `requirements.txt` if missing. PyTorch is deliberately not installed from a generic CPU/CUDA wheel: use the ROCm build provided by your cloud environment or appropriate AMD/PyTorch setup instructions.

3. In your private Jupyter workspace, put `cloud/AMD_Cloud_Animation_Lab.ipynb` beside `peashooter-source.zip`. The notebook is self-contained. Run all cells in order. Uploading the source bundle sends original game assets to that workspace; keep its access private.

4. The notebook checks the GPU and source hashes, compares CPU/GPU numerical output, benchmarks the renderer, exports previews, then runs the final continuous-body/attached-eyelid repair. The last cell produces `amd-attached-eyelids.zip` containing 125 original-art PNG frames and a report. Download it to `cloud/` for the private game build.

5. Inspect the animation and report. A new export does not establish in-game compatibility. The recorded accepted run is described in `evidence/`; automatic checks supplement visual checks.

The clean notebook has no outputs or embedded artwork. Running it populates outputs with game artwork. Clear every cell's output and execution count before committing; `tools/check_repo.py` rejects notebooks with outputs or attachments. Keep generated images, previews and ZIPs out of Git. `.gitignore` covers these files, but it cannot remove files already tracked or deliberately force-added.

Tested cloud environment: Radeon Pro W7900D, approximately 48 GiB VRAM, PyTorch 2.13.0+rocm10.0.0, reported ROCm 7.15.26333. These describe the measured environment, not universal installation requirements.
