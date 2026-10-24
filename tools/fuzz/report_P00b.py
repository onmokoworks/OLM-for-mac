#!/usr/bin/env python3
"""Save reproducible P00b audit checkpoints, without claiming pixel conformance."""
from pathlib import Path
import argparse,collections,gzip,io,json,re,shutil,subprocess,sys
import ae_realism_audit as audit
ROOT=audit.ROOT
STATE=ROOT/'orchestra/state/P00b-ae-realism-audit-rerun'
DEST=ROOT/'orchestra/reports/P00b-evidence'
def performance_lines(rows):
 out=['Performance (seconds per render selector; **bold** flags >2 s at 1080p):',
      'Heaviest means the largest observed render time among sampled corpus tuples for that size/depth; a timeout is only a process-time lower bound.', '',
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

def profile_lines():
 out=[];records=[]
 directory=STATE/'profiles'
 if not directory.exists():return out
 target=DEST/'profiles';target.mkdir(exist_ok=True)
 for p in sorted(directory.glob('*.sample.txt')):
  (target/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
 for p in sorted(directory.glob('*.json*')):
  shutil.copy2(p,target/p.name)
  if p.name.startswith('results-'):
   records.extend(json.loads(x) for x in p.open())
 if records:
  out += ['Profile reruns (sampling is separate from the performance table):', 'Each rerun samples a two-second window after a one-second startup delay, then deliberately stops a still-running host. `sampled_then_stopped` is not a crash or a new timeout measurement. Late live profiles additionally identify DirectionalBlur scatter and RadialBlur rotation; sampled leaf counts are not whole-frame time fractions.', '',
          '| Cell | Corpus identity | Rerun status | sample exit | Top sampled leaf functions |',
          '|---|---|---|---|---|']
 for r in records:
  path=STATE/r['profile'];hot=[]
  if path.exists():
   content=path.read_text();marker='Sort by top of stack, same collapsed (when >= 5):'
   if marker in content:
    text=content.split(marker,1)[1].split('Binary Images:',1)[0]
    for line in text.splitlines():
     if '  (in ' in line:
      hot.append(line.strip().split('  (in ',1)[0])
      if len(hot)==3:break
  out.append('| '+r['identity']+' | '+r['case']+' | '+r['status']+' | '+str(r['sample_returncode'])+' | '+'; '.join(hot)+' |')
 return out+['']

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args()
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
 for p in (STATE/'build/bundle-builds.json',STATE/'memory-checks.jsonl',Path.home()/'.cache/olm-emu/P00b/build.json'):
  if p.exists():shutil.copy2(p,DEST/p.name)
 out=['status: done' if args.final else 'status: partial','summary:', '- Fresh Universal Release bundles audited through the SDK host; native AE and pixel exactness are not claimed.' if args.final else '- Fresh-bundle audit checkpoint; matrix/performance work is still in progress.', '- No plugin source, release gate, ledger, MAIN or AEXCompat edits.', '', 'facts:', '- Runtime: Apple M1 Pro, 16 GiB, macOS 15.7.2 (24G325), native arm64 host. Shared-machine single-frame measurements; recorded memory checks are in `P00b-evidence/runtime.json`.', '- Verification: `python3 tools/fuzz/verify_P00b.py` passed all cell-coverage, profile and cache-hash checks; exact output is retained in `P00b-evidence/verification.txt`.', '- Source build HEAD: d1b18b9accaee821543548c1d2d7adf33781dcca (merge of P00).', '- Host and bundle identities, parameter paths/hashes and raw rows are in `P00b-evidence/`.', '- This is an oracle-free SDK host loading real arm64 plugin bundles, not native AE or a pixel-exact comparison.', '- Unlisted status counts are zero; OK nonzero counts refer to active output bytes only.', '- Matrix uses independent host-shape probes, with two additional 4K downsample probes. ROI keeps the full source world; large-layer is a comp-sized viewport, not a compositor. Expansion occurs only when PreRender asks for larger bounds; the situation label alone does not prove expansion.', '- ColorKeep uses three nested T15b anchors sampled with replacement; ColorKey/KiraKira/Smoother2 also sample with replacement (9/8/8 unique paths).', '- Corpus values are reused unchanged, including absolute point coordinates from small original cases; this is not a rescaled artistic preset benchmark.', '- Timeouts are 60-second process wall limits; successful times below are render-selector seconds.', '']
 if args.final:
  index=out.index('facts:')-1
  out[index:index]=[f"- Baseline: {len(allrows['baseline'])} rows, {dict(collections.Counter(r['status'] for r in allrows['baseline']))}.",f"- Matrix: {len(allrows['matrix'])} rows, {dict(collections.Counter(r['status'] for r in allrows['matrix']))}.",'- All 25 slow default/heaviest performance cells have successful stack samples; concrete follow-up tickets are listed below.']
 out += ['- Fresh Universal Release build: `python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/P00b-ae-realism-audit-rerun/build` completed for all ten bundles; products were copied to the registered P00b cache and scratch xcode trees removed.', '- Initial host baseline: 54 OK / 6 ColorKeep iterate host errors; after the host-only rectangle correction: 60 OK. `test_P00b_iterate.cpp` compiled and exited 0.', '- Original default probe: `python3 tools/fuzz/probe_P00b_defaults.py`; 32x24 original Smart succeeds at PF8/PF16/PF32, real Mac PF32 returns 516 (the two lower depths return zero). See the hash-bound JSON.', '- Native process profiling uses `sample PID 2 1 -file PATH`; live profiles and separate default/heaviest-cell reruns are retained. No Instruments, oracle rebuild, plugin source change or pixel oracle in the matrix.', '- All runs use `--jobs 1 --timeout 60`; at most two rendering/oracle processes run concurrently. Interrupted in-flight calls while splitting lanes were discarded and rerun; only completed rows/timeouts are counted.', '']
 for phase,rows in allrows.items():
  out += [f'{phase}: {len(rows)} rows; {dict(collections.Counter(r["status"] for r in rows))}', '']
  if not rows:continue
  groups=collections.defaultdict(list)
  for r in rows:groups[r['plugin'],r['situation']].append(r)
  for plugin in audit.PLUGINS:
   if not any(p==plugin for p,s in groups):continue
   out += ['**'+audit.PLUGINS[plugin]+'**', '', '| Situation | Status counts | Refusal tags | OK nonzero / OK |', '|---|---|---|---|']
   for (p,s),rs in groups.items():
    if p!=plugin:continue
    counts=dict(collections.Counter(r['status'] for r in rs));tags=dict(collections.Counter(t for r in rs for t in r['tags']));ok=[r for r in rs if r['status']=='ok']
    out.append(f'| {s} | {counts} | {tags} | {sum(bool(r["result"].get("nonzero")) for r in ok)}/{len(ok)} |')
   out+=['']
 out += performance_lines(allrows['matrix'])
 out += profile_lines()
 if args.final:
  identities=[(r['plugin'],r['case'],r['situation'],r['depth']) for r in allrows['matrix']]
  assert len(identities)==len(set(identities))==6930
  assert len(allrows['baseline'])==60
  with (DEST/'verification.txt').open('w') as log:
   subprocess.run([sys.executable,str(ROOT/'tools/fuzz/verify_P00b.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
 if (DEST/'interpretation.md').exists():out += [(DEST/'interpretation.md').read_text(),'']
 out += ['inference:', '- Successful return and nonzero output are sanity checks only; no numerical compatibility inference.', '- The classification above distinguishes observed return behavior from original-host and native-AE inference.', '', 'changed_files:', '- `tools/fuzz/ae_realism_audit.py`: 60-second timeout, required 8bpc baseline, additional 4K probes, cache-specific registration, incremental manifests.', '- `tools/emulation/aexcompat_patches/P00-host-realism.{cpp,md}`: SDK iterate clipping and rerun documentation.', '- `tools/fuzz/{report_P00b,profile_P00b,probe_P00b_defaults,verify_P00b}.py`, `test_P00b_iterate.cpp`, this report and `P00b-evidence/`.', '- P00 host/driver and stale evidence were brought in by the required merge.', '', 'verify:', 'Read-only evidence check first; optional full rerun uses a fresh subdirectory and the registered binaries. Timing/timeout boundaries may vary with shared-machine load.', '```sh', 'python3 tools/fuzz/verify_P00b.py', 'mkdir -p orchestra/state/P00b-ae-realism-audit-rerun/recheck', 'export TMPDIR="$PWD/orchestra/state/P00b-ae-realism-audit-rerun/recheck" PYTHONDONTWRITEBYTECODE=1', 'scripts/setup_ae_sdk_links.sh > "$TMPDIR/sdk-links.log" 2>&1', 'clang++ -std=c++17 -O2 -Wno-pragma-pack -IHeaders -IHeaders/SP tools/fuzz/test_P00b_iterate.cpp -o "$TMPDIR/test-iterate" > "$TMPDIR/test-build.log" 2>&1', '"$TMPDIR/test-iterate"', 'python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state "$TMPDIR" > "$TMPDIR/baseline.log" 2>&1', 'python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state "$TMPDIR" > "$TMPDIR/matrix.log" 2>&1', 'python3 tools/fuzz/ae_realism_audit.py --summarize --state "$TMPDIR"', 'git diff --check', '```', 'Expected: integrity OK, iterate regression exit 0, 60 baseline OK rows and 6930 unique matrix rows; compare measured status/tag counts above. The matrix is not an all-success gate. Full reruns take substantial time because every timed-out cell gets 60 seconds.', '', 'next:', '- Finish matrix; profile each slow full-size default/heaviest-corpus performance cell.', '- Classify each remaining refusal against F52c/T15b evidence and current source before proposing fix tickets.', '- Retain ten independent exact ColorKeep corpus tuples in a separate coverage ticket.']
 if args.final and (DEST/'followups.md').exists():
  start=out.index('next:');out=out[:start+1]+[(DEST/'followups.md').read_text()]
 body='\n'.join(out)+'\n'
 for field in ('summary','facts','inference','changed_files','verify','next'):body=body.replace('\n'+field+':\n-', '\n'+field+':\n\n-')
 (ROOT/'orchestra/reports/P00b-ae-realism-audit-rerun.md').write_text(body)
 print({k:len(v) for k,v in allrows.items()})
if __name__=='__main__':main()
