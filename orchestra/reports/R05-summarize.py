#!/usr/bin/env python3
"""Retain every failed gate record; incomplete evidence never becomes PASS."""
import collections,hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R05-regenerate-stale-bindings'
OUT=ROOT/'orchestra/reports'
read=lambda p:json.loads(p.read_text())
fixtures=read(S/'fixtures/results.json');generic=read(S/'generic.json');release=read(S/'release.json')
f40={r['index']:r for r in read(OUT/'F40-adjudication.json')['commands']}
r03={r['key']:r for r in read(OUT/'R03-results.json')['results']}
radial={r['command_index']:r for r in read(S/'radial/results.json')}
installed_ids={35,36,40,65,66,91,92,99,100,119,120,134,135,183,197,198,200,201,202,203}
focused=read(S/'focused.json')
rows=[]
for index,r in enumerate(fixtures):
    row=dict(index=index,**r)
    if r['returncode']==0: disposition='pass'
    elif index==4 and any(v['name']=='matrix' and v['exit']==0 for v in focused): disposition='source binding refreshed after full gate; strict focused audit now passes (historical gate return code retained)'
    elif r['returncode']==126 or index in installed_ids: disposition='requires real AE/Windows: installed identity/build receipt and host evidence; not pass'
    elif index in radial: disposition='unresolved intermediate-plane binding: F46 twice/current Mac final exact for first witness only; not pass'
    elif f'fixture-{index:03}' in r03:
        prior=r03[f'fixture-{index:03}']
        disposition='unresolved '+prior['outcome']+'; original R03 diagnostic retained; not pass'
        row['R03_diagnostic']=prior.get('note')
    elif index in f40:
        disposition='unresolved F40 evidence/input/contract; not pass'
        row['F40_note']=f40[index]['note']
    else: disposition='unresolved gate finding; not pass'
    row['disposition']=disposition
    rows.append(row)
for row in generic.get('entries',[]):
    if row['status']=='FAIL':
        row['disposition']=('requires real AE/Windows to renew the Windows-owner claim; not pass' if 'windows_owner' in row['test'] else 'unresolved runtime/contract or documentation/performance binding; not pass')
result=dict(status='blocked',full_gate_scope='Release/fixtures completed before the one Blur metadata refresh; focused audit verifies that refresh. Generic entries are the final clean rerun.',focused=focused,before_boundary=read(S/'before-boundary.json'),after_boundary=read(S/'after-boundary.json'),fixture_counts=dict(collections.Counter(str(r['returncode']) for r in fixtures)),fixture_records=len(fixtures),
            skipped_fixture_commands=sum(r.get('skipped',0) for r in fixtures),generic_counts=generic.get('counts'),
            release_status=release['status'],releasable=release['releasable'],windows_boundary=release['windows_ae_release_boundary'],
            parameter_ui=release['parameter_ui_registration'],installed=release['universal_installs'],host_smoke=release['mac_ae_representative']['counts'],
            fixtures=rows,generic_entries=generic.get('entries'),radial=read(S/'radial/results.json'),
            blur=read(S/'blur/verification.json'),trace_capability=read(S/'trace-capability.json'),commands=read(S/'commands.json'))
(OUT/'R05-results.json').write_text(json.dumps(result,indent=2)+'\n')
paths=[]
for p in S.rglob('*'):
    if not p.is_file() or p.suffix not in ('.json','.log','.md'):continue
    rel=p.relative_to(S)
    if 'scratch' in rel.parts or 'build' in rel.parts or 'gate-input-backup' in rel.parts:continue
    paths.append(p)
archive=OUT/'R05-evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted(paths):tar.add(p,arcname=str(p.relative_to(S)),recursive=False)
with archive.open('rb') as f:archive_sha=hashlib.file_digest(f,'sha256').hexdigest()
manifest=dict(archive=archive.name,sha256=archive_sha,files=[])
for p in sorted(paths):
    with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    manifest['files'].append(dict(path=str(p.relative_to(S)),sha256=digest,bytes=p.stat().st_size))
(OUT/'R05-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('fixture_counts','fixture_records','skipped_fixture_commands','generic_counts','release_status','releasable')}))
