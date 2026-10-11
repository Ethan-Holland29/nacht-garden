"""List missing private inputs before running any asset preparation or linker."""
from pathlib import Path
import os, sys, shutil
ROOT = Path(__file__).resolve().parents[1]
needed = [
 'cloud/peashooter-source.zip', 'cloud/amd-attached-eyelids.zip',
 'work/stock-sprite.efx', 'work/common-callbacks.csc',
 'work/waw-materials/materials/rank_pvt1.json',
 'work/waw-materials/materials/gfx_fxt_misc_missing_fx.json',
 'work/betty-export/raw/model_export/viewmodel_bbetty_mine_lod0.xmodel_export',
 'work/sumpf-materials/materials/mc/mtl_foliage_cod5_grass05c_card_static.json',
 'work/factory-weapons/weapons/mine_bouncing_betty',
 'work/reference/sumpf-sounds.csv',
 'work/modtools/raw/materials/ng_test',
 'work/modtools/raw/material_properties/ng_held_peashooter',
 'work/modtools/bin/converter.exe', 'work/modtools/bin/linker_pc.exe',
]
missing = [name for name in needed if not (ROOT/name).is_file()]
for env, suffix in [('PVZ_GAME_DIR','main.pak'), ('WAW_GAME_DIR','zone/english/common.ff'),
                    ('WAW_GAME_DIR','zone/english/code_post_gfx.ff'),
                    ('WAW_GAME_DIR','zone/english/nazi_zombie_prototype.ff'),
                    ('WAW_GAME_DIR','zone/english/nazi_zombie_sumpf.ff'),
                    ('WAW_GAME_DIR','zone/english/nazi_zombie_factory.ff')]:
 if not os.environ.get(env) or not (Path(os.environ[env]).expanduser()/suffix).is_file():
  missing.append(f'{env}/{suffix}')
for env in ['WAW_WINE','WAW_WINEPREFIX']:
 if not os.environ.get(env): missing.append(env)
if not os.environ.get('OAT_RUNNER') and not os.environ.get('OAT_BIN_DIR'):
 missing.append('OAT_BIN_DIR or OAT_RUNNER')
if not shutil.which('ffmpeg'): missing.append('ffmpeg on PATH')
if missing:
 print('Private build inputs are missing. See docs/BUILD.md:')
 for name in missing: print(' - '+name)
 sys.exit(1)
print('Required private input files found. Native tool/runtime compatibility still requires a build.')
