#!/usr/bin/env python3
"""Prepare a private mod using only the two locally installed games' artwork."""
from pathlib import Path
import hashlib, json, math, os, shutil, struct, xml.etree.ElementTree as ET, zlib
from PIL import Image

ROOT = Path(__file__).resolve().parent
TASK = ROOT.parent
GAME = Path(os.environ['WAW_GAME_DIR']).expanduser()
PVZ = Path(os.environ['PVZ_GAME_DIR']).expanduser()
RAW = ROOT / 'raw'
for directory in ['maps', 'images', 'materials']:
    (RAW / directory).mkdir(parents=True, exist_ok=True)

def pak_entries():
    data = bytes(c ^ 0xf7 for c in (PVZ / 'main.pak').read_bytes())
    assert data[:8] == b'\xc0J\xc0\xba\0\0\0\0', 'Unsupported PvZ archive'
    pos, entries = 8, []
    while True:
        flag = data[pos]; pos += 1
        if flag & 128: break
        length = data[pos]; pos += 1
        name = data[pos:pos+length].decode().replace('\\', '/'); pos += length
        size = struct.unpack_from('<I', data, pos)[0]; pos += 12
        entries.append((name, size))
    result = {}
    for name, size in entries:
        result[name.lower()] = (name, data[pos:pos+size]); pos += size
    assert pos == len(data)
    return result

assets = pak_entries()
provenance = {}
def asset(path):
    name, data = assets[path.lower()]
    provenance[name] = hashlib.sha256(data).hexdigest()
    return data

def reanim_frame(name, index, crop=True):
    """Evaluate original reanimation transforms; no new drawing or geometry."""
    from io import BytesIO
    root = ET.fromstring('<root>' + asset('reanim/' + name + '.reanim').decode() + '</root>')
    canvas = Image.new('RGBA', (256, 256))
    for track in root.findall('track'):
        state = dict(x=0., y=0., sx=1., sy=1., kx=0., ky=0., a=1., f=0., i='')
        for t in track.findall('t')[:index+1]:
            for element in t:
                if element.tag in state:
                    state[element.tag] = element.text if element.tag == 'i' else float(element.text)
        if not state['i'] or state['f'] < 0 or state['a'] <= 0: continue
        path = 'reanim/' + state['i'].removeprefix('IMAGE_REANIM_') + '.png'
        picture = Image.open(BytesIO(asset(path))).convert('RGBA')
        # Reanim uses independently skewed x/y axes, in degrees.
        kx, ky = math.radians(state['kx']), math.radians(state['ky'])
        a, b = math.cos(kx)*state['sx'], -math.sin(ky)*state['sy']
        c, d = math.sin(kx)*state['sx'], math.cos(ky)*state['sy']
        det = a*d-b*c
        if abs(det) < 1e-8: continue
        x, y = state['x'] + 64, state['y'] + 64
        inv = (d/det, -b/det, (b*y-d*x)/det, -c/det, a/det, (c*x-a*y)/det)
        picture = picture.transform(canvas.size, Image.Transform.AFFINE, inv, Image.Resampling.BICUBIC)
        if state['a'] != 1:
            picture.putalpha(picture.getchannel('A').point(lambda v: round(v*state['a'])))
        canvas.alpha_composite(picture)
    box = canvas.getbbox()
    assert box, f'Empty original reanimation: {name} frame {index}'
    return canvas.crop(box) if crop else canvas

def iwi(name, image):
    # CoD WaW accepts the original IWI v6 RGBA format, with no mip maps.
    # Padding preserves the sprite's aspect ratio in a power-of-two texture.
    side = 1 << (max(image.size)-1).bit_length()
    target = Image.new('RGBA', (side, side))
    target.alpha_composite(image, ((side-image.width)//2, side-image.height))
    pixels = target.tobytes('raw', 'BGRA')
    header = b'IWi\x06' + struct.pack('<BBHHH4I', 1, 2, side, side, 1, *([28+len(pixels)]*4))
    (RAW/'images'/f'{name}.iwi').write_bytes(header+pixels)
    target.save(ROOT/f'{name}-preview.png')
    template = json.loads((TASK/'work/waw-materials/materials/rank_pvt1.json').read_text())
    template['textures'][0]['image'] = name
    (RAW/'materials'/f'{name}.json').write_text(json.dumps(template, indent=2)+'\n')

for name, source, frame in [('ng_peashooter','PeaShooter',79), ('ng_sunflower','SunFlower',4), ('ng_wallnut','Wallnut',0)]:
    iwi(name, reanim_frame(source, frame))
from io import BytesIO
iwi('ng_pea', Image.open(BytesIO(asset('images/ProjectilePea.png'))).convert('RGBA'))

# Extract just the two original scripts that need integration hooks.
zone = zlib.decompress((GAME/'zone/english/nazi_zombie_prototype.ff').read_bytes()[12:])
def stock_script(name):
    marker = name.encode()+b'\0'; at = zone.find(marker)
    assert at >= 12
    length = struct.unpack_from('<I', zone, at-8)[0]
    raw = zone[at+len(marker):at+len(marker)+length]
    assert raw.startswith(b'#include') and zone[at+len(marker)+length] == 0
    provenance[name] = hashlib.sha256(raw).hexdigest()
    return raw.decode().replace('\r\n','\n')

name = 'maps/nazi_zombie_prototype.gsc'
code = stock_script(name)
needle = '\tmaps\\_zombiemode::main();'
assert code.count(needle) == 1
code = code.replace(needle, '\tmaps\\_nacht_garden::init();\n' + needle)
(RAW/name).write_text(code)
name = 'maps/_zombiemode_spawner.gsc'
code = stock_script(name)
needle = '\t\t\tself SetGoalPos( self.favoriteenemy.origin );'
assert code.count(needle) == 1
code = code.replace(needle, '\t\t\tif ( !self maps\\_nacht_garden::garden_goal() )\n\t\t\t{\n'+needle+'\n\t\t\t}')
(RAW/name).write_text(code)

(ROOT/'zone_source').mkdir(exist_ok=True)
lines = ['>game,T4', '>name,mod', 'rawfile,maps/nazi_zombie_prototype.gsc', 'rawfile,maps/_zombiemode_spawner.gsc', 'rawfile,maps/_nacht_garden.gsc']
lines += ['material,'+n for n in ['ng_peashooter','ng_sunflower','ng_wallnut','ng_pea']]
(ROOT/'zone_source/nacht_garden.zone').write_text('\n'.join(lines)+'\n')
(ROOT/'asset-provenance.json').write_text(json.dumps({'note':'Sprite images are rendered from original PvZ reanimation transforms. Material template is original WaW rank_pvt1, with only its image reference changed. No new artwork.', 'source_sha256':provenance},indent=2)+'\n')
print('Prepared original sprite conversions, original map-script hooks, and zone manifest.')
