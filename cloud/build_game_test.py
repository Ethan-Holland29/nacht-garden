"""Build assets for an isolated Nacht AMD animation test; retain baseline files."""
from pathlib import Path
import json, math, re, struct, sys, zipfile
from PIL import Image,ImageSequence
from io import BytesIO
root=Path(__file__).resolve().parent;task=root.parent;base=task/'mod';test=root/'game-test';raw=test/'raw';native=task/'work/modtools'
accepted = root/'accepted-demo-2026-10-10'
baseline_maps = accepted/'baseline-maps' if accepted.exists() else base/'raw/maps'
for d in ['images','materials','maps','fx/ng']:(raw/d).mkdir(parents=True,exist_ok=True)
(test/'zone_source').mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(base));from pvz_animation import Reanimations
source=zipfile.ZipFile(root/'peashooter-source.zip');anim=Reanimations(source.read)
tracks=[n for n,_ in anim.load('PeaShooterSingle')];stem=tracks[:tracks.index('anim_stem')+1]
idle=anim.sequence('PeaShooterSingle',79,103)
shoot=anim.sequence('PeaShooterSingle',54,78,lambda i:{n:79+i for n in stem})
blink=anim.sequence('PeaShooterSingle',79,81,lambda i:{'anim_blink':1+i})
b=[im.getbbox() for im in idle+shoot+blink];bounds=(min(v[0] for v in b),min(v[1] for v in b),max(v[2] for v in b),max(v[3] for v in b))
with zipfile.ZipFile(root/'amd-attached-eyelids.zip') as cloud:
 repair_report=json.loads(cloud.read('report.json'));cloud_bounds=repair_report['bounds']
 frames=[Image.open(BytesIO(cloud.read(f'frames/{i:03}.png'))).convert('RGBA') for i in range(125)]
assert repair_report['source_keyframe_transforms_preserved'] and repair_report['frames']==125
assert repair_report['eyelid_face_attachment_verified'] and repair_report['max_attachment_error']<1e-7
cell_size=128;bottom_margin=4;origin_x=(128-(bounds[2]-bounds[0]))//2-bounds[0];origin_y=128-bottom_margin-bounds[3]
cells=[]
for im in frames:
 cell=Image.new('RGBA',(128,128));x=origin_x+cloud_bounds[0];y=origin_y+cloud_bounds[1]
 assert x>=0 and y>=0 and x+im.width<=128 and y+im.height<=128,'Would clip cloud pixels'
 cell.alpha_composite(im,(x,y));cells.append(cell)
# The blink and final-to-first transition are included in the cloud output.
assert len(cells)==125
# Remove only empty cell margins so all 125 frames fit a single texture.
# D3D9 supports non-power-of-two, non-mipmapped, clamped textures; this
# candidate still needs validation in WaW's original image loader.
compact=[]
for cell in cells:
 box=cell.getbbox();assert box[0]>=24 and box[1]>=48 and box[2]<=104 and box[3]<=128,box
 compact.append(cell.crop((24,48,104,128)))
meta=json.loads((base/'animation-clips.json').read_text())['peashooter_idle'];units=meta['world_width']/128
# Reconstruct the original head attachment: current stem transform multiplied
# by inverse bind-pose stem transform. This source's stem has translation only.
import copy
fixed=Reanimations(source.read);fixed.load('PeaShooterSingle')
fixed.tracks['PeaShooterSingle']=copy.deepcopy(anim.load('PeaShooterSingle'))
state_map=dict(fixed.tracks['PeaShooterSingle']);bind=state_map['anim_stem'][4]
for i in range(25):
 current=state_map['anim_stem'][4+i]
 assert all(current[k]==bind[k] for k in ('sx','sy','kx','ky'))
 for name,states in fixed.tracks['PeaShooterSingle']:
  if name in stem:continue
  states[54+i]['x']+=current['x']-bind['x']
  states[54+i]['y']+=current['y']-bind['y']
shoot_fixed=fixed.sequence('PeaShooterSingle',54,78,lambda i:{n:4+i for n in stem})
shoot_cells=[]
for im in shoot_fixed:
 b=im.getbbox();assert b[0]+origin_x>=0 and b[1]+origin_y>=0 and b[2]+origin_x<=128 and b[3]+origin_y<=128,b
 cell=Image.new('RGBA',(128,128));cell.paste(im,(origin_x,origin_y));shoot_cells.append(cell)
