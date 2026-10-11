"""Read and composite the installed game's reanimation tracks, without new art."""
import math
import xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image


class Reanimations:
    def __init__(self, asset):
        self.asset = asset
        self.tracks = {}
        self.images = {}
        self.fps = {}

    def load(self, name):
        if name in self.tracks:
            return self.tracks[name]
        root = ET.fromstring('<root>'+self.asset('reanim/'+name+'.reanim').decode()+'</root>')
        self.fps[name] = float(root.findtext('fps'))
        tracks = []
        for track in root.findall('track'):
            state = dict(x=0., y=0., sx=1., sy=1., kx=0., ky=0., a=1., f=0., i='')
            states = []
            for frame in track.findall('t'):
                for item in frame:
                    if item.tag in state:
                        state[item.tag] = item.text if item.tag == 'i' else float(item.text)
                states.append(state.copy())
            tracks.append((track.findtext('name'), states))
        self.tracks[name] = tracks
        return tracks

    def image(self, path):
        if path not in self.images:
            self.images[path] = Image.open(BytesIO(self.asset(path))).convert('RGBA')
        return self.images[path]

    def frame(self, name, index, overrides=None, replacements=None):
        canvas = Image.new('RGBA', (512, 512))
        for track, states in self.load(name):
            selected = (overrides or {}).get(track, index)
            if selected is None:
                continue
            state = states[min(selected, len(states)-1)]
            if not state['i'] or state['f'] < 0 or state['a'] <= 0:
                continue
            image_id = (replacements or {}).get(state['i'], state['i'])
            path = 'reanim/'+image_id.removeprefix('IMAGE_REANIM_')+'.png'
            picture = self.image(path)
            kx, ky = math.radians(state['kx']), math.radians(state['ky'])
            a, b = math.cos(kx)*state['sx'], -math.sin(ky)*state['sy']
            c, d = math.sin(kx)*state['sx'], math.cos(ky)*state['sy']
            det = a*d-b*c
            if abs(det) < 1e-8:
                continue
            x, y = state['x']+192, state['y']+192
            inverse = (d/det, -b/det, (b*y-d*x)/det, -c/det, a/det, (c*x-a*y)/det)
            layer = picture.transform(canvas.size, Image.Transform.AFFINE, inverse, Image.Resampling.BICUBIC)
            if state['a'] != 1:
                layer.putalpha(layer.getchannel('A').point(lambda v: round(v*state['a'])))
            canvas.alpha_composite(layer)
        assert canvas.getbbox(), (name,index)
        return canvas

    def sequence(self, name, first, last, overrides=None, replacements=None):
        return [self.frame(name, i, overrides(i-first) if callable(overrides) else overrides, replacements)
                for i in range(first,last+1)]
