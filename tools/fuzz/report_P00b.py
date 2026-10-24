#!/usr/bin/env python3
"""Save reproducible P00b audit checkpoints, without claiming pixel conformance."""
from pathlib import Path
import collections,gzip,io,json,shutil
import ae_realism_audit as audit
ROOT=audit.ROOT
STATE=ROOT/'orchestra/state/P00b-ae-realism-audit-rerun'
DEST=ROOT/'orchestra/reports/P00b-evidence'
def performance_lines(rows):
 out=['Performance (seconds per render selector; **bold** flags >2 s at 1080p):',
      'Heaviest means the largest observed render time among sampled corpus tuples for that size/depth; a timeout is only a process-time lower bound.',
      '| Plugin | bpc | Default 1080p | Default 4K | Heaviest 1080p (case) | Heaviest 4K (case) |',
      '|---|---|---|---|---|---|']
 for plugin in audit.PLUGINS:
  for depth in (8,16,32):
   values=[]
   for category,situation in [('default','full'),('default','4k'),('heaviest','full'),('heaviest','4k')]:
    cells=[r for r in rows if (r['plugin'],r['depth'],r['situation'])==(plugin,depth,situation)]
    candidates=[r for r in cells if r['case']=='default'] if category=='default' else [r for r in cells if r['case']!='default' and r['status'] in ('ok','timeout')]
    if not candidates:values.append('unavailable');continue
    r=max(candidates,key=lambda x:60 if x['status']=='timeout' else x['result'].get('render_seconds',0))
    value=f"{r['result']['render_seconds']:.3f}" if r['status']=='ok' else '>=60 wall (timeout)' if r['status']=='timeout' else r['status']
    if situation=='full' and (r['status']=='timeout' or r['result'].get('render_seconds',0)>2):value='**'+value+'**'
    if category=='heaviest':value+=' ('+r['case']+')'
    values.append(value)
   out.append('| '+plugin+' | '+str(depth)+' | '+' | '.join(values)+' |')
 return out+['']

