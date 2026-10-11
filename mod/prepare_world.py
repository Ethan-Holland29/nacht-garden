#!/usr/bin/env python3
"""Convert original PvZ animation frames to WaW world-effect atlases."""
import json, math, re, struct, os
from pathlib import Path
from PIL import Image
import prepare as base
from pvz_animation import Reanimations
from catalog import PLANTS

root, raw = base.ROOT, base.RAW
native = base.TASK/'work/modtools'
effects = native/'raw/fx/ng'
effects.mkdir(parents=True, exist_ok=True)
template = (base.TASK/'work/stock-sprite.efx').read_text()
start = template.index('{\n\tname "glow";')
template = template[start:template.index('\n{\n\tname "mist";', start)]
fx_material = json.loads((base.TASK/'work/waw-materials/materials/gfx_fxt_misc_missing_fx.json').read_text())
materials, fx_names, clips = [], [], {}
animations = Reanimations(base.asset)

def image_asset(name, image, columns=1, rows=1):
    # Uncompressed BGRA preserves the original converted sprite pixels.
    pixels = image.tobytes('raw', 'BGRA')
    header = b'IWi\x06' + struct.pack('<BBHHH4I', 1, 2, image.width, image.height, 1, *([28+len(pixels)]*4))
    (raw/'images'/f'{name}.iwi').write_bytes(header+pixels)
    material = json.loads(json.dumps(fx_material))
    material['textures'][0]['image'] = name
    material['textureAtlas'] = {'columns': columns, 'rows': rows}
    (raw/'materials'/f'{name}.json').write_text(json.dumps(material, indent=2)+'\n')
    materials.append(name)
    # Native FX compilation needs atlas dimensions but does not ship this
    # temporary material: it is external to ng_world.ff. Final material above
    # binds the installed game's real effect technique and original PvZ art.
    stub = bytearray((native/'raw/materials/ng_test').read_bytes())
    assert stub[8:12] == bytes([0,48,1,1])
    stub[10:12] = bytes([rows,columns])
    # The raw material stores its name as a file-relative string pointer.
    struct.pack_into('<I', stub, 0, len(stub))
    stub.extend(name.encode()+b'\0')
    (native/'raw/materials'/name).write_bytes(stub)

def effect(name, material, count=1, fps=0, size=39.1, preview=False, projectile=False,
           looping=True, columns=1, rows=1, lifetime=None, oriented=True, fade=False, height=None):
    # Descriptor parameters connect the original images to WaW's existing
    # billboard renderer; no artwork, mesh, shader, or animation is authored.
    duration = lifetime or (round(count*1000/fps) if fps else 1000)
    if projectile: looping = False
    values = {
        'name': '"'+name+'"',
        'editorFlags': 'looping useBackCompatVel' if looping else 'useBackCompatVel',
        'flags': 'spawnRelative spawnOffsetNone runRelToEffect',
        'spawnRange': '0 0', 'fadeInRange': '0 0', 'fadeOutRange': '0 0',
        'spawnLooping': f'{duration} 0', 'spawnOneShot': '1 0',
        'lifeSpanMsec': f'{duration} 0',
        'spawnOrgX': '0 0', 'spawnOrgY': '0 0', 'spawnOrgZ': '0 0',
        'atlasBehavior': 'startFixed', 'atlasIndex': '0',
        'atlasFps': str(fps), 'atlasLoopCount': '0',
        'atlasColIndexBits': str(int(math.log2(columns))),
        'atlasRowIndexBits': str(int(math.log2(rows))),
        'atlasEntryCount': str(count), 'sortOrder':'0',
    }
    s = template
    for key,value in values.items():
        s,n = re.subn(r'(?m)^(\s*'+key+r')\s+[^;\n]*;',lambda m:m[1]+' '+value+';',s)
        assert n==1,(key,n)
    # Constant curves: white tint, no velocity/rotation, fixed size and opacity.
    for key,scale,components in [('sizeGraph0',size,'1'),('sizeGraph1',height or size,'1'),
          ('scaleGraph',1,'1'),('colorGraph',1,'1 1 1'),
          ('alphaGraph',1,'0.3' if preview else '1'),('rotGraph',0,'0')]:
        curve = f'\t{key} {scale}\n\t{{\n' + ''.join(f'\t\t{{\n\t\t\t0 {components}\n\t\t\t1 {components}\n\t\t}}\n' for _ in range(2)) + '\t};'
        s,n = re.subn(r'(?ms)^\s*'+key+r'\s+[^\n]+\n\s*\{.*?\};',lambda m: '\n'+curve,s)
        assert n==1
    if fade:
        s=re.sub(r'(?ms)\s*alphaGraph 1\s*\{.*?\};', '\n\talphaGraph 1\n\t{\n\t\t{\n\t\t\t0 1\n\t\t\t0.7 1\n\t\t\t1 0\n\t\t}\n\t\t{\n\t\t\t0 1\n\t\t\t0.7 1\n\t\t\t1 0\n\t\t}\n\t};',s)
    s=s.replace('"gfx_fxt_light_flare4"','"'+material+'"')
    if oriented: s=s.replace('billboardSprite','orientedSprite')
    descriptor = 'iwfx 2\n\n'+s+'\n'
    (effects/f'{name}.efx').write_text(descriptor)
    (raw/'fx/ng').mkdir(parents=True, exist_ok=True)
    (raw/'fx/ng'/f'{name}.efx').write_text(descriptor)
    fx_names.append('ng/'+name)

