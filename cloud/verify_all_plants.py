"""Check packed frame pixels, large disconnected components and memory budget."""
from pathlib import Path
from PIL import Image
import argparse,io,json,re,zipfile

def disconnected(im):
 p=im.getchannel('A').load();todo={(x,y) for y in range(im.height) for x in range(im.width) if p[x,y]>100};large=0
 while todo:
  queue=[todo.pop()];count=0
  while queue:
   x,y=queue.pop();count+=1
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
    other=(x+dx,y+dy)
    if other in todo:todo.remove(other);queue.append(other)
  large+=count>50
 return large>1

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cloud',type=Path,required=True);p.add_argument('--test',type=Path,required=True);args=p.parse_args()
 report=json.loads((args.test/'build-report.json').read_text());result={}
 with zipfile.ZipFile(args.cloud) as z:
  for name,v in report['clips'].items():
   effect=(args.test/'raw/fx/ng'/('full_'+name+'.efx')).read_text()
   flags=re.search(r'(?m)^\s*flags\s+([^;]+);',effect)[1].split()
   assert 'nonUniformScale' in flags,('Rectangular sprite would be stretched',name)
   cw,ch=v['cell_dimensions'];units=v['units_per_pixel']
   for key,wanted in [('sizeGraph0',cw*units),('sizeGraph1',ch*units)]:
    assert abs(float(re.search(r'(?m)^\s*'+key+r'\s+([\d.]+)',effect)[1])-wanted)<1e-5
   data=(args.test/'raw/images'/('ng_fx_full_'+name+'.iwi')).read_bytes()
   atlas=Image.frombytes('RGBA',tuple(v['atlas_dimensions']),data[28:],'raw','BGRA')
   cw,ch=v['cell_dimensions'];bad=[];margins=[]
   for i in range(v['frames']):
    cloud=Image.open(io.BytesIO(z.read(f'{name}/{i:03}.png'))).convert('RGBA')
    packed=atlas.crop(((i%v['atlas_columns'])*cw,(i//v['atlas_columns'])*ch,(i%v['atlas_columns']+1)*cw,(i//v['atlas_columns']+1)*ch))
    # Crop only transparent margins to compare every visible source pixel.
    assert cloud.crop(cloud.getbbox()).tobytes()==packed.crop(packed.getbbox()).tobytes(),(name,i)
    box=packed.getbbox();margin=min(box[0],box[1],cw-box[2],ch-box[3]);margins.append(margin)
    assert margin>=2,('Visible pixels touch atlas cell boundary',name,i,box)
    if disconnected(packed):bad.append(i)
   # Original rock, leaf and water pieces may be separate. Record for visual review.
   assert v['texture_bytes']<=8*2**20
   assert max(v['atlas_dimensions'])<=2048
   result[name]={'verified_frames':v['frames'],'disconnected_large_components':bad,'packed_pixels_equal_cloud':True,
     'independent_width_height_verified':True,'minimum_transparent_border_pixels':min(margins)}
 (args.test/'frame-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Verified',sum(v['verified_frames'] for v in result.values()),'frames: all packed pixels unchanged; separate components recorded for review.')
