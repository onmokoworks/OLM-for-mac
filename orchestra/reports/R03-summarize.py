#!/usr/bin/env python3
"""Package measured R03 outcomes; do not treat post-link failures as passes."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R03-harness-ucrt-link'
OUT=ROOT/'orchestra/reports'
rows=json.loads((S/'results.json').read_text())
assert len(rows)==98
numeric={38,39,41,42,43,44,45,51,53,54,55,56,57,58,60,64,65,67}
binding={34,69,93}
notes={
4:'Probe exit 3; captured SOURCE_BOUND_ATOMIC pass=0 positives=0 negatives=0. First 2304-byte output matches retained SHA-256 2b05dfeed6c1385d4818cd727aabc6931581b6d39ce22f84a13461b91a33e740.',
5:'Cleanup probe rc=134: budget err=-3 alloc=1 output=1 layer=2 out=1 checkin=1 pc=21 pi=21.',
21:'Adapter exit 38: layer3 err=-1 exact=0 visible=0 pad=1.',
31:'Probe exit 1: PF8=10 PF16=10 PF32=10 (fail-close expectations).',
34:'Installed Kira executable hash 69e87ce32570ebf299d8a3e94b707321b607ac51de42324e6a0444f490714c4d != d4c9b587d41797259de8627e2d3d5bcf7a376f12fa3c8b99dcd820e0b6d80ae3.',
43:'Also fails rejection controls strength5_nv50 and strength6_nv25.',
44:'Also fails rejection controls offset5_nv25 and offset2_nv50.',
45:'Also fails rejection control inner50_noise50.',
48:'Unsupported-variation probe exits 1.',
49:'Unproven-geometry executable returns nonzero; unchanged r.returncode==0 assertion fails.',
50:'Render probe exits 3: OLMRadialBlurTestRenderWorld returned nonzero before output comparison.',
51:'Internal arrays differ; final PF8 output remains exact: cb39306e0e340bfa121e5ea55c9e1b43f87696237b4d6c855a47ce09dba188fc.',
58:'Internal arrays differ; retained final output matches.',
60:'Internal post-blur plane differs; retained final output matches.',
67:'Internal arrays differ; retained final output matches.',
69:'All compared pixels/planes and fixture hashes match; installed Radial hash 0ed4a2f573c1e48471309b3a35209bbefda90d977aee8ddca3b216a94f7014c9 != 9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5.',
70:'Host mock exits 10 (SmartPreRender/event contract).',
78:'EffectMain probe rc=10; FAIL code=1568 line=704; FAIL code=10 line=808.',
80:'Cleanup probe rc=134: budget err=-3 alloc=1 output=1 layer=2 out=1 checkin=1 pc=21 pi=21.',
81:'Both normal and sanitizer probes exit 75: pf32_blurred_budget_rejects expectation.',
85:'Three failures: MODE3_UI_REJECT length=0 reports ok=0 at depths 8/16/32; length=301 reports ok=1.',
86:'Baseline probe exit 38.',
93:'EvidenceBindingError: invocation executable prefix mismatch; command mismatch OLMDistanceGradation/uhd. Both compiler invocations succeed.',
}
for index,r in enumerate(rows):
    r['index']=index
    r['outcome']='pass' if r['exit']==0 else 'numeric failure' if index in numeric else 'stale binding' if index in binding else 'runtime/contract failure'
    r['note']=notes.get(index,'')
    events=[json.loads(line) for line in (S/f'{index:03d}-links.jsonl').read_text().splitlines()]
    assert events and all(e['exit']==0 and any(str(a).endswith('libucrtmath.a') for a in e['command']) for e in events)
    r['first_differences']=[]
    for p in sorted((S/'diagnostics'/str(index)).glob('*.json')):
        data=json.loads(p.read_text())
        for c in data.get('comparisons',[]):
            if c['first_byte'] is not None:
                r['first_differences'].append(dict(c,evidence=str(p.relative_to(S))))
    for p in sorted((S/'generated'/str(index)).rglob('*.json')):
        data=json.loads(p.read_text())
        for plane,values in data.get('differences',{}).items():
            if not isinstance(values,dict):continue
            first=values.get('first_byte',values.get('first_different'))
            if first is not None:
                r['first_differences'].append(dict(plane=plane,first=first,
                    unit='byte' if 'first_byte' in values else 'value index',
                    count=values.get('different_bytes',values.get('different_values')),
                    evidence=str(p.relative_to(S))))
    if index in numeric: assert r['first_differences'], (index,'missing first difference')
summary=dict(baseline='f40209b85623dfeef32b650fa1d004f5c857ef99',
             class_a_counts=dict(collections.Counter(r['outcome'] for r in rows[:93])),
             all_counts=dict(collections.Counter(r['outcome'] for r in rows)),
             class_a_links=sum(r['links'] for r in rows[:93]),all_links=sum(r['links'] for r in rows),results=rows)
(OUT/'R03-results.json').write_text(json.dumps(summary,indent=2)+'\n')
files=[]
for p in S.rglob('*'):
    if p.is_file() and p.name != 'summary.log' and (p.suffix in ('.log','.jsonl') or p.name in ('results.json','initial-results.json') or 'generated' in p.parts or 'diagnostics' in p.parts):
        files.append(p)
archive=OUT/'R03-evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted(files):tar.add(p,arcname=str(p.relative_to(S)),recursive=False)
manifest=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
              files=[dict(path=str(p.relative_to(S)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)])
(OUT/'R03-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
changed=subprocess.check_output(['git','diff','--name-only','f40209b85623dfeef32b650fa1d004f5c857ef99'],cwd=ROOT,text=True)
(OUT/'R03-changed-files.txt').write_text(changed)
print(json.dumps({k:v for k,v in summary.items() if k!='results'}))
print('Evidence',len(files),'files;',archive.stat().st_size,'bytes; sha256',manifest['sha256'])
