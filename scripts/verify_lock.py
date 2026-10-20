"""Check the original public snapshot without modifying it."""
import hashlib
import json
from pathlib import Path
from prepare import ROOT

def verify(root=ROOT):
    manifest=json.loads((root/'data/LOCK.json').read_text())
    for relative,expected in manifest['files'].items():
        file=root/relative
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=expected:
            raise ValueError('Locked artifact changed: '+relative)
    return manifest

if __name__=='__main__':
    manifest=verify()
    print('Verified',len(manifest['files']),'locked artifacts; locked at',manifest['locked_at'])
