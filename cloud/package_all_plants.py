"""Package the new isolated profile without modifying the accepted demo."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--accepted',type=Path,required=True);p.add_argument('--test',type=Path,required=True);args=p.parse_args()
a=args.accepted;t=args.test;dest=t/'dist/garden_amd_full';dest.mkdir(parents=True,exist_ok=True)
source=a/'dist/garden_amd_test/nacht_garden.iwd';before=hashlib.sha256(source.read_bytes()).hexdigest()
def compact_weapon(data):
 # The native linker accepts the full definition, but WaW's IWD text reader
 # has an 8192-byte limit. Match the working base packager for every override.
 fields=data.decode().split('\\');weapon=dict(zip(fields[1::2],fields[2::2]))
 compact='WEAPONFILE'+''.join('\\'+k+'\\'+v for k,v in weapon.items() if v and not k.lower().startswith('ads'))
 assert len(compact.encode())<8192
 return compact.encode()
shutil.copy2(t/'build/mod.ff',dest/'mod.ff')
with zipfile.ZipFile(source) as src,zipfile.ZipFile(dest/'nacht_garden.iwd','w',zipfile.ZIP_DEFLATED) as out:
 for info in src.infolist():
  data=src.read(info.filename)
  if info.filename in ['maps/_nacht_garden.gsc','maps/_nacht_garden_assets.gsc','clientscripts/_callbacks.csc']:data=(t/'raw'/info.filename).read_bytes()
  override=t/'raw/weapons'/Path(info.filename).name
  if info.filename.startswith('weapons/sp/') and override.is_file():data=compact_weapon(override.read_bytes())
  out.writestr(info,data)
 for file in sorted((t/'raw/images').glob('*.iwi')):out.write(file,'images/'+file.name)
 for file in sorted((t/'raw/weapons').iterdir()):
  name='weapons/sp/'+file.name
  if name not in src.namelist():out.writestr(name,compact_weapon(file.read_bytes()))
 out.writestr('all_plants_test.txt','Separate AMD animation test. Full roster plus Doom-shroom (500 sun/native nuke); Squash slam; larger peas; Wall-nut twitch removed; surfaced Potato Mine packet/held art. H/J/fire/K/L controls. Accepted Peashooter comparison B/N retained. Runtime validation pending.\n')
(dest/'mod.arena').write_text('{\n mod "garden_amd_full"\n name "Garden AMD Full Roster Test"\n description "Nacht: full plant animation test"\n}\n')
with zipfile.ZipFile(source) as old,zipfile.ZipFile(dest/'nacht_garden.iwd') as new:
 assert new.testzip() is None
 for name in old.namelist():
  if name.startswith('images/'):assert old.read(name)==new.read(name),name
 assert len([n for n in new.namelist() if n.startswith('images/')])==86+len(list((t/'raw/images').glob('*.iwi')))
 assert len(new.namelist())==len(set(new.namelist()))
 weapons={}
 for name in new.namelist():
  if name.startswith('weapons/sp/ng_seed_'):
   data=new.read(name);assert data.startswith(b'WEAPONFILE') and len(data)<8192,(name,len(data))
   fields=data.decode().split('\\');values=dict(zip(fields[1::2],fields[2::2]))
   override=t/'raw/weapons'/Path(name).name
   if override.is_file():assert data==compact_weapon(override.read_bytes()),name
   assert values['gunModel'].startswith('ng_held_'),name
   assert values['fireAnim']=='viewmodel_bbetty_fire',name
   weapons[Path(name).name]={'text_bytes':len(data),'below_8192_byte_limit':True,'gun_model':values['gunModel'],'original_betty_fire_animation':True}
 assert len(weapons)==11,len(weapons)
(t/'weapon-validation.json').write_text(json.dumps(weapons,indent=2)+'\n')
assert before==hashlib.sha256(source.read_bytes()).hexdigest()
(t/'package-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in dest.iterdir() if f.is_file()},indent=2)+'\n')
print('Packaged isolated test: all 86 accepted image files unchanged; lossless roster and Doom-shroom atlases plus original packet/held images. CRC checks passed.')
