# Measurements and validation

## Initial cloud renderer benchmark

| Measurement | Result |
| --- | ---: |
| GPU | AMD Radeon Pro W7900D |
| VRAM | Approximately 48 GiB |
| CPU configuration | 8 PyTorch threads |
| CPU median for 16 frames | 1.388190 s |
| GPU median for 16 frames | 0.039186 s |
| CPU/GPU median ratio | 35.426× |
| Maximum CPU/GPU premultiplied-channel error | 0.00000656 on a 0–1 scale |

The initial test used the same renderer and 16 phase samples at 512×512 on both devices, one warm-up and three measured trials. GPU completion was synchronized and textures were already resident. Upload, readback, encoding and networking were excluded. This predates the final attachment repair. It is a renderer benchmark, not game FPS or end-to-end speedup.

`cloud-results.json` is the unchanged historical result. Its scope text refers to the experiment at measurement time, before subsequent in-game integration.

## Accepted final animation

`repair-validation.json` records no disconnected large components in the tested idle/shooting frames and a final-to-first pixel-difference metric of approximately 0.00622. These are asset checks, not gameplay proof.

`game-test-runtime-verification.json` records the developer's visual acceptance of the final Nacht comparison. `game-test-package-sha256.json` identifies the exact private package used for that demo. Package hashes allow comparison; the packages and original artwork are not distributed here.

The recorded comparison includes changes to renderer, sample rate, loop structure and attachment behavior. It does not isolate sample rate alone. The final right-hand idle has 125 frames at 60 animation samples/sec, a 2,083 ms loop and a 3.125 MiB uncompressed texture. The left-hand prior loop is 2,333 ms at 12 samples/sec. Both use locally corrected 24-sample/sec shooting.
