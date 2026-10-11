"""Decode owned PvZ audio; no synthesized or replacement sound effects."""
import csv, hashlib, json, subprocess, shutil
from pathlib import Path

def prepare(base):
    native=base.TASK/'work/modtools/raw'
    wave=native/'sound/ng'; wave.mkdir(parents=True,exist_ok=True)
    sources={'throw':.28,'throw2':.28,'splat':.3,'splat2':.3,'splat3':.3,
      'plant':.55,'plant2':.55,'plant_water':.6,'shovel':.5,
      'cherrybomb':.7,'potato_mine':.7,'dirt_rise':.35,
      'bigchomp':.6,'gulp':.55,'chomp':.25,'chomp2':.25,
      'squash_hmm':.55,'squash_hmm2':.55,'floop':.65,
      'zombiesplash':.65,'points':.25,'seedlift':.3}
    headers=(base.TASK/'work/reference/sumpf-sounds.csv').read_text().splitlines()[0].split(',')
    report={}
    with (native/'soundaliases/ng_pvz.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(headers)
        for name,volume in sources.items():
            data=base.asset('sounds/'+name+'.ogg')
            ogg=base.TASK/'work'/('pvz-'+name+'.ogg');ogg.write_bytes(data)
            dest=wave/(name+'.wav')
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(ogg),'-ar','44100','-ac','1','-c:a','pcm_s16le',str(dest)],check=True)
            stream=base.RAW/'sound/ng'/(name+'.wav');stream.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dest,stream)
            values=dict(name='ng_'+name,file='ng\\'+name+'.wav',limit_count='3',limit_type='priority',vol_min=str(volume),vol_max=str(volume),pitch_min='1',pitch_max='1',dist_min='80',dist_max='850',volumefalloffcurve='curve2',bus='full_vol',spatialized='3d',type='streamed',loadspec='all_sp')
            writer.writerow([values.get(h,'') for h in headers])
            report[name]={'source':'sounds/'+name+'.ogg','source_sha256':hashlib.sha256(data).hexdigest(),'conversion':'44100 Hz mono PCM16','volume':volume,'simultaneous_limit':3}
    (base.ROOT/'audio-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    return ['ng_'+n for n in sources]
