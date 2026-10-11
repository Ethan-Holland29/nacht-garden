"""Install only the locally built Nacht comparison, with hash checks and backup."""
from pathlib import Path
import datetime, hashlib, os, shutil, subprocess

if __name__ == '__main__':
    root=Path(__file__).resolve().parents[1]
    source=root/'cloud/game-test/dist/garden_amd_test'
    files=['mod.ff','nacht_garden.iwd','mod.arena']
    if not all((source/n).is_file() for n in files):
        raise SystemExit('Build the demo first; see docs/BUILD.md.')
    if not os.environ.get('WAW_MODS_DIR'):
        raise SystemExit('Set WAW_MODS_DIR to your user-data CoDWaW/mods folder.')
    if not shutil.which('pgrep'):
        raise SystemExit('This installer requires Linux pgrep to check that the game is closed.')
    if subprocess.run(['pgrep','-x','CoDWaW.exe'],capture_output=True).returncode==0:
        raise SystemExit('Close World at War before installing.')
    target=Path(os.environ['WAW_MODS_DIR']).expanduser()/'garden_amd_test'
    backup=root/'private/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    target.mkdir(parents=True,exist_ok=True)
    for name in files:
        dest=target/name
        if dest.exists():
            backup.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dest,backup/name)
        shutil.copy2(source/name,dest)
        assert hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256((source/name).read_bytes()).digest()
    print('Installed comparison:',target,'Previous files, if present:',backup)
