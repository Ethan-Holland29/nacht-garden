"""Check packed frame pixels, large disconnected components and memory budget."""
from pathlib import Path
from PIL import Image
import argparse,io,json,zipfile

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
   data=(args.test/'raw/images'/('ng_fx_amd_'+name+'.iwi')).read_bytes()
   atlas=Image.frombytes('RGBA',tuple(v['atlas_dimensions']),data[28:],'raw','BGRA')
   cw,ch=v['cell_dimensions'];bad=[]
   for i in range(v['frames']):
    cloud=Image.open(io.BytesIO(z.read(f'{name}/{i:03}.png'))).convert('RGBA')
    packed=atlas.crop(((i%16)*cw,(i//16)*ch,(i%16+1)*cw,(i//16+1)*ch))
    # Crop only transparent margins to compare every visible source pixel.
    assert cloud.crop(cloud.getbbox()).tobytes()==packed.crop(packed.getbbox()).tobytes(),(name,i)
    if disconnected(packed):bad.append(i)
   assert not bad,(name,bad)
   result[name]={'verified_frames':v['frames'],'disconnected_large_components':bad,'packed_pixels_equal_cloud':True}
 (args.test/'frame-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Verified',sum(v['verified_frames'] for v in result.values()),'frames: no changed pixels or large disconnected components.')
