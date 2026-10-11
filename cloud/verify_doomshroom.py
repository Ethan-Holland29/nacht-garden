"""Verify every Doom-shroom atlas page against the downloaded AMD-rendered frames."""
from pathlib import Path
import argparse,io,json,re,zipfile
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--test',type=Path,required=True);p.add_argument('--cloud',type=Path,required=True);a=p.parse_args()
build=json.loads((a.test/'doom-build-report.json').read_text());result={}
with zipfile.ZipFile(a.cloud) as z:
 for clip,v in build['clips'].items():
  checked=0;margins=[]
  effect=(a.test/'raw/fx/ng'/('full_'+clip+'.efx')).read_text()
  flags=re.findall(r'(?m)^\s*flags\s+([^;]+);',effect)
  assert len(flags)==len(v['pages']) and all('nonUniformScale' in f.split() for f in flags),clip
  for page in v['pages']:
   data=(a.test/'raw/images'/(page['image']+'.iwi')).read_bytes();atlas=Image.frombytes('RGBA',tuple(page['dimensions']),data[28:],'raw','BGRA');cw,ch=page['cell'];cols=page['columns']
   assert len(data)-28==page['texture_bytes'] and page['texture_bytes']<=8*2**20
   for i in range(page['frames']):
    original=Image.open(io.BytesIO(z.read(f'{clip}/{page["start"]+i:03}.png'))).convert('RGBA');packed=atlas.crop(((i%cols)*cw,(i//cols)*ch,(i%cols+1)*cw,(i//cols+1)*ch))
    assert packed.crop(packed.getbbox()).tobytes()==original.crop(original.getbbox()).tobytes(),(clip,i)
    box=packed.getbbox();margin=min(box[0],box[1],cw-box[2],ch-box[3]);margins.append(margin)
    assert margin>=2,('Visible pixels touch atlas cell boundary',clip,i,box)
    checked+=1
  assert checked==v['frames'];result[clip]={'frames_checked':checked,'packed_pixels_equal_cloud':True,'pages':len(v['pages']),
    'independent_width_height_verified':True,'minimum_transparent_border_pixels':min(margins)}
(a.test/'doom-frame-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Doom-shroom:',sum(v['frames_checked'] for v in result.values()),'frames verified without pixel loss.')