def main():
 DEST.mkdir(parents=True,exist_ok=True)
 allrows={}
 for phase in ('baseline','matrix'):
  p=STATE/(phase+'.jsonl')
  rows=[]
  if p.exists():
   with p.open() as f:
    for line in f:
     try: rows.append(json.loads(line))
     except json.JSONDecodeError: break # a live checkpoint may catch the last write
   if phase=='matrix' and (STATE/'heavy/matrix.jsonl').exists():
    with (STATE/'heavy/matrix.jsonl').open() as f:
     for line in f:
      try:
       row=json.loads(line)
       if row['plugin']!='radialblur' or not (STATE/'radial/matrix.jsonl').exists():rows.append(row)
      except json.JSONDecodeError: break
   if phase=='matrix' and (STATE/'radial/matrix.jsonl').exists():
    with (STATE/'radial/matrix.jsonl').open() as f:
     for line in f:
      try:
       row=json.loads(line)
       rows.append(row)
      except json.JSONDecodeError:break
   if phase=='matrix' and (STATE/'radial-tail/matrix.jsonl').exists():
    with (STATE/'radial-tail/matrix.jsonl').open() as f:
     for line in f:
      try:rows.append(json.loads(line))
      except json.JSONDecodeError:break
   with (DEST/(phase+'.jsonl.gz')).open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed, io.TextIOWrapper(compressed) as f:
    for row in rows:f.write(json.dumps(row,sort_keys=True)+'\n')
  allrows[phase]=rows
  m=STATE/(phase+'-manifest.json')
  if m.exists():
   data=json.loads(m.read_text())
   if phase=='matrix' and (STATE/'heavy/matrix-manifest.json').exists():
    other=json.loads((STATE/'heavy/matrix-manifest.json').read_text())
    for key in ('bundles','samples'):data[key].update(other[key])
    data['memory']+=other['memory']
   if phase=='matrix' and (STATE/'radial/matrix-manifest.json').exists():
    other=json.loads((STATE/'radial/matrix-manifest.json').read_text())
    for key in ('bundles','samples'):data[key].update(other[key])
    data['memory']+=other['memory']
   if phase=='matrix' and (STATE/'radial-tail/matrix-manifest.json').exists():
    other=json.loads((STATE/'radial-tail/matrix-manifest.json').read_text())
    data['memory']+=other['memory']
   data['counts']=dict(collections.Counter(r['status'] for r in rows))
   (DEST/m.name).write_text(json.dumps(data,indent=2)+'\n')
 for p in (STATE/'build/bundle-builds.json',Path.home()/'.cache/olm-emu/P00b/build.json'):
  if p.exists():shutil.copy2(p,DEST/p.name)
 out=['status: partial','summary:', '- Fresh-bundle audit checkpoint; matrix/performance work is still in progress.', '- No plugin source, release gate, ledger, MAIN or AEXCompat edits.', '', 'facts:', '- Source build HEAD: d1b18b9accaee821543548c1d2d7adf33781dcca (merge of P00).', '- Host and bundle identities, parameter paths/hashes and raw rows are in `P00b-evidence/`.', '- This is an oracle-free SDK host loading real arm64 plugin bundles, not native AE or a pixel-exact comparison.', '- Matrix uses independent host-shape probes, with two additional 4K downsample probes.', '- ColorKeep uses three nested T15b anchors sampled with replacement; ColorKey/KiraKira/Smoother2 also sample with replacement (9/8/8 unique paths).', '- Timeouts are 60-second process wall limits; successful times below are render-selector seconds.', '']
 for phase,rows in allrows.items():
  out += [f'{phase}: {len(rows)} rows; {dict(collections.Counter(r["status"] for r in rows))}', '']
  if not rows:continue
  out += ['| Plugin / situation | Status counts | Refusal tags | OK nonzero / OK |', '|---|---|---|---|']
  groups=collections.defaultdict(list)
  for r in rows:groups[r['plugin'],r['situation']].append(r)
  for (p,s),rs in groups.items():
   counts=dict(collections.Counter(r['status'] for r in rs));tags=dict(collections.Counter(t for r in rs for t in r['tags']));ok=[r for r in rs if r['status']=='ok']
   out.append(f'| {p} / {s} | {counts} | {tags} | {sum(bool(r["result"].get("nonzero")) for r in ok)}/{len(ok)} |')
  out+=['']
 out += performance_lines(allrows['matrix'])
 if (DEST/'interpretation.md').exists():out += [(DEST/'interpretation.md').read_text(),'']
 out += ['inference:', '- Successful return and nonzero output are sanity checks only; no numerical compatibility inference.', '- Refusal classification and hotspot attribution remain pending until the matrix completes.', '', 'changed_files:', '- `tools/fuzz/ae_realism_audit.py`: 60-second timeout, required 8bpc baseline, additional 4K probes, cache-specific registration, incremental manifests.', '- `tools/fuzz/report_P00b.py`, this report and `P00b-evidence/`.', '- P00 host/driver and stale evidence were brought in by the required merge.', '', 'verify:', '```sh', 'python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/P00b-ae-realism-audit-rerun/build', 'python3 tools/fuzz/ae_realism_audit.py --build-host --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun', 'python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun', 'python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun', 'python3 tools/fuzz/report_P00b.py', 'git diff --check', '```', 'Expected complete coverage: 60 baseline rows and 6930 matrix rows. Checkpoint counts above are measured, not a completion claim. Build products must be installed under P00b/xcode before running the host.', '', 'next:', '- Finish matrix; profile each slow full-size default/heaviest-corpus performance cell.', '- Classify each remaining refusal against F52c/T15b evidence and current source before proposing fix tickets.', '- Retain ten independent exact ColorKeep corpus tuples in a separate coverage ticket.']
 (ROOT/'orchestra/reports/P00b-ae-realism-audit-rerun.md').write_text('\n'.join(out)+'\n')
 print({k:len(v) for k,v in allrows.items()})
if __name__=='__main__':main()
