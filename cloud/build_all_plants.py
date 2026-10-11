"""Prepare isolated garden_amd_full from a private accepted Peashooter demo.

Only original artwork is repacked. The accepted demo is read-only input.
"""
from pathlib import Path
import argparse,io,json,math,re,shutil,struct,sys,zipfile
from PIL import Image

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base',type=Path,required=True)
parser.add_argument('--accepted',type=Path,required=True)
parser.add_argument('--native',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--cloud',type=Path,required=True)
parser.add_argument('--source',type=Path,required=True)
args=parser.parse_args();base=args.base;accepted=args.accepted;native=args.native;test=args.output;raw=test/'raw'
sys.path.insert(0,str(base));from pvz_animation import Reanimations
source=zipfile.ZipFile(args.source);anim=Reanimations(source.read)
meta=json.loads((base/'animation-clips.json').read_text())
for d in ['images','materials','fx/ng','maps','clientscripts']:(raw/d).mkdir(parents=True,exist_ok=True)
(test/'zone_source').mkdir(parents=True,exist_ok=True)
for name in ['maps/_nacht_garden.gsc','maps/_nacht_garden_assets.gsc','clientscripts/_callbacks.csc']:
 shutil.copy2(accepted/'raw'/name,raw/name)
from apply_roster_gameplay import patch
gameplay=raw/'maps/_nacht_garden.gsc'
gameplay.write_text(patch(gameplay.read_text()))
# Reconstruct only the original family's bounds to preserve world position and
# units per source pixel through all animation states.
def original_bounds(family):
 frames=[]
 source_name={'sunflower':'SunFlower','repeater':'PeaShooter','wallnut':'Wallnut',
  'cherrybomb':'CherryBomb','potatomine':'PotatoMine','chomper':'Chomper','squash':'Squash','lilypad':'LilyPad','tanglekelp':'Tanglekelp'}[family]
 # All authored ranges, including former separately appended blink clips,
 # reconstruct the old family crop exactly for world-space alignment.
 for clip,m in meta.items():
  if clip.split('_')[0]!=family:continue
  if family=='wallnut':continue
  if clip=='squash_attack':continue
  if clip.endswith('_blink'):
   if family=='potatomine':first,track=32,'PotatoMine_blink'
   else:first,track=1,'anim_blink'
   frames+=anim.sequence(source_name,m['first_frame'],m['last_frame'],lambda i:{track:first+i})
  elif clip=='repeater_shoot':
   names=[n for n,_ in anim.load(source_name)];stem=names[:names.index('anim_stem')+1]
   frames+=anim.sequence(source_name,54,78,lambda i:{n:79+i for n in stem})
  else:frames+=anim.sequence(source_name,m['first_frame'],m['last_frame'])
 if family=='wallnut':
  for stage in range(3):
   replace={} if stage==0 else {'IMAGE_REANIM_WALLNUT_BODY':'IMAGE_REANIM_WALLNUT_CRACKED'+str(stage)}
   frames+=anim.sequence('Wallnut',0,16,replacements=replace)
   for first,count,track in [(17,5,'anim_blink_twitch'),(23,7,'anim_blink_twice'),(31,11,'anim_blink_thrice')]:
    frames+=anim.sequence('Wallnut',0,count-1,lambda i,f=first,t=track:{t:f+i},replace)
 boxes=[im.getbbox() for im in frames]
 return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
old_bounds={f:original_bounds(f) for f in ['sunflower','repeater','wallnut','cherrybomb','potatomine','chomper','squash','lilypad','tanglekelp']}
report={'profile':'garden_amd_full','game_runtime_verified':False,'clips':{},'accepted_demo_modified':False}
assets=(raw/'maps/_nacht_garden_assets.gsc').read_text()
zone=(accepted/'zone_source/garden_amd_test.zone').read_text();names=[];fxs=[]
with zipfile.ZipFile(args.cloud) as cloud:
 gpu=json.loads(cloud.read('report.json'));report['gpu']=gpu['gpu'];report['rocm']=gpu['rocm']
 for clip,v in gpu['clips'].items():
  family=clip.split('_')[0];m=meta[clip];b=old_bounds[family];cb=v['bounds']
  units=m['world_width']/m['cell_width'];assert abs(units-m['world_height']/m['cell_height'])<1e-7
  center_x=b[0]+m['cell_width']/2-(m['cell_width']-(b[2]-b[0]))//2
  old_center_y=b[3]-m['cell_height']/2
  cw=math.ceil(2*max(center_x-cb[0],cb[2]-center_x)/4)*4
  ch=math.ceil((cb[3]-cb[1])/4)*4
  left=int(center_x-cw/2);top=cb[3]-ch
  cols=min(16,1<<((2048//cw).bit_length()-1),1<<((v['frames']-1).bit_length()));rows=1<<((math.ceil(v['frames']/cols)-1).bit_length())
  assert cw*cols<=2048 and ch*rows<=2048,(clip,cw,ch,cols,rows)
  atlas=Image.new('RGBA',(cw*cols,ch*rows));cells=[]
  for i in range(v['frames']):
   im=Image.open(io.BytesIO(cloud.read(f'{clip}/{i:03}.png'))).convert('RGBA')
   cell=Image.new('RGBA',(cw,ch));x=cb[0]-left;y=cb[1]-top
   assert 0<=x and 0<=y and x+im.width<=cw and y+im.height<=ch
   cell.paste(im,(x,y));assert cell.crop((x,y,x+im.width,y+im.height)).tobytes()==im.tobytes()
   cells.append(cell)
  for i in range(cols*rows):atlas.paste(cells[min(i,len(cells)-1)],((i%cols)*cw,(i//cols)*ch))
  name='ng_fx_full_'+clip;fx='full_'+clip;names.append(name);fxs.append(fx)
  data=atlas.tobytes('raw','BGRA');assert len(data)<=8*2**20,(clip,len(data))
  header=b'IWi\x06'+struct.pack('<BBHHH4I',1,2,atlas.width,atlas.height,1,*([28+len(data)]*4))
  (raw/'images'/f'{name}.iwi').write_bytes(header+data)
  atlas.save(test/f'{name}.png')
  material=json.loads((base/'raw/materials'/f'ng_fx_{clip}.json').read_text())
  material['textures'][0]['image']=name;material['textureAtlas']={'columns':cols,'rows':rows}
  (raw/'materials'/f'{name}.json').write_text(json.dumps(material,indent=2)+'\n')
  stub=bytearray((native/'raw/materials/ng_test').read_bytes());stub[10:12]=bytes([rows,cols]);struct.pack_into('<I',stub,0,len(stub));stub.extend(name.encode()+b'\0');(native/'raw/materials'/name).write_bytes(stub)
  s=(base/'raw/fx/ng'/f'{clip}.efx').read_text().replace('"'+clip+'"','"'+fx+'"').replace('"ng_fx_'+clip+'"','"'+name+'"')
  values={'flags':'spawnRelative spawnOffsetNone runRelToEffect nonUniformScale',
          'atlasFps':v['fps'],'atlasColIndexBits':int(math.log2(cols)),'atlasRowIndexBits':int(math.log2(rows)),
          'atlasEntryCount':v['frames'],'lifeSpanMsec':f"{v['duration_msec']} 0",'spawnOrgZ':f'{(old_center_y-(cb[3]-ch/2))*units} 0'}
  if v['loop']:values['spawnLooping']=f"{v['duration_msec']} 0"
  for k,value in values.items():
   s,n=re.subn(r'(?m)^(\s*'+k+r')\s+[^;\n]*;',lambda m:m[1]+' '+str(value)+';',s);assert n==1,k
  for k,value in [('sizeGraph0',cw*units),('sizeGraph1',ch*units)]:
   s,n=re.subn(r'(?m)^(\s*'+k+r') [^\n]+',lambda m:m[1]+' '+str(value),s);assert n==1
  for p in [raw/'fx/ng'/f'{fx}.efx',native/'raw/fx/ng'/f'{fx}.efx']:p.write_text(s)
  assets=assets.replace('LoadFX( "ng/'+clip+'" )','LoadFX( "ng/'+fx+'" )')
  assets,n=re.subn(r'(level.ng_clip_msec\["'+clip+r'"\] = )\d+;',lambda m:m[1]+str(v['duration_msec'])+';',assets);assert n==1
  zone=zone.replace('material,ng_fx_'+clip+'\n','material,'+name+'\n').replace('fx,ng/'+clip+'\n','fx,ng/'+fx+'\n')
  oldbytes=(base/'raw/images'/f'ng_fx_{clip}.iwi').stat().st_size-28
  report['clips'][clip]={'frames':v['frames'],'fps':v['fps'],'duration_msec':v['duration_msec'],
      'atlas_columns':cols,'atlas_rows':rows,'atlas_dimensions':list(atlas.size),'cell_dimensions':[cw,ch],'texture_bytes':len(data),'old_texture_bytes':oldbytes,
      'pixels_preserved':True,'independent_width_height':True,'units_per_pixel':units,'old_source_bounds':b,'new_source_bounds':cb,
      'spawn_offset_z':(old_center_y-(cb[3]-ch/2))*units,'loop':v['loop']}
report['total_new_texture_mib']=sum(v['texture_bytes'] for v in report['clips'].values())/2**20
report['replaced_texture_mib']=sum(v['old_texture_bytes'] for v in report['clips'].values())/2**20
assert report['total_new_texture_mib']<=report['replaced_texture_mib']+8
# Match the pea sprite's source-pixel scale to Peashooter's source-pixel scale.
# The original 28px image is centered in a 32px texture, with a 24px visible pea.
pea_units=meta['peashooter_idle']['world_height']/meta['peashooter_idle']['cell_height']
pea_size=32*pea_units
pea=(base/'raw/fx/ng/pea.efx').read_text().replace('"pea"','"full_pea"')
for key in ['sizeGraph0','sizeGraph1']:
 pea,n=re.subn(r'(?m)^(\s*'+key+r') [^\n]+',lambda m:m[1]+' '+str(pea_size),pea);assert n==1
for dest in [raw/'fx/ng/full_pea.efx',native/'raw/fx/ng/full_pea.efx']:dest.write_text(pea)
fxs.append('full_pea')
assets=assets.replace('LoadFX( "ng/pea" )','LoadFX( "ng/full_pea" )')
zone=zone.replace('fx,ng/pea\n','fx,ng/full_pea\n')
report['pea_proportions']={'source_sprite_pixels':[28,28],'visible_source_diameter_pixels':24,
 'source_peashooter_height_pixels':69,'source_peashooter_world_height':38,
 'old_quad_width':7,'new_quad_width':pea_size,'new_visible_diameter':24*pea_units,
 'diameter_multiplier':pea_size/7,'method':'shared world units per original source pixel; no new projectile artwork'}
(raw/'maps/_nacht_garden_assets.gsc').write_text(assets)
# New held model/material keep accepted native assets untouched.
zone=zone.replace('xmodel,ng_held_potatomine\n','xmodel,ng_held_potatomine_surface\n').replace('material,mc/ng_held_potatomine\n','material,mc/ng_held_potatomine_surface\n')
zone=zone.replace('material,ng_packet_potatomine\n','material,ng_packet_potatomine_surface\n')
assets=(raw/'maps/_nacht_garden_assets.gsc').read_text().replace('\"ng_packet_potatomine\"','\"ng_packet_potatomine_surface\"')
(raw/'maps/_nacht_garden_assets.gsc').write_text(assets)
(test/'zone_source/garden_amd_full.zone').write_text(zone)
(native/'zone_source/english/assetlist/ng_full_materials.csv').write_text(''.join('material,'+n+'\n' for n in names)+'material,mc/ng_held_potatomine_surface\n')
(native/'zone_source/ng_full_plants.csv').write_text('ignore_full,ng_full_materials\n'+''.join('fx,ng/'+f+'\n' for f in fxs)+'xmodel,ng_held_potatomine_surface\n')
(test/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
