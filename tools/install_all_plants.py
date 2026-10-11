"""Install only garden_amd_full; preserve the accepted comparison and main mod."""
from pathlib import Path
import argparse,datetime,hashlib,shutil,subprocess
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--test',type=Path,required=True);p.add_argument('--mods',type=Path,required=True);args=p.parse_args()
if subprocess.run(['pgrep','-x','CoDWaW.exe'],capture_output=True).returncode==0:raise SystemExit('Close World at War before installing.')
source=args.test/'dist/garden_amd_full';target=args.mods/'garden_amd_full';backup=args.test/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
files=['mod.ff','nacht_garden.iwd','mod.arena'];assert all((source/n).is_file() for n in files)
target.mkdir(parents=True,exist_ok=True)
for name in files:
 dest=target/name
 if dest.exists():backup.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,backup/name)
 shutil.copy2(source/name,dest)
 assert hashlib.sha256((source/name).read_bytes()).digest()==hashlib.sha256(dest.read_bytes()).digest()
print('Installed and hash-verified only garden_amd_full.')
