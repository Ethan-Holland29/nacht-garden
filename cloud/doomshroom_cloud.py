"""ROCm rendering of original Doom-shroom tracks and original Doom particle artwork.

Particle motion is a deterministic port of the supplied Doom.xml parameters.
The original full-screen flash is supplied by WaW's actual nuke power-up.
"""
import io,json,math,random,re,zipfile,hashlib
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import torch
import all_plants_cloud as ap

SPECS=[dict(name='doomshroom_idle',source='DoomShroom',first=0,count=20,rate=12,fps=24,loop=True),
       dict(name='doomshroom_explode',source='DoomShroom',first=19,count=33,rate=23,fps=46,loop=False),
       dict(name='doomshroom_sleep',source='DoomShroom',first=52,count=25,rate=12,fps=24,loop=True)]

def scalar(text,rng):
    if text.startswith('['):
        a,b=map(float,text[1:-1].split());return rng.uniform(min(a,b),max(a,b))
    return float(text)

def curve(text,rng,default=0):
    if text is None:return [(0.,default),(1.,default)]
    tokens=re.findall(r'(\[[^]]+\]|[-+.\deE]+)(?:,([-+.\deE]+))?',text)
    assert tokens,text
    if len(tokens)==1:return [(0.,scalar(tokens[0][0],rng)),(1.,scalar(tokens[0][0],rng))] if not tokens[0][0].startswith('[') else constant_range(tokens[0][0],rng)
    points=[]
    for i,(value,pos) in enumerate(tokens):points.append((float(pos)/100 if pos else i/(len(tokens)-1),scalar(value,rng)))
    if points[0][0]>0:points.insert(0,(0,points[0][1]))
    if points[-1][0]<1:points.append((1,points[-1][1]))
    return points

def constant_range(text,rng):
    v=scalar(text,rng);return [(0,v),(1,v)]

def at(points,t):
    for i in range(1,len(points)):
        if t<=points[i][0]:
            a,b=points[i-1],points[i];f=(t-a[0])/max(1e-9,b[0]-a[0]);return a[1]+f*(b[1]-a[1])
    return points[-1][1]

class DoomParticles(ap.ClipRenderer):
    def __init__(self,bundle,device):
        rng=random.Random(500);pictures={};self.parts={};tracks=[]
        with zipfile.ZipFile(bundle) as z:
            root=ET.fromstring('<root>'+z.read('particles/Doom.xml').decode()+'</root>')
            for e in root:
                if e.findtext('FullScreen')=='1':continue
                image_name=e.findtext('Image');file={'IMAGE_DOOM':'Doom','IMAGE_DOOMSHROOM_EXPLOSION_BASE':'DoomShroom_Explosion_Base','IMAGE_DOOMSHROOM_EXPLOSION_STEM':'DoomShroom_Explosion_Stem','IMAGE_DOOMSHROOM_EXPLOSION_TOP':'DoomShroom_Explosion_Top'}[image_name]
                original=Image.open(io.BytesIO(z.read('particles/'+file+'.png'))).convert('RGBA')
                for i in range(int(e.findtext('SpawnMaxLaunched','1'))):
                    name=e.findtext('Name')+'_'+str(i);part={};part['count']=int(e.findtext('ImageFrames','1'));part['animrate']=float(e.findtext('AnimationRate','0'))
                    bright=scalar(e.findtext('ParticleBrightness','1'),rng)
                    for f in range(part['count']):
                        w=original.width//part['count'];arr=np.array(original.crop((f*w,0,(f+1)*w,original.height)));arr[:,:,:3]=np.rint(arr[:,:,:3].astype(float)*bright).astype(np.uint8);pictures[name+'_'+str(f)]=arr
                    part['w']=original.width//part['count'];part['h']=original.height
                    for key,tag,default in [('alpha','ParticleAlpha',1),('scale','ParticleScale',1),('stretch','ParticleStretch',1),('spin','ParticleSpinSpeed',0)]:part[key]=curve(e.findtext(tag),rng,default)
                    part['rot']=rng.uniform(0,360) if e.findtext('RandomLaunchSpin')=='1' else 0
                    part['x']=float(e.findtext('EmitterOffsetX','0'));part['y']=float(e.findtext('EmitterOffsetY','0'))
                    if e.findtext('EmitterType')=='Box':part['x']+=scalar(e.findtext('EmitterBoxX'),rng);part['y']+=scalar(e.findtext('EmitterBoxY'),rng)
                    if e.findtext('EmitterType')=='Circle':
                        radius=scalar(e.findtext('EmitterRadius'),rng);angle=rng.uniform(0,2*math.pi);part['x']+=math.cos(angle)*radius;part['y']+=math.sin(angle)*radius
                    part['fields']=[]
                    for f in list(e.findall('Field'))+list(e.findall('SystemField')):
                        kind=f.findtext('FieldType');assert kind in ('Position','SystemPosition','Shake'),kind
                        part['fields'].append((kind,curve(f.findtext('X'),rng),curve(f.findtext('Y'),rng)))
                    self.parts[name]=part;tracks.append((name,[dict(x=0.,y=0.,sx=1.,sy=1.,kx=0.,ky=0.,a=1.,f=0.,i=name+'_0')]))
        super().__init__(tracks,pictures,device,dict(source='DoomParticles'))
    def pose(self,name,phase):
        p=self.parts[name];t=phase/36;sec=phase/24;x=p['x'];y=p['y']
        for kind,px,py in p['fields']:
            if kind=='Shake':x+=math.sin(phase*2.17)*at(px,t);y+=math.cos(phase*2.73)*at(py,t)
            else:x+=at(px,t);y+=at(py,t)
        scale=at(p['scale'],t);sy=scale*at(p['stretch'],t);angle=p['rot']+at(p['spin'],t)*sec;r=math.radians(angle)
        # Source particle images are centered; the shared renderer uses top-left transforms.
        x+=64-math.cos(r)*scale*p['w']/2+math.sin(r)*sy*p['h']/2
        y+=192-math.sin(r)*scale*p['w']/2-math.cos(r)*sy*p['h']/2
        frame=int(sec*p['animrate'])%p['count']
        return dict(x=x,y=y,sx=scale,sy=sy,kx=angle,ky=angle,a=at(p['alpha'],t),f=0,i=name+'_'+str(frame))

