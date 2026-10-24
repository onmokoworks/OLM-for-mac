#!/usr/bin/env python3
"""Verify the retained A01 load evidence and installed binary identities; no AE launch."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'orchestra/reports/A01-evidence'
manifest=json.loads((EVIDENCE/'bundles.json').read_text())
probe=json.loads((EVIDENCE/'probe-2026.json').read_text())
vmmap=(EVIDENCE/'vmmap-2026-plugins.txt').read_text()
assert probe['phase']=='complete'
assert len(manifest['bundles'])==len(probe['rows'])==10
for record in manifest['bundles']:
    name=record['plugin']
    row=next(r for r in probe['rows'] if r['plugin']==name)
    assert row['registered'] and row['applied'], name
    assert f'/OLM-smoke/{name}.plugin/Contents/MacOS/{name}' in vmmap, name
    for folder in record['installed']:
        binary=Path(folder)/'Contents/MacOS'/name
        assert hashlib.sha256(binary.read_bytes()).hexdigest()==record['sha256'], str(binary)
        arch=subprocess.check_output(['lipo','-archs',str(binary)],text=True).split()
        assert set(arch)=={'arm64','x86_64'}, (name,arch)
    print(name, 'load/apply + mapping + two installed hashes: OK')
print('10/10 load/apply; 20/20 installed hashes. No render/exactness claim.')
