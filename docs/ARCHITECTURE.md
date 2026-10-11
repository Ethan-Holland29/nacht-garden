# Architecture

The integration keeps the original WaW executable and rendering engine. GSC code implements plant selection, placement checks, sun costs, plant attacks and interactions with zombies. Stock scripts are extracted from local fastfiles and patched by preparation code; their full source is not included here.

Original PvZ art and reanimation tracks are decoded locally. The general converter composes those tracks into sprites. The AMD experiment uploads only the minimal Peashooter source bundle to a private workspace, interpolates numeric transforms with PyTorch/ROCm and composites sprites with premultiplied-alpha sampling. Sprite identity and visibility remain discrete.

The accepted body loop uses 25 original poses with independent original blink states. Each fractional eyelid pose follows the current face matrix multiplied by the inverse bind matrix and the original blink matrix. Shooting uses body-only stem poses and a separate local attachment correction. No new artwork is drawn.

Native WaW tools compile FX, loaded original PCM sound aliases and held plant models. OAT links the game-facing materials and scripts. The comparison package keeps old idle on the left and corrected idle on the right; it is a full-pipeline comparison, not a sample-rate-only experiment.

The old idle loop lasts 2,333 ms; the accepted continuous body loop lasts 2,083 ms. Both comparison plants use the same corrected local shooting and gameplay. The recorded test's plant sizes are matched, while uncompressed animation pixels are preserved when empty texture margins are removed.

Cloud processing finishes before gameplay. The local game does not contact the cloud. ROCm is not running inside WaW, and this project does not integrate FSR.
