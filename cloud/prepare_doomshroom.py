"""Add original Doom-shroom animations, packet, Betty-held model and loaded audio."""
from pathlib import Path
import argparse,csv,hashlib,io,json,math,re,shutil,struct,subprocess,sys,zipfile
from PIL import Image
from apply_doom_gameplay import patch
p=argparse.ArgumentParser(description=__doc__)
for n in ['base','native','output','cloud','source','ui-source']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();raw=a.output/'raw';native=a.native
z=zipfile.ZipFile(a.cloud);report=json.loads(z.read('report.json'));units=42/76;materials=[];effects=[];packed={}

def image_asset(name,im,cols=1,rows=1,kind='fx'):
 data=im.tobytes('raw','BGRA');assert len(data)<=8*2**20 and max(im.size)<=2048
 (raw/'images'/(name+'.iwi')).write_bytes(b'IWi\x06'+struct.pack('<BBHHH4I',1,2,im.width,im.height,1,*([28+len(data)]*4))+data)
 template='ng_fx_cherrybomb_idle' if kind=='fx' else 'ng_packet_cherrybomb'
 material=json.loads((a.base/'raw/materials'/(template+'.json')).read_text());material['textures'][0]['image']=name
 if kind=='fx':material['textureAtlas']={'columns':cols,'rows':rows}
 (raw/'materials'/(name+'.json')).write_text(json.dumps(material,indent=2)+'\n');materials.append(name)
 stub=bytearray((native/'raw/materials/ng_test').read_bytes());stub[10:12]=bytes([rows,cols]);struct.pack_into('<I',stub,0,len(stub));stub.extend(name.encode()+b'\0');(native/'raw/materials'/name).write_bytes(stub)
 return len(data)

def effect_block(name,material,v,cw,ch,cols,rows,count,offset_z,delay=0,loop=False):
 template='cherrybomb_idle' if loop else 'cherrybomb_explode';s=(a.base/'raw/fx/ng'/(template+'.efx')).read_text()
 s=s.replace('"'+template+'"','"'+name+'"').replace('"ng_fx_'+template+'"','"'+material+'"')
 duration=round(count*1000/v['fps'])
 values={'flags':'spawnRelative spawnOffsetNone runRelToEffect nonUniformScale','atlasFps':v['fps'],'atlasColIndexBits':int(math.log2(cols)),'atlasRowIndexBits':int(math.log2(rows)),'atlasEntryCount':count,'lifeSpanMsec':f'{duration} 0','spawnOrgZ':f'{offset_z} 0','spawnDelayMsec':f'{delay} 0'}
 if loop:values['spawnLooping']=f'{duration} 0'
 for k,value in values.items():
  s,n=re.subn(r'(?m)^(\s*'+k+r')\s+[^;\n]*;',lambda m:m[1]+' '+str(value)+';',s);assert n==1,k
 for key,size in [('sizeGraph0',cw*units),('sizeGraph1',ch*units)]:
  s,n=re.subn(r'(?m)^(\s*'+key+r') [^\n]+',lambda m:m[1]+' '+str(size),s);assert n==1
 return s.removeprefix('iwfx 2').strip()

