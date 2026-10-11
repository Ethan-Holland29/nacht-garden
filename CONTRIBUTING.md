# Contributing

Current scope is the accepted Nacht proof of concept. Other maps are paused. Preserve the original-art constraint and keep the recorded demo separate from experimental changes.

Before committing:

```bash
python3 tools/check_repo.py
```

Run syntax and asset checks for the change, then separately record any in-game validation. Never describe a clean build as proof of runtime compatibility. Keep benchmark setup, exclusions and original trial values alongside performance claims.

Do not commit game archives, extracted stock scripts, artwork, sound, compiled mods, native tool binaries, local paths/credentials or notebook outputs. Run notebooks in a private working copy or clear outputs before saving. Do not force-add ignored generated files.

No project-wide license has been chosen. Discuss the intended license with the project maintainers before adding a license or importing third-party code.