names=[];fxs=[];parts=[]
for fx,group,cols,rows,fps,size,zoffset,template_name in [
 ('peashooter_idle_60',compact,16,8,60,80*units,-28*units,'peashooter_idle'),
 ('peashooter_shoot_attached',shoot_cells,8,4,24,128*units,-4*units,'peashooter_shoot')]:
 side=group[0].width;atlas=Image.new('RGBA',(side*cols,side*rows))
 for i in range(cols*rows):atlas.paste(group[min(i,len(group)-1)],((i%cols)*side,(i//cols)*side))
 name='ng_fx_'+fx;names.append(name);fxs.append(fx)
 atlas.save(test/(name+'.png'));pixels=atlas.tobytes('raw','BGRA')
 payload=b'IWi\x06'+struct.pack('<BBHHH4I',1,2,atlas.width,atlas.height,1,*([28+len(pixels)]*4))+pixels
 (raw/'images'/f'{name}.iwi').write_bytes(payload)
 decoded=Image.frombytes('RGBA',atlas.size,payload[28:],'raw','BGRA')
 for i,cell in enumerate(group):
  x=(i%cols)*side;y=(i//cols)*side
  assert decoded.crop((x,y,x+side,y+side)).tobytes()==cell.tobytes(),'Frame pixels changed'
 material=json.loads((base/'raw/materials/ng_fx_peashooter_idle.json').read_text());material['textures'][0]['image']=name;material['textureAtlas']={'columns':cols,'rows':rows}
 (raw/'materials'/f'{name}.json').write_text(json.dumps(material,indent=2)+'\n')
 stub=bytearray((native/'raw/materials/ng_test').read_bytes());stub[10:12]=bytes([rows,cols]);struct.pack_into('<I',stub,0,len(stub));stub.extend(name.encode()+b'\0');(native/'raw/materials'/name).write_bytes(stub)
 s=(base/'raw/fx/ng'/f'{template_name}.efx').read_text().replace('"'+template_name+'"','"'+fx+'"').replace('"ng_fx_'+template_name+'"','"'+name+'"')
 for key,value in {'atlasFps':str(fps),'atlasColIndexBits':str(int(math.log2(cols))),'atlasRowIndexBits':str(int(math.log2(rows))),'atlasEntryCount':str(len(group)),'spawnOrgZ':f'{zoffset} 0'}.items():
  s,n=re.subn(r'(?m)^(\s*'+key+r')\s+[^;\n]*;',lambda m:m[1]+' '+value+';',s);assert n==1,key
 if fx=='peashooter_idle_60':
  for key in ['spawnLooping','lifeSpanMsec']:
   s,n=re.subn(r'(?m)^(\s*'+key+r')\s+[^;\n]*;',lambda m:m[1]+' 2083 0;',s);assert n==1
 for key in ['sizeGraph0','sizeGraph1']:
  s,n=re.subn(r'(?m)^(\s*'+key+r') [^\n]+',lambda m:m[1]+' '+str(size),s);assert n==1
 for path in [raw/'fx/ng'/f'{fx}.efx',native/'raw/fx/ng'/f'{fx}.efx']:path.write_text(s)
 parts.append({'image':name,'frames':len(group),'fps':fps,'atlas_size':list(atlas.size),'texture_mib':len(pixels)/2**20})
(native/'zone_source/english/assetlist/ng_amd_materials.csv').write_text(''.join('material,'+name+'\n' for name in names))
(native/'zone_source/ng_amd_test.csv').write_text('ignore_full,ng_amd_materials\n'+''.join('fx,ng/'+fx+'\n' for fx in fxs))
import csv
with (native/'raw/soundaliases/ng_pvz.csv').open() as f:
 sound_rows=list(csv.reader(f))
header=sound_rows[0];sound_renames={}
for row in sound_rows[1:]:
 old=row[header.index('name')];new=old.replace('ng_','ng_loaded_',1)
 sound_renames[old]=new;row[header.index('name')]=new;row[header.index('type')]='loaded'
with (native/'raw/soundaliases/ng_amd_loaded.csv').open('w') as f:csv.writer(f).writerows(sound_rows)
with (native/'zone_source/ng_amd_test.csv').open('a') as f:f.write('sound,ng_amd_loaded,,all_sp\n')
script=(baseline_maps/'_nacht_garden_assets.gsc').read_text().replace('LoadFX( "ng/peashooter_idle" )','LoadFX( "ng/peashooter_idle_60" )').replace('LoadFX( "ng/peashooter_shoot" )','LoadFX( "ng/peashooter_shoot_attached" )')
script=script.replace('    level.ng_clip_msec = [];','    level.ng_clip_msec = [];\n    level.ng_clips["peashooter_original_idle"] = LoadFX( "ng/peashooter_idle" );')
script=script.replace('level.ng_clip_msec["peashooter_idle"] = 2333;', 'level.ng_clip_msec["peashooter_idle"] = 2083;')
(raw/'maps/_nacht_garden_assets.gsc').write_text(script)
gamecode=(baseline_maps/'_nacht_garden.gsc').read_text().replace('level.ng_sun = 200;','level.ng_sun = 2000; // Isolated visual test budget.')
gamecode=gamecode.replace('show_clip( name )\n{','show_clip( name )\n{\n    if ( name == "peashooter_idle" && IsDefined( self.ng_original ) && self.ng_original ) name = "peashooter_original_idle";')
gamecode=gamecode.replace('tick_plant( now )\n{','tick_plant( now )\n{\n    if ( IsDefined( self.ng_comparison_hold ) && self.ng_comparison_hold ) return;')
gamecode=gamecode.replace('            if ( action == "next" )','            if ( action == "compare" ) self comparison_pair();\n            if ( action == "compare_fire" ) self comparison_toggle();\n            if ( action == "next" )')
gamecode=gamecode.replace('H: choose   J: hold plant   K: shovel   L: none','H: choose  J: hold  K: shovel  L: none | B: compare  N: shooting')
gamecode+='\n'+(root/'comparison.gsc').read_text()
for old,new in sound_renames.items():gamecode=gamecode.replace('"'+old+'"','"'+new+'"')
(raw/'maps/_nacht_garden.gsc').write_text(gamecode)
baseline_zone = accepted/'zone_source/garden_amd_test.zone' if accepted.exists() else base/'zone_source/nacht_garden.zone'
zone=baseline_zone.read_text()+'\n'+''.join('material,'+name+'\n' for name in names)+''.join('fx,ng/'+fx+'\n' for fx in fxs)
for old,new in sound_renames.items():zone=zone.replace('sound,'+old+'\n','sound,'+new+'\n')
# The retail callback accepts one argument while the runtime supplies more.
# Preserve event names and payloads, including the local-client-prefixed form.
callback=(task/'work/common-callbacks.csc').read_text()
old='level_notify(notify_name)\n{\n\tlevel notify(notify_name);\n}'
assert old in callback
callback=callback.replace(old,'''level_notify(arg0, arg1, arg2, arg3)
{
    if ( IsString( arg0 ) ) { level notify(arg0, arg1, arg2, arg3); return; }
    if ( IsDefined( arg1 ) && IsString( arg1 ) ) { level notify(arg1, arg2, arg3); return; }
    PrintLn( "Garden: unrecognized level_notify arguments" );
}''')
(raw/'clientscripts').mkdir(exist_ok=True)
(raw/'clientscripts/_callbacks.csc').write_text(callback)
zone+='rawfile,clientscripts/_callbacks.csc\n'
(test/'zone_source/garden_amd_test.zone').write_text('\n'.join(dict.fromkeys(zone.splitlines()))+'\n')
(root/'game-test-build.json').write_text(json.dumps({'profile':'garden_amd_test','cloud_frames':125,'original_blink_states':3,'fps':60,'duration_msec':2083,'body_cycle_continuous':True,'world_size':meta['world_width'],'texture_parts':parts,'frame_pixels_verified':True,'extra_uncompressed_texture_mib':sum(p['texture_mib'] for p in parts),'baseline_modified':False,'shooting_attachment_source':'anim_idle frames 4..28, bind pose 4','loaded_sound_count':len(sound_renames),'cloud_loop_report':repair_report,'comparison_keys':{'B':'Place original left and AMD right','N':'Toggle both shooting'},'game_runtime_verified':False},indent=2)+'\n')
print('Prepared side-by-side comparison, compact single-sheet idle, shared corrected shooting.')
