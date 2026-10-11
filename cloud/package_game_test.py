from pathlib import Path
import zipfile,shutil,hashlib,json
root=Path(__file__).resolve().parent;base=root.parent/'mod';test=root/'game-test';dest=test/'dist/garden_amd_test';dest.mkdir(parents=True,exist_ok=True)
baseline_iwd=base/'backups/pre-amd-integration-2026-10-10/nacht_garden/nacht_garden.iwd'
if not baseline_iwd.exists():baseline_iwd=base/'dist/nacht_garden/nacht_garden.iwd'
shutil.copy2(test/'build/mod.ff',dest/'mod.ff')
with zipfile.ZipFile(baseline_iwd) as src,zipfile.ZipFile(dest/'nacht_garden.iwd','w') as out:
 overrides={'maps/_nacht_garden.gsc','maps/_nacht_garden_assets.gsc'}
 for info in src.infolist():
  data=(test/'raw'/info.filename).read_bytes() if info.filename in overrides else src.read(info.filename)
  if info.filename=='nacht_garden.cfg':data+=b'\nbind B "set ng_action compare"\nbind N "set ng_action compare_fire"\n'
  out.writestr(info,data)
 for part in json.loads((root/'game-test-build.json').read_text())['texture_parts']:
  name='images/'+part['image']+'.iwi'
  out.write(test/'raw'/name,name,compress_type=zipfile.ZIP_DEFLATED)
 out.write(test/'raw/clientscripts/_callbacks.csc','clientscripts/_callbacks.csc',compress_type=zipfile.ZIP_DEFLATED)
 out.writestr('amd_test_readme.txt','Isolated AMD Peashooter idle test: 60 samples/s + original blink. Original attacks remain unchanged. Starting sun 2000 for testing. H select; J equip; left-click place; K shovel; L none.\n')
(dest/'mod.arena').write_text('{\n mod "garden_amd_test"\n name "AMD Cloud Peashooter Test"\n description "Nacht: cloud-resampled idle, preserved attacks"\n}\n')
with zipfile.ZipFile(dest/'nacht_garden.iwd') as z:
 assert z.testzip() is None
 with zipfile.ZipFile(baseline_iwd) as old:
  assert all(z.read(n)==old.read(n) for n in old.namelist() if n.startswith('images/'))
  assert sum(n.startswith('images/') for n in z.namelist())==86
(root/'game-test-package-sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()},indent=2)+'\n')
print('Test package checked; 84 original images unchanged + compact AMD idle and corrected shared shooting.')