def run(bundle='doomshroom-source.zip',output='amd-doomshroom.zip'):
    previous=ap.SPECS
    try:ap.SPECS=SPECS;report=ap.run(bundle,'doom-body-private.zip')
    finally:ap.SPECS=previous
    report['scope']='Original Doom-shroom idle, explode and sleep tracks; original Doom.xml particle layers including DOOM lettering'
    gpu=DoomParticles(bundle,'cuda');cpu=DoomParticles(bundle,'cpu');a=cpu.render([0,12,30]);b=gpu.render([0,12,30]).cpu();d=(a-b).abs();assert float(d.max())<.01 and float(d.mean())<.0001
    frames=[]
    for begin in range(0,36,4):frames += [Image.fromarray(x) for x in ap.core.rgba(gpu.render(np.arange(begin,min(begin+4,36))))]
    boxes=[f.getbbox() for f in frames];bounds=[min(b[0] for b in boxes)-2,min(b[1] for b in boxes)-2,max(b[2] for b in boxes)+2,max(b[3] for b in boxes)+2];assert min(bounds)>=0 and max(bounds)<=512,bounds
    name='doomshroom_burst';report['clips'][name]=dict(name=name,source='Doom.xml',frames=36,fps=24,duration_msec=1500,loop=False,bounds=bounds,max_cpu_gpu_error=float(d.max()),mean_cpu_gpu_error=float(d.mean()),source_origin=[256,384],method='deterministic port of source particle counts, positions, scales, spin, alpha and original images; native nuke supplies screen flash')
    with zipfile.ZipFile('doom-body-private.zip') as old,zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for n in old.namelist():
            if n!='report.json':z.writestr(n,old.read(n))
        seq=[f.crop(bounds) for f in frames]
        for i,im in enumerate(seq):
            out=io.BytesIO();im.save(out,format='PNG');z.writestr(f'{name}/{i:03}.png',out.getvalue())
        out=io.BytesIO();seq[0].save(out,format='WEBP',save_all=True,append_images=seq[1:],duration=[round((i+1)*1000/24)-round(i*1000/24) for i in range(36)],loop=0,lossless=True);z.writestr(name+'.webp',out.getvalue());z.writestr('report.json',json.dumps(report,indent=2))
    return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
