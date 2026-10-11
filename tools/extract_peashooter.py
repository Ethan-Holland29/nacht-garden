"""Extract the minimal original Peashooter bundle from a user's local PvZ copy."""
from pathlib import Path
import argparse, hashlib, json, struct, zipfile
import xml.etree.ElementTree as ET

def extract(pak, output):
    data = bytes(c ^ 0xf7 for c in pak.read_bytes())
    if data[:8] != b'\xc0J\xc0\xba\0\0\0\0':
        raise ValueError('Unsupported main.pak format')
    offset, entries = 8, []
    while True:
        flag = data[offset]; offset += 1
        if flag & 128: break
        count = data[offset]; offset += 1
        name = data[offset:offset+count].decode().replace('\\','/')
        offset += count
        size = struct.unpack_from('<I', data, offset)[0]
        offset += 12
        entries.append((name, size))
    assets = {}
    for name, size in entries:
        if offset+size > len(data): raise ValueError('Truncated archive')
        assets[name.lower()] = data[offset:offset+size]
        offset += size
    if offset != len(data): raise ValueError('Unexpected archive tail')
    source = 'reanim/PeaShooterSingle.reanim'
    xml = ET.fromstring('<root>'+assets[source.lower()].decode()+'</root>')
    paths = [source] + sorted({'reanim/'+e.text.removeprefix('IMAGE_REANIM_')+'.png'
                              for e in xml.iter('i') if e.text})
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as bundle:
        for name in paths:
            content = assets[name.lower()]
            bundle.writestr(name, content)
            manifest[name] = hashlib.sha256(content).hexdigest()
        bundle.writestr('provenance.json',json.dumps({
            'source':'User-installed Plants vs Zombies main.pak',
            'files':manifest,
            'purpose':'Private animation interoperability prototype; original art and motion tracks only.'},indent=2))
    return len(paths)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pak',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'cloud/peashooter-source.zip')
    args = parser.parse_args()
    print(f'Extracted {extract(args.pak,args.output)} original files into {args.output}. Keep this bundle private.')
