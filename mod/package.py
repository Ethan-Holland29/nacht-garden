#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,shutil,zipfile
from catalog import MAPS
root=Path(__file__).resolve().parent
config=('bind H "set ng_action next"\n'
        'bind J "set ng_action plant"\n'
        'bind K "set ng_action shovel"\n'
        'bind L "set ng_action none"\n'
        'bind F5 "set ng_action page"\n'
        'bind F6 "set ng_action next"\n'
        'bind F7 "set ng_action plant"\n'
        'bind F8 "set ng_action shovel"\n'
        'bind F9 "set ng_action none"\nset ng_action ""\n')
manifest={}
for mapname,profile,label in MAPS:
    dest=root/'dist'/profile;dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'build'/profile/'mod.ff',dest/'mod.ff')
    with zipfile.ZipFile(dest/'nacht_garden.iwd','w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('nacht_garden.cfg',config)
        for file in sorted((root/'raw/weapons').glob('ng_seed_*')):
            fields=file.read_text().split('\\')
            weapon=dict(zip(fields[1::2],fields[2::2]))
            # Grenades cannot aim down sights. Omit unused ADS fields and empty
            # values to stay below the original game's 8192-byte text limit.
            compact='WEAPONFILE'+''.join('\\'+k+'\\'+v for k,v in weapon.items() if v and not k.lower().startswith('ads'))
            assert len(compact.encode()) < 8192
            archive.writestr('weapons/sp/'+file.name,compact)
        for name in ['_nacht_garden.gsc','_nacht_garden_assets.gsc']:
            archive.write(root/'raw/maps'/name,'maps/'+name)
        for file in sorted((root/'map-profiles'/profile).rglob('*.gsc')):
            archive.write(file,file.relative_to(root/'map-profiles'/profile))
        for file in sorted((root/'raw/clientscripts').rglob('*.csc')):
            archive.write(file,file.relative_to(root/'raw'))
        for file in sorted((root/'raw/sound').rglob('*.wav')):
            archive.write(file,file.relative_to(root/'raw'),compress_type=zipfile.ZIP_STORED)
        for file in sorted((root/'raw/images').glob('*.iwi')):
            archive.write(file,file.relative_to(root/'raw'))
    (dest/'mod.arena').write_text('{\n mod "'+profile+'"\n name "Garden: '+label+'"\n description "Original PvZ plants in '+label+' (solo)"\n}\n')
    manifest[profile]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()}
(root/'package-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Packaged all four stock map profiles.')