families = {}
def clip(family, action, source, first, last, fps=12, looping=True, overrides=None, replacements=None):
    name=family+'_'+action
    frames=animations.sequence(source,first,last,overrides,replacements)
    families.setdefault(family,{})[name]=(frames,fps,looping)
    clips[name]={'source':source+'.reanim','first_frame':first,'last_frame':last,'fps':fps,'count':len(frames),'looping':looping}

# PvZ runs stem, head and eyelid tracks independently. Retain the original
# stem motion while selecting the authored shooting/blinking head sequence.
pea_tracks=[n for n,_ in animations.load('PeaShooterSingle')]
stem_end=pea_tracks.index('anim_stem')
stem_tracks=pea_tracks[:stem_end+1]
clip('peashooter','idle','PeaShooterSingle',79,103)
clip('peashooter','shoot','PeaShooterSingle',54,78,24,False,
     overrides=lambda i:{n:79+i for n in stem_tracks})
clip('peashooter','blink','PeaShooterSingle',79,81,12,False,
     overrides=lambda i:{'anim_blink':1+i})
clip('sunflower','idle','SunFlower',4,28)
clip('sunflower','blink','SunFlower',4,6,12,False,
     overrides=lambda i:{'anim_blink':1+i})
for stage in range(3):
    suffix='' if stage==0 else '_crack'+str(stage)
    replace={} if stage==0 else {'IMAGE_REANIM_WALLNUT_BODY':'IMAGE_REANIM_WALLNUT_CRACKED'+str(stage)}
    clip('wallnut',suffix[1:]+'_idle' if stage else 'idle','Wallnut',0,16,replacements=replace)
    for action,first,last,track in [('twitch',17,21,'anim_blink_twitch'),('blink',23,29,'anim_blink_twice'),('blink3',31,41,'anim_blink_thrice')]:
        clip('wallnut',(suffix[1:]+'_' if stage else '')+action,'Wallnut',0,last-first,12,False,
             overrides=lambda i,f=first,t=track:{t:f+i},replacements=replace)
clip('cherrybomb','idle','CherryBomb',14,26,30)
clip('cherrybomb','explode','CherryBomb',0,13,30,False)
clip('potatomine','idle','PotatoMine',0,0)
clip('potatomine','rise','PotatoMine',1,19,12,False)
clip('potatomine','armed','PotatoMine',20,30)
clip('potatomine','blink','PotatoMine',20,22,12,False,
     overrides=lambda i:{'PotatoMine_blink':32+i})
clip('potatomine','mashed','PotatoMine',36,36)
for action,first,last,rate,loop in [('idle',0,24,12,True),('bite',25,49,24,False),('chew',50,65,12,True),('swallow',66,93,24,False)]:
    clip('chomper',action,'Chomper',first,last,rate,loop)

# Repeater uses the original two-pea head in PeaShooter.reanim.
repeat_tracks=[n for n,_ in animations.load('PeaShooter')]
repeat_stem=repeat_tracks[:repeat_tracks.index('anim_stem')+1]
clip('repeater','idle','PeaShooter',79,103)
clip('repeater','shoot','PeaShooter',54,78,24,False,
     overrides=lambda i:{n:79+i for n in repeat_stem})
clip('repeater','blink','PeaShooter',79,81,12,False,
     overrides=lambda i:{'anim_blink':1+i})
clip('squash','idle','Squash',5,23)
clip('squash','look','Squash',37,42,12,False)
clip('squash','jump','Squash',50,64,24,False)
clip('squash','land','Squash',65,72,24,False)
clip('lilypad','idle','LilyPad',0,0)
clip('lilypad','blink','LilyPad',0,2,12,False,
     overrides=lambda i:{'anim_blink':1+i})
