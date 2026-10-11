"""Original emerged Potato Mine artwork for the packet and Betty-held sprite."""
from pathlib import Path
import argparse,io,json,re,shutil,struct,sys,zipfile
from PIL import Image
p=argparse.ArgumentParser(description=__doc__)
for key in ['base','native','output','source']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();raw=a.output/'raw';sys.path.insert(0,str(a.base));from pvz_animation import Reanimations
with zipfile.ZipFile(a.source) as z:
 anim=Reanimations(z.read);frame=anim.frame('PotatoMine',20);portrait=frame.crop(frame.getbbox())
 packet=anim.image('images/seeds.png').crop((0,0,50,70));small=portrait.copy();small.thumbnail((40,45),Image.Resampling.LANCZOS)
 packet.alpha_composite(small,((50-small.width)//2,5+(45-small.height)//2))
 font=z.read('data/Pico129.txt').decode('latin1');rects=[tuple(map(int,m)) for m in re.findall(r'\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)',re.search(r'Define RectList\s*\((.*?)\);',font,re.S)[1])]
 glyphs=[];fontim=anim.image('data/_Pico129.png')
 for digit in '25':
  x,y,w,h=rects[52+int(digit)];glyph=Image.new('RGBA',(w,h),(0,0,0,0));glyph.putalpha(fontim.crop((x,y,x+w,y+h)).convert('L'));glyphs.append(glyph)
 digits=Image.new('RGBA',(sum(g.width+1 for g in glyphs)-1,12));x=0
 for g in glyphs:digits.alpha_composite(g,(x,0));x+=g.width+1
 packet.alpha_composite(digits,((50-digits.width)//2,54))
name='ng_held_potatomine_surface';packetname='ng_packet_potatomine_surface'
for d in ['images','materials/mc','weapons']:(raw/d).mkdir(parents=True,exist_ok=True)
def iwi(name,im):
 data=im.tobytes('raw','BGRA');(raw/'images'/(name+'.iwi')).write_bytes(b'IWi\x06'+struct.pack('<BBHHH4I',1,2,im.width,im.height,1,*([28+len(data)]*4))+data)
iwi(name,portrait.resize((128,128),Image.Resampling.LANCZOS));iwi(packetname,packet.resize((64,128),Image.Resampling.LANCZOS))
for old,new,sub in [('ng_held_potatomine',name,'mc'),('ng_packet_potatomine',packetname,'')]:
 material=json.loads((a.base/'raw/materials'/sub/(old+'.json')).read_text())
 for tex in material['textures']:
  if tex['image']==old:tex['image']=new
 (raw/'materials'/sub/(new+'.json')).write_text(json.dumps(material,indent=2)+'\n')
original=(a.native/'model_export/ng_held_potatomine.xmodel_export').read_text();width=min(14,12*portrait.width/portrait.height);height=width*portrait.height/portrait.width
points=[(-width/2,0,0),(width/2,0,0),(width/2,0,height),(-width/2,0,height)]
s=original.replace('ng_held_potatomine',name)
for i,(x,y,h) in enumerate(points):
 s,n=re.subn(r'(VERT '+str(i)+r'\nOFFSET )[^\n]+',lambda m:m[1]+f'{x}, {y}, {h}',s);assert n==1
skeleton_unchanged=original.split('NUMVERTS')[0]==s.split('NUMVERTS')[0]
assert skeleton_unchanged
(a.native/'model_export'/(name+'.xmodel_export')).write_text(s)
shutil.copy2(a.native/'raw/material_properties/ng_held_potatomine',a.native/'raw/material_properties'/name)
stub=bytearray((a.native/'raw/materials/ng_held_potatomine').read_bytes());struct.pack_into('<I',stub,0,len(stub));stub.extend(name.encode()+b'\0');(a.native/'raw/materials'/name).write_bytes(stub)
(a.native/'source_data/ng_potato_surface.gdt').write_text('{\n"'+name+'" ( "xmodel.gdf" )\n{\n"type" "animated"\n"filename" "'+name+'.xmodel_export"\n"highLodDist" "1000000"\n"collisionLOD" "None"\n}\n}\n')
s=(a.base/'raw/weapons/ng_seed_potatomine').read_text();assert '\\gunModel\\ng_held_potatomine\\' in s
(raw/'weapons/ng_seed_potatomine').write_text(s.replace('\\gunModel\\ng_held_potatomine\\','\\gunModel\\'+name+'\\'))
packet.save(a.output/'potato-packet-preview.png');portrait.save(a.output/'potato-held-preview.png')
(a.output/'potato-surface-report.json').write_text(json.dumps({'source':'PotatoMine.reanim','original_frame':20,'appearance':'fully emerged; original ground placement still begins buried','held_dimensions':[width,height],'packet_price':25,'original_betty_skeleton_unchanged':skeleton_unchanged},indent=2)+'\n')
print('Prepared emerged Potato Mine packet and held sprite using original artwork.')
