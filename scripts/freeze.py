"""Freeze after verification and before the publication deadline. No overwrite."""
import hashlib
import json
import platform
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from build import DEADLINE
from prepare import ROOT, DATA, dump

def freeze(root=ROOT,now=None):
    now=now or datetime.now(ZoneInfo('Europe/Bratislava'))
    if (root/'data/LOCK.json').exists():raise ValueError('Already locked')
    if now>DEADLINE:raise ValueError('Publication deadline passed')
    file=root/'docs/data/forecast.json'
    forecast=json.loads(file.read_text())
    if datetime.fromisoformat(forecast['cutoff'])>now:raise ValueError('Future cutoff')
    forecast['status']='locked'
    dump(file,forecast)
    paths=[p for p in (root/'data').rglob('*') if p.is_file() and p.suffix!='.zip' and p.name!='LOCK.json']
    paths += list((root/'scripts').glob('*.py')) + list((root/'tests').glob('*.py'))
    paths += [root/'METHODOLOGY.md',root/'README.md']
    paths += [root/'docs'/name for name in ['all.html','index.html','app.js','style.css','METHODOLOGY.md']]
    paths += [p for p in (root/'docs/data').glob('*.json') if p.name not in ['LOCK.json','evaluation.json','actuals.json']]
    paths += [root/'docs/data/forecast.csv']
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    manifest=dict(version=1,locked_at=now.replace(microsecond=0).isoformat(),cutoff=forecast['cutoff'],deadline=DEADLINE.isoformat(),python=platform.python_version(),algorithm='sha256',files=hashes,note='Public commit and forecast-final-v1 tag anchor this manifest. Hashes detect changes; a repository owner can still alter history. No claim of cryptographic immutability.')
    dump(root/'data/LOCK.json',manifest)
    dump(root/'docs/data/LOCK.json',manifest)
    return manifest

if __name__=='__main__':
    manifest=freeze();print('Locked:',manifest['locked_at'],len(manifest['files']),'artifacts')
