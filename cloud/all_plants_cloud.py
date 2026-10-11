"""ROCm animation expansion: the remaining original plant roster; Wall-nut blink repair.

Requires animation_lab.py and all-plants-source.zip. Outputs remain private.
Does not modify the accepted Peashooter renderer or its files.
"""
import copy, hashlib, io, json, math, time, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import torch
import animation_lab as core
from animation_lab import SIZE, F, NUMERIC

SPECS = [
 dict(name='sunflower_idle',source='SunFlower',first=4,count=25,rate=12,fps=60,loop=True),
 dict(name='repeater_idle',source='PeaShooter',first=79,count=25,rate=12,fps=60,loop=True),
 dict(name='repeater_shoot',source='PeaShooter',first=54,count=25,rate=24,fps=48,loop=False),
 *[dict(name='wallnut'+('_crack'+str(stage) if stage else '')+'_idle',source='Wallnut',first=0,count=51,rate=12,fps=24,loop=True,stage=stage) for stage in range(3)]
]

# Source rates retain the mod's existing action timing; no spatial downscaling.
SPECS += [
 dict(name='cherrybomb_idle',source='CherryBomb',first=14,count=13,rate=30,fps=60,loop=True),
 dict(name='cherrybomb_explode',source='CherryBomb',first=0,count=14,rate=30,fps=60,loop=False),
 dict(name='potatomine_rise',source='PotatoMine',first=1,count=19,rate=12,fps=24,loop=False),
 dict(name='potatomine_armed',source='PotatoMine',first=20,count=11,rate=12,fps=24,loop=True),
 *[dict(name='chomper_'+action,source='Chomper',first=first,count=count,rate=rate,fps=rate*2,loop=loop)
   for action,first,count,rate,loop in [('idle',0,25,12,True),('bite',25,25,24,False),('chew',50,16,12,True),('swallow',66,28,24,False)]],
 dict(name='squash_idle',source='Squash',first=5,count=19,rate=12,fps=24,loop=True),
 dict(name='squash_attack',source='Squash',first=37,count=27,rate=24,fps=48,loop=False),
 dict(name='squash_land',source='Squash',first=65,count=8,rate=24,fps=48,loop=False),
 dict(name='lilypad_idle',source='LilyPad',first=0,count=48,rate=12,fps=24,loop=True),
 dict(name='tanglekelp_idle',source='Tanglekelp',first=5,count=22,rate=12,fps=24,loop=True),
 dict(name='tanglekelp_grab',source='Tanglekelp',first=27,count=5,rate=12,fps=24,loop=False),
]

