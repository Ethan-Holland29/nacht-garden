"""Check shareable source, notebook hygiene and Python syntax without game assets.

Examines tracked files plus non-ignored untracked files, so force-added assets
are caught. This is a focused project check, not a general secret scanner.
"""
from pathlib import Path
import ast, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
BLOCKED={'.pak','.iwd','.ff','.iwi','.dds','.png','.jpg','.jpeg','.webp','.gif',
         '.wav','.ogg','.mp3','.mp4','.webm','.exe','.dll','.so','.zip','.reanim',
         '.csc','.xmodel_export','.pem','.key','.p12','.pfx'}
PRIVATE={'work','private','backups','dist','build','accepted-demo-2026-10-10'}

def candidates():
    tracked=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],
                           cwd=ROOT,capture_output=True,check=True).stdout
    return sorted({n.decode() for n in tracked.split(b'\0') if n})

def inspect(name):
    p=ROOT/name
    if p.is_symlink(): return ['symlinks are not allowed in the source export']
    errors=[]
    if p.suffix.lower() in BLOCKED or any(part in PRIVATE for part in p.relative_to(ROOT).parts):
        return ['private/generated game content or binary']
    if p.name.startswith('.env') and p.name!='.env.example':return ['local environment configuration']
    if p.stat().st_size>500_000:errors.append('unexpectedly large source file')
    try:text=p.read_text(encoding='utf8')
    except UnicodeDecodeError:return ['non-text content']
    if re.search(r'/(?:home|Users)/[^/\s]+/|https://jupyter\.anruicloud\.com/instances/',text):
        errors.append('machine-specific home path or private notebook URL')
    if re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',text):
        errors.append('possible credential')
    try:
        if p.suffix=='.py':ast.parse(text,filename=name)
        if p.suffix=='.json':json.loads(text)
        if p.suffix=='.ipynb':
            nb=json.loads(text)
            for i,c in enumerate(nb['cells']):
                if c.get('outputs') or c.get('attachments') or c.get('execution_count') is not None:
                    errors.append(f'cell {i+1} contains output, attachments or execution history')
                if c['cell_type']=='code':ast.parse(''.join(c['source']),filename=f'{name}:cell{i+1}')
    except (SyntaxError,ValueError,KeyError) as e:errors.append(str(e))
    return errors

if __name__=='__main__':
    files=candidates()
    if not files:raise SystemExit('No repository source files found. Initialize Git in this folder first.')
    failures={n:inspect(n) for n in files}
    failures={n:e for n,e in failures.items() if e}
    for name,errors in failures.items():
        for error in errors:print(f'{name}: {error}')
    if failures:sys.exit(1)
    print(f'PASS: {len(files)} text source/evidence files; Python and notebook syntax valid; no notebook outputs, game binaries, home paths or matched credential patterns.')
