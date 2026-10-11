#!/usr/bin/env bash
set -euo pipefail
exec "${STEAM_BIN:-steam}" -applaunch 10090 +set fs_game mods/garden_amd_test +set developer 1 +set logfile 2 +set ng_audit 0 +exec nacht_garden.cfg +map nazi_zombie_prototype