def read_source(bundle, source):
    with zipfile.ZipFile(bundle) as z:
        manifest=json.loads(z.read('provenance.json'))
        for name,digest in manifest['files'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
        xml=ET.fromstring('<root>'+z.read('reanim/'+source+'.reanim').decode()+'</root>')
        tracks=[];pictures={}
        for t in xml.findall('track'):
            state=dict(x=0.,y=0.,sx=1.,sy=1.,kx=0.,ky=0.,a=1.,f=0.,i='');states=[]
            for frame in t.findall('t'):
                for item in frame:
                    if item.tag in state:state[item.tag]=item.text if item.tag=='i' else float(item.text)
                states.append(state.copy())
            name=t.findtext('name')
            if any(n==name for n,_ in tracks):name=name+'#'+str(len(tracks))
            tracks.append((name,states))
        keys={s['i'] for _,states in tracks for s in states if s['i']}
        if source=='Wallnut':keys.update('IMAGE_REANIM_WALLNUT_CRACKED'+str(i) for i in [1,2])
        for key in keys:
            pictures[key]=np.array(Image.open(io.BytesIO(z.read('reanim/'+key.removeprefix('IMAGE_REANIM_')+'.png'))).convert('RGBA'))
    return tracks,pictures,manifest

def matrix(s):
    x,y=math.radians(s['kx']),math.radians(s['ky'])
    return np.array([[math.cos(x)*s['sx'],-math.sin(y)*s['sy'],s['x']],
                     [math.sin(x)*s['sx'],math.cos(y)*s['sy'],s['y']],[0.,0.,1.]])

def interpolate(states,phase,first,count,loop=True):
    phase=phase%count if loop else min(max(phase,0),count-1)
    index=int(math.floor(phase));fraction=phase-index
    a=states[min(first+index,len(states)-1)]
    other=(index+1)%count if loop else min(index+1,count-1)
    b=states[min(first+other,len(states)-1)];pose=a.copy()
    if a['i']==b['i'] and (a['f']>=0)==(b['f']>=0):
        for k in core.NUMERIC:
            delta=b[k]-a[k]
            if k in ('kx','ky'):delta=(delta+180)%360-180
            pose[k]+=fraction*delta
    return pose

class ClipRenderer(core.Renderer):
    def __init__(self,tracks,pictures,device,spec):
        super().__init__(tracks,pictures,device)
        self.spec=spec;self.state=dict(tracks);self.attachment_errors=[]
        names=[n for n,_ in tracks]
        self.stem=set(names[:names.index('anim_stem')+1]) if 'anim_stem' in names else set()
    def attach(self,pose,parent,bind):
        transform=matrix(parent)@np.linalg.inv(matrix(bind))@matrix(pose)
        out=pose.copy();out.update(x=float(transform[0,2]),y=float(transform[1,2]),
            sx=float(np.hypot(transform[0,0],transform[1,0])),sy=float(np.hypot(transform[0,1],transform[1,1])),
            kx=math.degrees(math.atan2(transform[1,0],transform[0,0])),ky=math.degrees(math.atan2(-transform[0,1],transform[1,1])))
        error=float(np.abs(np.linalg.inv(matrix(parent))@matrix(out)-np.linalg.inv(matrix(bind))@matrix(pose)).max())
        assert error<1e-7,error
        self.attachment_errors.append(error)
        return out
    def pose(self,name,phase):
        s=self.spec;states=self.state[name]
        if s['source']=='Wallnut':
            pose=interpolate(states,phase,0,17)
            if name.startswith('anim_blink_'):
                events={'anim_blink_twice':(17,23,7),'anim_blink_thrice':(34,31,11)}
                if name=='anim_blink_twitch':
                    pose['f']=-1
                    return pose
                start,first,count=events[name];event=phase-start
                if not 0<=event<count:pose['f']=-1
                else:
                    pose=interpolate(states,event,first,count,False)
                    parent=interpolate(self.state['anim_face'],phase,0,17)
                    pose=self.attach(pose,parent,self.state['anim_face'][0])
            if s['stage'] and pose['i']=='IMAGE_REANIM_WALLNUT_BODY':
                pose['i']='IMAGE_REANIM_WALLNUT_CRACKED'+str(s['stage'])
            return pose
        if s['name']=='repeater_shoot':
            if name in self.stem:return interpolate(states,phase,4,25,False)
            pose=interpolate(states,phase,54,25,False)
            return self.attach(pose,interpolate(self.state['anim_stem'],phase,4,25,False),self.state['anim_stem'][4])
        if s['name']=='squash_attack':
            # Preserve the existing 500ms look + 625ms jump sequence.
            if phase<12:return interpolate(states,phase/2,37,6,False)
            return interpolate(states,phase-12,50,15,False)
        if s['source']=='LilyPad':
            pose=interpolate(states,0,0,1)
            if name=='anim_blink' and 24<=phase<27:
                pose=interpolate(states,phase-24,1,3,False)
                pose=self.attach(pose,self.state['anim_idle'][0],self.state['anim_idle'][0])
            return pose
        if s['source'] not in ('SunFlower','PeaShooter'):
            pose=interpolate(states,phase,s['first'],s['count'],s['loop'])
            if s['name']=='potatomine_armed' and name=='PotatoMine_blink' and 5<=phase<8:
                pose=interpolate(states,phase-5,32,3,False)
                parent=interpolate(self.state['anim_face'],phase,20,11)
                pose=self.attach(pose,parent,self.state['anim_face'][20])
            return pose
        pose=interpolate(states,phase,s['first'],s['count'])
        if name=='anim_blink' and phase<3:
            pose=interpolate(states,phase,1,3,False)
            parent_name='anim_idle' if s['source']=='SunFlower' else 'anim_face'
            bind_index=4 if s['source']=='SunFlower' else 29
            parent=interpolate(self.state[parent_name],phase,s['first'],s['count'])
            pose=self.attach(pose,parent,self.state[parent_name][bind_index])
        return pose
    @torch.inference_mode()
    def render(self, phases):
        n=len(phases)
        canvas=torch.zeros((n,4,SIZE,SIZE),device=self.device)
        for name,states in self.tracks:
            sampled=[self.pose(name,float(p)) for p in phases]
            keys=sorted({s['i'] for s in sampled if s['i'] and s['f']>=0 and s['a']>0})
            for key in keys:
                ids=[j for j,s in enumerate(sampled) if s['i']==key and s['f']>=0 and s['a']>0]
                values=torch.tensor([[sampled[j][k] for k in NUMERIC] for j in ids],device=self.device)
                x,y,sx,sy,kx,ky,alpha=values.unbind(1)
                kx=kx*math.pi/180;ky=ky*math.pi/180
                a=torch.cos(kx)*sx;b=-torch.sin(ky)*sy;c=torch.sin(kx)*sx;d=torch.cos(ky)*sy
                det=a*d-b*c
                valid=det.abs()>1e-8;det=torch.where(valid,det,torch.ones_like(det))
                dx=self.xx[None]-x[:,None,None]-192
                dy=self.yy[None]-y[:,None,None]-192
                u=(d[:,None,None]*dx-b[:,None,None]*dy)/det[:,None,None]
                v=(-c[:,None,None]*dx+a[:,None,None]*dy)/det[:,None,None]
                img=self.images[key];h,w=img.shape[-2:]
                grid=torch.stack((2*u/w-1,2*v/h-1),-1)
                layer=F.grid_sample(img.expand(len(ids),-1,-1,-1),grid,mode='bicubic',padding_mode='zeros',align_corners=False)
                # Clamp bicubic overshoot while retaining premultiplied-alpha invariants.
                la=layer[:,3:4].clamp(0,1)
                rgb=layer[:,:3].clamp_min(0).minimum(la)
                layer=torch.cat((rgb,la),1)*alpha[:,None,None,None].clamp(0,1)*valid[:,None,None,None]
                index=torch.tensor(ids,device=self.device)
                old=canvas[index]
                canvas[index]=layer+old*(1-layer[:,3:4])
        return canvas

def run(bundle='all-plants-source.zip',output='amd-all-plants.zip'):
    assert torch.version.hip and torch.cuda.is_available(),'AMD ROCm GPU required'
    report={'gpu':torch.cuda.get_device_name(0),'rocm':torch.version.hip,'pytorch':torch.__version__,
            'scope':'Existing roster expansion: six remaining plant families and Wall-nut without forced twitch; accepted Sunflower and Repeater retained',
            'game_runtime_verified':False,'clips':{}}
    exports={};renderers={}
    for spec in SPECS:
        tracks,pictures,manifest=read_source(bundle,spec['source'])
        gpu=ClipRenderer(tracks,pictures,'cuda',spec);cpu=ClipRenderer(tracks,pictures,'cpu',spec)
        # Compare this actual attachment-aware path across devices.
        phases=[0.,0.5,spec['count']-0.25]
        a=cpu.render(phases);b=gpu.render(phases).cpu();diff=(a-b).abs()
        assert float(diff.max())<0.01 and float(diff.mean())<0.0001
        count=spec['count']*spec['fps']//spec['rate']
        assert count*spec['rate']==spec['count']*spec['fps']
        frames=[];core.sync('cuda');start=time.perf_counter()
        for begin in range(0,count,8):
            phases=np.arange(begin,min(begin+8,count))*spec['rate']/spec['fps']
            frames += [Image.fromarray(x) for x in core.rgba(gpu.render(phases))]
        core.sync('cuda');elapsed=time.perf_counter()-start
        # Every original body pose remains represented; attachments alter child
        # coordinates intentionally, preserving the original relative transform.
        for name,states in tracks:
            if name.startswith('anim_blink') or name=='PotatoMine_blink' or spec['source']=='LilyPad' or spec['name']=='squash_attack' or (spec['name']=='repeater_shoot' and name not in gpu.stem):continue
            for i in range(spec['count']):
                pose=gpu.pose(name,float(i))
                index=i%17 if spec['source']=='Wallnut' else (4+i if spec['name']=='repeater_shoot' else spec['first']+i)
                original=states[min(index,len(states)-1)]
                assert all(abs(pose[k]-original[k])<1e-7 for k in core.NUMERIC)
        edges=[]
        for i in range(len(frames) if spec['loop'] else len(frames)-1):
            a=np.asarray(frames[i]).astype(np.float32)/255;b=np.asarray(frames[(i+1)%len(frames)]).astype(np.float32)/255
            mask=(a[:,:,3]+b[:,:,3])>0.05
            edges.append(float(np.abs(a[:,:,:3]*a[:,:,3:]-b[:,:,:3]*b[:,:,3:])[mask].mean()))
        exports[spec['name']]=frames
        report['clips'][spec['name']]={**spec,'frames':len(frames),'duration_msec':round(spec['count']*1000/spec['rate']),
             'render_and_readback_seconds':elapsed,'max_cpu_gpu_error':float(diff.max()),'mean_cpu_gpu_error':float(diff.mean()),
             'max_attachment_error':max(gpu.attachment_errors,default=0),'body_keyframes_verified':spec['name'] not in ('squash_attack','lilypad_idle'),
             'source_bundle_sha256':hashlib.sha256(Path(bundle).read_bytes()).hexdigest(),
             'forced_wallnut_twitch':False,
             'artwork_generated':False,
             'wrap_difference':edges[-1] if spec['loop'] else None,'median_step_difference':float(np.median(edges))}
        print(spec['name'],len(frames),'frames',flush=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,frames in exports.items():
            family=name.split('_')[0]
            boxes=[im.getbbox() for im in frames]
            boxes=[b for b in boxes if b]
            bounds=[min(b[0] for b in boxes)-2,min(b[1] for b in boxes)-2,max(b[2] for b in boxes)+2,max(b[3] for b in boxes)+2]
            assert 0<=bounds[0]<bounds[2]<=512 and 0<=bounds[1]<bounds[3]<=512
            report['clips'][name]['bounds']=bounds
            seq=[im.crop(bounds) for im in frames]
            for i,im in enumerate(seq):
                data=io.BytesIO();im.save(data,format='PNG');z.writestr(f'{name}/{i:03}.png',data.getvalue())
            fps=report['clips'][name]['fps'];durations=[round((i+1)*1000/fps)-round(i*1000/fps) for i in range(len(seq))]
            buffer=io.BytesIO();seq[0].save(buffer,format='WEBP',save_all=True,append_images=seq[1:],duration=durations,loop=0,lossless=True)
            z.writestr(name+'.webp',buffer.getvalue())
        z.writestr('report.json',json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
