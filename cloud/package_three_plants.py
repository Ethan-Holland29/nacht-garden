"""Package the new isolated profile without modifying the accepted demo."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--accepted',type=Path,required=True);p.add_argument('--test',type=Path,required=True);args=p.parse_args()
a=args.accepted;t=args.test;dest=t/'dist/garden_amd_plants';dest.mkdir(parents=True,exist_ok=True)
source=a/'dist/garden_amd_test/nacht_garden.iwd';before=hashlib.sha256(source.read_bytes()).hexdigest()
shutil.copy2(t/'build/mod.ff',dest/'mod.ff')
with zipfile.ZipFile(source) as src,zipfile.ZipFile(dest/'nacht_garden.iwd','w',zipfile.ZIP_DEFLATED) as out:
 for info in src.infolist():
  data=src.read(info.filename)
  if info.filename in ['maps/_nacht_garden.gsc','maps/_nacht_garden_assets.gsc','clientscripts/_callbacks.csc']:data=(t/'raw'/info.filename).read_bytes()
  out.writestr(info,data)
 for file in sorted((t/'raw/images').glob('*.iwi')):out.write(file,'images/'+file.name)
 out.writestr('three_plants_test.txt','Separate AMD animation test. Sunflower idle/blink; Repeater idle/blink/shoot; Wall-nut healthy and both cracked loops. H/J/fire/K/L controls. Accepted Peashooter comparison B/N retained. Runtime validation pending.\n')
(dest/'mod.arena').write_text('{\n mod "garden_amd_plants"\n name "Garden AMD Plant Test"\n description "Nacht: Sunflower, Wall-nut and Repeater animation test"\n}\n')
with zipfile.ZipFile(source) as old,zipfile.ZipFile(dest/'nacht_garden.iwd') as new:
 assert new.testzip() is None
 for name in old.namelist():
  if name.startswith('images/'):assert old.read(name)==new.read(name),name
 assert len([n for n in new.namelist() if n.startswith('images/')])==92
 assert len(new.namelist())==len(set(new.namelist()))
assert before==hashlib.sha256(source.read_bytes()).hexdigest()
(t/'package-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in dest.iterdir() if f.is_file()},indent=2)+'\n')
print('Packaged isolated test: all 86 accepted image files unchanged; six additional lossless atlases. CRC checks passed.')
