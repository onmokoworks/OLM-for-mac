#!/usr/bin/env python3
"""Save reproducible P00b audit checkpoints, without claiming pixel conformance."""
from pathlib import Path
import collections,gzip,json,shutil
import ae_realism_audit as audit
ROOT=audit.ROOT
STATE=ROOT/'orchestra/state/P00b-ae-realism-audit-rerun'
DEST=ROOT/'orchestra/reports/P00b-evidence'
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
      try: rows.append(json.loads(line))
      except json.JSONDecodeError: break
   with gzip.open(DEST/(phase+'.jsonl.gz'),'wt') as f:
    for row in rows:f.write(json.dumps(row,sort_keys=True)+'\n')
  allrows[phase]=rows
  m=STATE/(phase+'-manifest.json')
  if m.exists():
   data=json.loads(m.read_text())
   if phase=='matrix' and (STATE/'heavy/matrix-manifest.json').exists():
    other=json.loads((STATE/'heavy/matrix-manifest.json').read_text())
    for key in ('bundles','samples'):data[key].update(other[key])
    data['memory']+=other['memory']
   data['counts']=dict(collections.Counter(r['status'] for r in rows))
   (DEST/m.name).write_text(json.dumps(data,indent=2)+'\n')
 for p in (STATE/'build/bundle-builds.json',Path.home()/'.cache/olm-emu/P00b/build.json'):
  if p.exists():shutil.copy2(p,DEST/p.name)
 out=['status: partial','summary:', '- Fresh-bundle audit checkpoint; matrix/performance work is still in progress.', '- No plugin source, release gate, ledger, MAIN or AEXCompat edits.', '', 'facts:', '- Source build HEAD: d1b18b9accaee821543548c1d2d7adf33781dcca (merge of P00).', '- Host and bundle identities, parameter paths/hashes and raw rows are in `P00b-evidence/`.', '- This is an oracle-free SDK host loading real arm64 plugin bundles, not native AE or a pixel-exact comparison.', '- Matrix uses independent host-shape probes, with two additional 4K downsample probes.', '- ColorKeep has zero eligible corpus files. ColorKey/KiraKira/Smoother2 sample with replacement (9/8/8 unique paths).', '- Timeouts are 60-second process wall limits; successful times below are render-selector seconds.', '']
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
 out += ['inference:', '- Successful return and nonzero output are sanity checks only; no numerical compatibility inference.', '- Refusal classification and hotspot attribution remain pending until the matrix completes.', '', 'changed_files:', '- `tools/fuzz/ae_realism_audit.py`: 60-second timeout, required 8bpc baseline, additional 4K probes, cache-specific registration, incremental manifests.', '- `tools/fuzz/report_P00b.py`, this report and `P00b-evidence/`.', '- P00 host/driver and stale evidence were brought in by the required merge.', '', 'verify:', '```sh', 'python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/P00b-ae-realism-audit-rerun/build', 'python3 tools/fuzz/ae_realism_audit.py --build-host --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun', 'python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun', 'python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun', 'python3 tools/fuzz/report_P00b.py', 'git diff --check', '```', 'Expected complete coverage: 60 baseline rows and 6300 matrix rows. Checkpoint counts above are measured, not a completion claim. Build products must be installed under P00b/xcode before running the host.', '', 'next:', '- Finish matrix; profile each slow full-size default/heaviest-corpus performance cell.', '- Classify each remaining refusal against F52c/T15b evidence and current source before proposing fix tickets.', '- Retain ten independent exact ColorKeep corpus tuples in a separate coverage ticket.']
 (ROOT/'orchestra/reports/P00b-ae-realism-audit-rerun.md').write_text('\n'.join(out)+'\n')
 print({k:len(v) for k,v in allrows.items()})
if __name__=='__main__':main()
