"""ROCm cloud resampling of original PvZ tracks, not FSR or AI-generated art."""
import io, json, math, time, statistics, hashlib, zipfile, platform
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

SIZE = 512
SOURCE_FPS = 12
FIRST, COUNT = 79, 25
DURATION = COUNT / SOURCE_FPS
NUMERIC = ('x','y','sx','sy','kx','ky','a')

def load_source(path='peashooter-source.zip'):
    with zipfile.ZipFile(path) as z:
        manifest = json.loads(z.read('provenance.json'))
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest, name
        root = ET.fromstring('<root>'+z.read('reanim/PeaShooterSingle.reanim').decode()+'</root>')
        tracks, pictures = [], {}
        for t in root.findall('track'):
            state = dict(x=0., y=0., sx=1., sy=1., kx=0., ky=0., a=1., f=0., i='')
            states = []
            for item in t.findall('t'):
                for e in item:
                    if e.tag in state: state[e.tag] = e.text if e.tag == 'i' else float(e.text)
                states.append(state.copy())
                if state['i'] and state['i'] not in pictures:
                    name='reanim/'+state['i'].removeprefix('IMAGE_REANIM_')+'.png'
                    pictures[state['i']] = np.array(Image.open(io.BytesIO(z.read(name))).convert('RGBA'))
            tracks.append((t.findtext('name'), states))
    return tracks, pictures, manifest

def sample(states, phase):
    """Tween numeric transforms; hold sprite identity/visibility until its keyframe."""
    i=int(math.floor(phase)) % COUNT
    a=states[min(FIRST+i,len(states)-1)]
    b=states[min(FIRST+(i+1)%COUNT,len(states)-1)]
    f=phase-math.floor(phase)
    out=a.copy()
    # Do not morph or fade between unrelated images or visibility changes.
    if a['i']==b['i'] and (a['f']>=0)==(b['f']>=0):
        for k in NUMERIC:
            delta=b[k]-a[k]
            if k in ('kx','ky'): delta=(delta+180)%360-180
            out[k]=a[k]+f*delta
    return out

class Renderer:
    def __init__(self, tracks, pictures, device):
        self.tracks=tracks; self.device=torch.device(device)
        self.images={}
        for key,a in pictures.items():
            t=torch.tensor(a.astype(np.float32)/255,device=self.device).permute(2,0,1)
            t[:3]*=t[3:4]  # Premultiplied alpha prevents dark transparent-edge halos.
            self.images[key]=t.unsqueeze(0)
        xy=torch.arange(SIZE,device=self.device,dtype=torch.float32)+0.5
        self.yy,self.xx=torch.meshgrid(xy,xy,indexing='ij')

    @torch.inference_mode()
    def render(self, phases):
        n=len(phases)
        canvas=torch.zeros((n,4,SIZE,SIZE),device=self.device)
        for name,states in self.tracks:
            sampled=[sample(states,float(p)) for p in phases]
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

def sync(device):
    if torch.device(device).type=='cuda': torch.cuda.synchronize(device)

def rgba(canvas):
    alpha=canvas[:,3:4]
    rgb=torch.where(alpha>1e-7,canvas[:,:3]/alpha.clamp_min(1e-7),torch.zeros_like(canvas[:,:3]))
    return (torch.cat((rgb,alpha),1).clamp(0,1)*255).round().to(torch.uint8).permute(0,2,3,1).cpu().numpy()

def validate(cpu,gpu):
    # Original keyframes survive resampling. No new paths/art/pose design.
    for _,states in cpu.tracks:
        for i in range(COUNT):
            s=sample(states,i);original=states[min(FIRST+i,len(states)-1)]
            assert all(abs(s[k]-original[k])<1e-7 for k in NUMERIC)
            assert s['i']==original['i'] and s['f']==original['f']
    phases=[0.,0.2,0.5,5.,12.5,24.8]
    a=cpu.render(phases).cpu();b=gpu.render(phases).cpu()
    diff=(a-b).abs()
    report={'max_premultiplied_pixel_error':float(diff.max()),'mean_premultiplied_pixel_error':float(diff.mean()),'integer_keyframes_preserved':True}
    # Allow small floating-point hardware differences, not visible shape changes.
    assert report['max_premultiplied_pixel_error']<0.01,report
    assert report['mean_premultiplied_pixel_error']<0.0001,report
    return report

def benchmark(renderer,phases,repeats=3):
    renderer.render(phases);sync(renderer.device)
    times=[]
    for _ in range(repeats):
        sync(renderer.device);start=time.perf_counter()
        result=renderer.render(phases);sync(renderer.device)
        times.append(time.perf_counter()-start)
        del result
    return {'median_seconds':statistics.median(times),'trials_seconds':times,'frames_per_second':len(phases)/statistics.median(times)}

def export_clips(renderer,out='animation-results'):
    out=Path(out);out.mkdir(exist_ok=True)
    frames_by_rate={};report={}
    for fps in (12,24,60):
        n=round(DURATION*fps);assert abs(n/fps-DURATION)<1e-9
        frames=[];sync(renderer.device);start=time.perf_counter()
        for j in range(0,n,8):
            phases=np.arange(j,min(j+8,n))*SOURCE_FPS/fps
            frames.extend(Image.fromarray(a) for a in rgba(renderer.render(phases)))
        sync(renderer.device)
        boxes=[im.getbbox() for im in frames]
        assert all(boxes),'Empty frame'
        frames_by_rate[fps]=frames
        report[str(fps)]={'frames':n,'duration_seconds':n/fps,'render_and_readback_seconds':time.perf_counter()-start}
    # Common crop for all versions prevents size/anchor changes between previews.
    boxes=[im.getbbox() for fs in frames_by_rate.values() for im in fs]
    bounds=(min(b[0] for b in boxes)-2,min(b[1] for b in boxes)-2,max(b[2] for b in boxes)+2,max(b[3] for b in boxes)+2)
    for fps,frames in frames_by_rate.items():
        frames=[im.crop(bounds) for im in frames]
        # Lossless WebP preview uses millisecond intervals with cumulative rounding.
        durations=[round((i+1)*1000/fps)-round(i*1000/fps) for i in range(len(frames))]
        frames[0].save(out/f'peashooter-{fps}fps.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True)
        w=1<<(frames[0].width-1).bit_length();h=1<<(frames[0].height-1).bit_length()
        columns=8;rows=1<<(math.ceil(len(frames)/columns)-1).bit_length()
        atlas=Image.new('RGBA',(w*columns,h*rows))
        for i,im in enumerate(frames):atlas.alpha_composite(im,((i%columns)*w+(w-im.width)//2,(i//columns)*h+h-im.height))
        atlas.save(out/f'peashooter-{fps}fps-atlas.png')
        report[str(fps)].update({'atlas_size':list(atlas.size),'uncompressed_texture_bytes':atlas.width*atlas.height*4,'common_source_bounds':bounds,'preview_duration_ms':sum(durations)})
    return report