for clip,v in report['clips'].items():
 b=v['bounds'];center=256 if clip.endswith('_burst') else 232.5;ground=384 if clip.endswith('_burst') else 272
 cw=math.ceil(2*max(center-b[0],b[2]-center)/4)*4;ch=math.ceil((b[3]-b[1])/4)*4;left=math.floor(center-cw/2);top=b[3]-ch
 frames=[]
 for i in range(v['frames']):
  im=Image.open(io.BytesIO(z.read(f'{clip}/{i:03}.png'))).convert('RGBA');cell=Image.new('RGBA',(cw,ch));xy=(b[0]-left,b[1]-top);cell.paste(im,xy);assert cell.crop((*xy,xy[0]+im.width,xy[1]+im.height)).tobytes()==im.tobytes();frames.append(cell)
 page_size=8 if clip.endswith('_burst') else len(frames);blocks=[];pages=[]
 for start in range(0,len(frames),page_size):
  seq=frames[start:start+page_size];cols=min(4 if clip.endswith('_burst') else 8,1<<((len(seq)-1).bit_length()));rows=1<<((math.ceil(len(seq)/cols)-1).bit_length());atlas=Image.new('RGBA',(cw*cols,ch*rows))
  for i in range(cols*rows):atlas.paste(seq[min(i,len(seq)-1)],((i%cols)*cw,(i//cols)*ch))
  name='ng_fx_full_'+clip+('_p'+str(start//page_size) if clip.endswith('_burst') else '')
  size=image_asset(name,atlas,cols,rows)
  for i,cell in enumerate(seq):assert atlas.crop(((i%cols)*cw,(i//cols)*ch,(i%cols+1)*cw,(i//cols+1)*ch)).tobytes()==cell.tobytes()
  delay=round(start*1000/v['fps']);blocks.append(effect_block(clip+'_'+str(start),name,v,cw,ch,cols,rows,len(seq),(ground-(top+ch/2))*units,delay,v['loop']))
  pages.append(dict(image=name,frames=len(seq),start=start,columns=cols,rows=rows,dimensions=list(atlas.size),cell=[cw,ch],texture_bytes=size,delay_msec=delay))
 fx='full_'+clip;s='iwfx 2\n\n'+'\n\n'.join(blocks)+'\n'
 for dest in [raw/'fx/ng'/(fx+'.efx'),native/'raw/fx/ng'/(fx+'.efx')]:dest.write_text(s)
 effects.append(fx);packed[clip]=dict(pages=pages,frames=v['frames'],duration_msec=v['duration_msec'],fps=v['fps'],packed_pixels_equal_cloud=True)

# Seed packet and held artwork use the original awake idle pose.
sys.path.insert(0,str(a.base));from pvz_animation import Reanimations
source=zipfile.ZipFile(a.source);anim=Reanimations(source.read);f=anim.frame('DoomShroom',0);portrait=f.crop(f.getbbox())
ui=zipfile.ZipFile(a.ui_source);ui_anim=Reanimations(ui.read);card=ui_anim.image('images/seeds.png').crop((0,0,50,70));small=portrait.copy();small.thumbnail((40,45),Image.Resampling.LANCZOS);card.alpha_composite(small,((50-small.width)//2,5+(45-small.height)//2))
font=ui.read('data/Pico129.txt').decode('latin1');rects=[tuple(map(int,m)) for m in re.findall(r'\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)',re.search(r'Define RectList\s*\((.*?)\);',font,re.S)[1])];fontim=ui_anim.image('data/_Pico129.png');glyphs=[]
for d in '500':
 x,y,w,h=rects[52+int(d)];g=Image.new('RGBA',(w,h));g.putalpha(fontim.crop((x,y,x+w,y+h)).convert('L'));glyphs.append(g)
digits=Image.new('RGBA',(sum(g.width+1 for g in glyphs)-1,12));x=0
for g in glyphs:digits.alpha_composite(g,(x,0));x+=g.width+1
card.alpha_composite(digits,((50-digits.width)//2,54));image_asset('ng_packet_doomshroom',card.resize((64,128),Image.Resampling.LANCZOS),kind='hud');card.save(a.output/'doom-packet-preview.png')
name='ng_held_doomshroom';image_asset(name,portrait.resize((128,128),Image.Resampling.LANCZOS));materials.remove(name);materials.append('mc/'+name)
mat=json.loads((a.base/'raw/materials/mc/ng_held_potatomine.json').read_text())
for tex in mat['textures']:
 if tex['image']=='ng_held_potatomine':tex['image']=name
(raw/'materials/mc'/(name+'.json')).write_text(json.dumps(mat,indent=2)+'\n')
original=(native/'model_export/ng_held_potatomine.xmodel_export').read_text();model=original.replace('ng_held_potatomine',name);w=min(14,12*portrait.width/portrait.height);h=w*portrait.height/portrait.width
for i,(x,y,zz) in enumerate([(-w/2,0,0),(w/2,0,0),(w/2,0,h),(-w/2,0,h)]):
 model,n=re.subn(r'(VERT '+str(i)+r'\nOFFSET )[^\n]+',lambda m:m[1]+f'{x}, {y}, {zz}',model);assert n==1
assert model.split('NUMVERTS')[0]==original.split('NUMVERTS')[0];(native/'model_export'/(name+'.xmodel_export')).write_text(model);shutil.copy2(native/'raw/material_properties/ng_held_potatomine',native/'raw/material_properties'/name)
(native/'source_data/ng_doomshroom.gdt').write_text('{\n"'+name+'" ( "xmodel.gdf" )\n{\n"type" "animated"\n"filename" "'+name+'.xmodel_export"\n"highLodDist" "1000000"\n"collisionLOD" "None"\n}\n}\n')
weapon=(a.base/'raw/weapons/ng_seed_cherrybomb').read_text().replace('ng_seed_cherrybomb','ng_seed_doomshroom').replace('ng_held_cherrybomb',name).replace('Cherry Bomb','Doom-shroom');(raw/'weapons/ng_seed_doomshroom').write_text(weapon)
# Loaded PCM audio avoids the old streamed-WAV PRIV errors.
ogg=a.output/'doomshroom.ogg';ogg.write_bytes(source.read('sounds/doomshroom.ogg'));wav=native/'raw/sound/ng/doomshroom.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(ogg),'-ar','44100','-ac','1','-c:a','pcm_s16le',str(wav)],check=True)
rows=list(csv.reader((native/'raw/soundaliases/ng_amd_loaded.csv').open()));header=rows[0];row=['']*len(header)
for key,value in dict(name='ng_loaded_doomshroom',file='ng\\doomshroom.wav',limit_count='2',limit_type='priority',vol_min='.7',vol_max='.7',pitch_min='1',pitch_max='1',dist_min='80',dist_max='1600',volumefalloffcurve='curve2',bus='full_vol',spatialized='3d',type='loaded',loadspec='all_sp').items():row[header.index(key)]=value
with (native/'raw/soundaliases/ng_doom_loaded.csv').open('w') as out:writer=csv.writer(out);writer.writerow(header);writer.writerow(row)
for path,lines in [(a.output/'zone_source/garden_amd_full.zone',['material,'+n for n in materials]+['fx,ng/'+f for f in effects]+['weapon,ng_seed_doomshroom','sound,ng_loaded_doomshroom']), (native/'zone_source/ng_full_plants.csv',['fx,ng/'+f for f in effects]+['xmodel,ng_held_doomshroom','sound,ng_doom_loaded,,all_sp']), (native/'zone_source/english/assetlist/ng_full_materials.csv',['material,'+n for n in materials])]:
 existing=[line for line in path.read_text().splitlines() if 'doomshroom' not in line and 'ng_doom_loaded' not in line];path.write_text('\n'.join(existing+lines)+'\n')
assets=raw/'maps/_nacht_garden_assets.gsc';s=assets.read_text();s=re.sub(r'(?s)    // NG_DOOM_ASSETS_BEGIN.*?    // NG_DOOM_ASSETS_END\n','',s);end=s.rfind('}')
extra='    // NG_DOOM_ASSETS_BEGIN\n'
for clip,v in report['clips'].items():extra+=f'    level.ng_clips["{clip}"] = LoadFX( "ng/full_{clip}" );\n    level.ng_clip_msec["{clip}"] = {v["duration_msec"]};\n'
extra+='''    level.ng_clips["doomshroom_preview"] = level.ng_clips["doomshroom_idle"];
    level.ng_base[10] = "doomshroom";
    level.ng_names[10] = "Doom-shroom";
    level.ng_cost[10] = 500;
    level.ng_cooldown[10] = 50000;
    level.ng_anchor[10] = 0;
    level.ng_packet[10] = "ng_packet_doomshroom";
    level.ng_weapons[10] = "ng_seed_doomshroom";
    PrecacheShader( "ng_packet_doomshroom" );
    PrecacheItem( "ng_seed_doomshroom" );
    // NG_DOOM_ASSETS_END
'''
assets.write_text(s[:end]+extra+s[end:]);game=raw/'maps/_nacht_garden.gsc';game.write_text(patch(game.read_text()))
result=dict(profile='garden_amd_full',price=500,cooldown_msec=50000,clips=packed,total_texture_mib=sum(page['texture_bytes'] for v in packed.values() for page in v['pages'])/2**20,source_audio_sha256=hashlib.sha256(source.read('sounds/doomshroom.ogg')).hexdigest(),nuke='maps/_zombiemode_powerups::nuke_powerup; native Nacht behavior',sleep_note='Original sleep loop included but unused in night-map gameplay',game_runtime_verified=False)
(a.output/'doom-build-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