clip('tanglekelp','idle','Tanglekelp',5,26)
clip('tanglekelp','grab','Tanglekelp',27,31,12,False)

# Consolidate authored idle/blink/twitch clips into shared looping atlases.
# Previews reuse those effects. This preserves original animation frames while
# reducing the fixed engine FX pool footprint across the DLC maps.
aliases={}
for family,sequences in families.items():
    for name in list(sequences):
        if not name.endswith('_idle') and not (family=='potatomine' and name=='potatomine_armed'): continue
        frames,fps,loop=sequences[name]
        prefix=name.rsplit('_',1)[0]
        if family=='potatomine' and name=='potatomine_idle':continue
        keys=[prefix+'_'+a for a in ['twitch','blink','blink3'] if prefix+'_'+a in sequences]
        if not keys:continue
        combined=[]
        if prefix+'_twitch' in sequences:combined+=sequences[prefix+'_twitch'][0]
        combined+=frames
        for key in keys:
            if not key.endswith('_twitch'):combined+=sequences[key][0]
            aliases[key]=name
            del sequences[key]
        sequences[name]=(combined,fps,True)
        clips[name]['count']=len(combined)
        clips[name]['composed_original_clips']=keys
# Potato blink belongs to its armed appearance, not the underground idle.
# Squash looking and jumping are consecutive parts of one committed attack.
sq=families['squash']; look=sq.pop('squash_look'); jump=sq.pop('squash_jump')
sq['squash_attack']=(sum(([f,f] for f in look[0]),[])+jump[0],24,False)
clips['squash_attack']={'source':'Squash.reanim','first_frame':37,'last_frame':64,'fps':24,'count':len(sq['squash_attack'][0]),'looping':False}
aliases['squash_look']='squash_attack';aliases['squash_jump']='squash_attack'

anchors={}; portraits={}
for family,sequences in families.items():
    boxes=[f.getbbox() for frames,_,_ in sequences.values() for f in frames]
    bounds=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
    idle=sequences[family+'_idle'][0]
    # A single ground coordinate per plant keeps all states aligned. In FX,
    # size is full sprite width, so the centre belongs half a width above its base.
    ground=max(f.getbbox()[3] for f in idle)
    if family=='potatomine': ground=max(f.getbbox()[3] for f in sequences['potatomine_armed'][0])
    cell_width=1 << (bounds[2]-bounds[0]-1).bit_length()
    cell_height=1 << (bounds[3]-bounds[1]-1).bit_length()
    reference=idle
    if family=='potatomine': reference=sequences['potatomine_armed'][0]
    visible_height=max(f.getbbox()[3]-f.getbbox()[1] for f in reference)
    target_height=next(p[4] for p in PLANTS if p[0]==family)
    units=target_height/visible_height
    size=cell_width*units
    height=cell_height*units
    anchors[family]=(cell_height/2-(bounds[3]-ground))*units
    for name,(frames,fps,looping) in sequences.items():
        cells=[]
        for frame in frames:
            picture=frame.crop(bounds); cell=Image.new('RGBA',(cell_width,cell_height))
            cell.alpha_composite(picture,((cell_width-picture.width)//2,cell_height-picture.height)); cells.append(cell)
        columns=min(8,1 << (len(cells)-1).bit_length()); rows=1 << ((math.ceil(len(cells)/columns)-1).bit_length())
        atlas=Image.new('RGBA',(cell_width*columns,cell_height*rows))
        for i in range(columns*rows):
            atlas.alpha_composite(cells[min(i,len(cells)-1)],((i%columns)*cell_width,(i//columns)*cell_height))
        material='ng_fx_'+name
        image_asset(material,atlas,columns,rows)
        effect(name,material,len(frames),fps,size,looping=looping,columns=columns,rows=rows,height=height)
        clips[name].update({'cell_width':cell_width,'cell_height':cell_height,'columns':columns,'rows':rows,'world_width':size,'world_height':height,'ground_anchor':anchors[family]})
        atlas.save(root/(name+'-animation-atlas.png'))
        if name==family+'_idle':
            portraits[family]=cells[0]
            image_asset('ng_fx_'+family+'_preview',cells[0])
            aliases[family+'_preview']=family+'_idle'

from io import BytesIO
pea=Image.open(BytesIO(base.asset('images/ProjectilePea.png'))).convert('RGBA')
side=1 << (max(pea.size)-1).bit_length(); cell=Image.new('RGBA',(side,side))
cell.alpha_composite(pea,((side-pea.width)//2,(side-pea.height)//2))
image_asset('ng_fx_pea',cell)
effect('pea','ng_fx_pea',size=7,projectile=True,lifetime=50,oriented=False)

# Original PvZ explosion lettering and particles, never an invented BOOM label.
for name,path,size,duration in [('powie','particles/ExplosionPowie.png',95,500),('spudow','particles/ExplosionSpudow.png',95,700),('cloud','particles/ExplosionCloud.png',65,550)]:
    picture=animations.image(path);side=1 << (max(picture.size)-1).bit_length()
    cell=Image.new('RGBA',(side,side));cell.alpha_composite(picture,((side-picture.width)//2,(side-picture.height)//2))
    image_asset('ng_fx_'+name,cell)
    effect(name,'ng_fx_'+name,size=size,looping=False,lifetime=duration,oriented=False,fade=True)
cloud=(effects/'cloud.efx').read_text().split('iwfx 2',1)[1]
for blast in ['powie','spudow']:
    path=effects/(blast+'.efx')
    descriptor=path.read_text()+cloud
    path.write_text(descriptor)
    (raw/'fx/ng'/(blast+'.efx')).write_text(descriptor)
fx_names.remove('ng/cloud')
aliases['cloud']='powie'
base.asset('particles/Powie.xml');base.asset('particles/PotatoMine.xml')

# Original rotating Sun animation is shown when a sunflower produces income.
sun_count=max(len(states) for _,states in animations.load('Sun'))
sun_frames=animations.sequence('Sun',0,sun_count-1)
boxes=[f.getbbox() for f in sun_frames];bounds=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
side=1 << (max(bounds[2]-bounds[0],bounds[3]-bounds[1])-1).bit_length();rows=1 << ((math.ceil(sun_count/8)-1).bit_length())
atlas=Image.new('RGBA',(side*8,side*rows))
for i in range(8*rows):
    pic=sun_frames[min(i,sun_count-1)].crop(bounds);atlas.alpha_composite(pic,((i%8)*side+(side-pic.width)//2,(i//8)*side+(side-pic.height)//2))
image_asset('ng_fx_sun',atlas,8,rows)
effect('sun','ng_fx_sun',sun_count,30,30,looping=False,columns=8,rows=rows,oriented=False)

# The seed bank and packets are composites of original UI artwork and plants.
def hud_asset(name,picture):
    w=1 << (picture.width-1).bit_length();h=1 << (picture.height-1).bit_length()
    # Resampling to powers of two avoids transparent padding in HUD quads;
    # the HUD displays the material at the source image's aspect ratio.
    picture=picture.resize((w,h),Image.Resampling.LANCZOS)
    image_asset(name,picture)
    material=json.loads((base.TASK/'work/waw-materials/materials/rank_pvt1.json').read_text())
    material['textures'][0]['image']=name
    (raw/'materials'/f'{name}.json').write_text(json.dumps(material,indent=2)+'\n')

plant_names=[p[0] for p in PLANTS]
hud_asset('ng_seedbank',animations.image('images/SeedBank.png'))
packet=animations.image('images/seeds.png').crop((0,0,50,70))
# Original bitmap font glyphs, composed in the packet's printed cost field.
font_text=base.asset('data/Pico129.txt').decode('latin1')
rect_text=re.search(r'Define RectList\s*\((.*?)\);',font_text,re.S)[1]
rects=[tuple(map(int,m)) for m in re.findall(r'\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)',rect_text)]
font_image=animations.image('data/_Pico129.png')
def price_image(value):
    glyphs=[]
    for digit in str(value):
        x,y,w,h=rects[52+int(digit)]
        glyph=font_image.crop((x,y,x+w,y+h))
        # PvZ tints this white bitmap font black when printing packet prices.
        glyph.paste((0,0,0), (0,0,w,h));glyph.putalpha(font_image.crop((x,y,x+w,y+h)).convert('L'))
        glyphs.append(glyph)
    result=Image.new('RGBA',(sum(g.width+1 for g in glyphs)-1,12))
    x=0
    for g in glyphs:result.alpha_composite(g,(x,0));x+=g.width+1
    return result
packet_previews=[]
for name,_,cost,_,_ in PLANTS:
    card=packet.copy();portrait=portraits[name].crop(portraits[name].getbbox());portrait.thumbnail((40,45),Image.Resampling.LANCZOS)
    card.alpha_composite(portrait,((50-portrait.width)//2,5+(45-portrait.height)//2))
    digits=price_image(cost);card.alpha_composite(digits,((50-digits.width)//2,54))
    packet_previews.append(card)
    hud_asset('ng_packet_'+name,card)
preview=Image.new('RGBA',(50*len(packet_previews),70))
for i,card in enumerate(packet_previews):preview.alpha_composite(card,(i*50,0))
preview.save(root/'seed-packets-preview.png')
hud_asset('ng_packet_glow',animations.image('particles/SeedPacketFlash.png'))

from prepare_held import prepare as prepare_held
held_models,held_weapons=[],[]
if os.environ.get('NG_BUILD_HELD','1')=='1':
    held_models,held_weapons=prepare_held(base,portraits,image_asset,materials)

assets_gsc=['// Generated integration manifest; all visual resources come from the installed games.','init()','{','    level.ng_clips = [];','    level.ng_clip_msec = [];']
for name in fx_names:
    key=name.removeprefix('ng/')
    assets_gsc.append(f'    level.ng_clips["{key}"] = LoadFX( "{name}" );')
    if key in clips: assets_gsc.append(f'    level.ng_clip_msec["{key}"] = {round(clips[key]["count"]*1000/clips[key]["fps"])};')
for key,target in aliases.items():
    assets_gsc.append(f'    level.ng_clips[\"{key}\"] = level.ng_clips[\"{target}\"];')
    if key in clips:
        msec=round(clips[key]['count']*1000/clips[key]['fps'])
        assets_gsc.append(f'    level.ng_clip_msec[\"{key}\"] = {msec};')
assets_gsc += ['    level.ng_base = [];','    level.ng_anchor = [];','    level.ng_packet = [];','    level.ng_cost = [];','    level.ng_cooldown = [];','    level.ng_names = [];']
for i,name in enumerate(plant_names):
    _,label,cost,cooldown,_=PLANTS[i]
    assets_gsc += [f'    level.ng_cost[{i}] = {cost};',f'    level.ng_names[{i}] = \"{label}\";',f'    level.ng_cooldown[{i}] = {cooldown};']
    assets_gsc += [f'    level.ng_base[{i}] = "{name}";',f'    level.ng_anchor[{i}] = {anchors[name]:.5f};',f'    level.ng_packet[{i}] = "ng_packet_{name}";',f'    PrecacheShader( "ng_packet_{name}" );']
assets_gsc += ['    PrecacheShader( "ng_seedbank" );','    PrecacheShader( "ng_packet_glow" );','}']
assets_gsc.insert(-1,'    level.ng_weapons = [];')
for i,weapon in enumerate(held_weapons):
    assets_gsc.insert(-1,f'    level.ng_weapons[{i}] = \"{weapon}\";')
    assets_gsc.insert(-1,f'    PrecacheItem( \"{weapon}\" );')
(raw/'maps/_nacht_garden_assets.gsc').write_text('\n'.join(assets_gsc)+'\n')

from prepare_sounds import prepare as prepare_sounds
sound_names=prepare_sounds(base)

# Native linker supplies effect structures, OAT supplies the final materials.
zone=native/'zone_source'; (zone/'english/assetlist').mkdir(parents=True,exist_ok=True)
(zone/'english/assetlist/ng_materials.csv').write_text(''.join('material,'+m+'\n' for m in materials))
(zone/'ng_world.csv').write_text('ignore_full,ng_materials\nsound,ng_pvz,,all_sp\n'+''.join('fx,'+n+'\n' for n in fx_names)+''.join('xmodel,'+n+'\n' for n in held_models))
manifest=root/'zone_source/nacht_garden.zone'
with manifest.open('a') as f:
    f.write('rawfile,maps/_nacht_garden_assets.gsc\n')
    f.write(''.join('material,'+m+'\n' for m in materials))
    f.write(''.join('fx,'+n+'\n' for n in fx_names))
    f.write(''.join('sound,'+n+'\n' for n in sound_names))
    f.write('sound,,weap_pickup\nsound,,melee_swing_small\nsound,,melee_swing_small_plr\nsound,,weap_raise\nsound,,weap_raise_plr\nsound,,weap_putaway\nsound,,weap_putaway_plr\nsound,,weap_ammo_pickup\nsound,,player_out_of_ammo\n')
    f.write(''.join('weapon,'+n+'\n' for n in held_weapons))
(root/'animation-clips.json').write_text(json.dumps(clips,indent=2)+'\n')
(root/'asset-provenance.json').write_text(json.dumps({'note':'Original installed PvZ frame transforms converted to atlases; original WaW effect shader/material. Only integration descriptors and gameplay logic are new.', 'source_sha256':base.provenance},indent=2)+'\n')
print('Prepared original animation atlases and world-effect descriptors.')
