#!/usr/bin/env python3
"""Summarize retained F36 runs with reviewed command-level classifications."""
import collections
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.emulation.olm_assets import main_assets
SCRATCH=ROOT/'orchestra/state/F36-fixture-runner-worktree-and-triage'
full=json.loads((SCRATCH/'full/results.json').read_text())
recheck=json.loads((SCRATCH/'recheck/results.json').read_text())
rows=recheck+full[len(recheck):]
rows[165]=json.loads((SCRATCH/'followup/165.json').read_text())
C={152:'Size1: 83 output bytes; f3765f38 first refused, ea3a16c5 re-admitted with differences (parent refuses).',
153:'NV0: 83 output bytes; first bad f5a74754, parent 6d0904f8 exact.',
155:'Ratio2/Angle0 9x7: 82 output bytes; f5a74754 parent exact.',
156:'Ratio2/Angle0 32x18: 674 output bytes; f5a74754 parent exact; Zoom cells pass.',
157:'Strength5/NV25: 85 output bytes; f5a74754 parent exact. Also obsolete negative controls.',
158:'OffsetMode3/Offset2/NV25: 4 output bytes; f5a74754 parent exact. Also obsolete negatives.',
159:'Zoom Inner50/NV25: 48 output bytes; b07f5c00 first bad, parent 47b8632a exact.',
165:'Retained full PF8: final output exact; 1,801,691 accum and 95,441 normalized words differ; f5a74754 parent exact.',
167:'PF16 neutral: 2 output bytes; f5a74754 parent exact.',
168:'PF32 neutral: 83 output bytes; f5a74754 parent exact.',
169:'OuterFade50: 102 output bytes at HEAD, 85 at f5a74754; its parent exact.',
170:'OuterFade50/NV25: 50 output bytes; 7a7f53fe first bad, parent bed824a7 exact.',
171:'PF32 Strength5: 9 output bytes; f5a74754 parent exact.',
172:'PF16 Strength5: final output exact; 2,105 accum bytes differ; f5a74754 parent exact.',
174:'Zoom PF16 Strength5: final output exact; 10,373 post-blur bytes differ; b07f5c00 parent exact.',
178:'PF32 OffsetMode3/Offset3: 1 output byte; f5a74754 parent exact.',
179:'PF32 OffsetMode3/Offset4: 41 output bytes; f5a74754 parent exact.',
181:'PF16 OffsetMode3/Offset3: final output exact; 229 accum bytes differ; f5a74754 parent exact.'}
D={20:'Obsolete documentation assertion; no numerical comparison failed.',
42:'Pinned typed-iterate worker missing/drifted; historical worker is not in the supplied cache.',
43:'Validator needs missing issue851 worker (same dependency exposed by command 044); source pins also stale.',
47:'First 2,304 output bytes match expected SHA exactly; first source mutation is now admitted (negatives=0).',
83:'Host adapter exits 38: layer3 err=-1 exact=0 visible=0 pad=1; no raw numerical mismatch established.',
95:'Source-text topology audit still requires old RenderBits dispatch strings; two string predicates false.',
106:'Package exists only in MAIN; tamper tests copy it. Copying MAIN assets is outside the worker authorization. Also stale generator pin.',
126:'Old Mode3 rejection contract: PF8=10 PF16=10 PF32=10; setup fails before numerical comparison.',
127:'Historical AEXCompat worker missing; no new worker was substituted or rebuilt.',
128:'Obsolete exact source-string assertion for RotatedAxisBoxBlur call.',
137:'Source-text audit mode2_typed_truncate is false; other 11 audited predicates true.',
162:'Old unsupported-variation rejection probe exits 1; current broadened admission is not a raw-output comparison.',
163:'Old unproven-geometry rejection probe exits nonzero; assertion is rejection behavior.',
164:'PF32 full-frame production entry refuses (rc=3) before output comparison; numerical result unavailable.',
184:'Host mock exits 10 at first Type3 SmartPreRender/event-order check, before render comparison.',
190:'Historical request package absent in worktree; tamper tests copy directory/ZIP; source provenance pin also stale.'}
# Missing inputs are (d), not (a): (a) is reserved for failures actually fixed.
missing_indices={10,11,30,31,32,33,34,44,45,46,48,49,50,53,54,97,98,101,102,103,104,199}
for i in missing_indices:D[i]='Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins.'
A={37:'SDK Util/AEGP_SuiteHandler.cpp and MissingSuiteError.cpp now resolve; recheck PASS.',
38:'SDK Util source inputs now resolve; recheck PASS.',39:'SDK Util source inputs now resolve; recheck PASS.',
57:'MAIN DirectionalBlur decomp input now resolves; recheck PASS.',58:'MAIN decomp dependency now resolves; recheck PASS.',
68:'SDK Util source inputs now resolve; recheck PASS.'}
bindings=json.loads((ROOT/'orchestra/reports/F36-binding-candidates.json').read_text())
source_map={x['path']:x for x in bindings['source_bindings']}
plugin_files={'blur':'OLMBlur','colorkeep':'ColorKeep','colorkey':'OLMColorKey','directionalblur':'OLMDirectionalBlur','distancegradation':'OLMDistanceGradation','kirakira':'OLMKiraKira','radialblur':'OLMRadialBlur'}
missing={}
classified=[]
for i,(before,row) in enumerate(zip(full,rows)):
    if not before['returncode'] and not row['returncode']:continue
    log=Path(row['log']).read_text() if row.get('log') else row.get('error','')
    category='a' if i in A else 'c' if i in C else 'd' if i in D else 'b'
    note=A.get(i,C.get(i,D.get(i,'')))
    if category=='b':
        plugin=plugin_files.get(row['lane'])
        source=source_map.get(f'mac/{plugin}/{plugin}.cpp',{})
        changed=source.get('last_changed_commit','').split(' ')[0][:8]
        if 'installed' in log.lower() and ('drift' in log.lower() or row['returncode']==126):
            note='Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json.'
        else:
            note=f'Stale source/helper/evidence binding; source last changed {changed or "see inventory"}; migrated helper hashes changed in 24e8b60d.'
        if i==105:note='Analyzer SHA changed d5da42b0… → fb79973f… in 744fc49e; package validation now reaches persisted binding comparison.'
    errors=[line.strip() for line in log.splitlines() if re.match(r'^(AssertionError|RuntimeError|ValueError|FileNotFoundError|FAIL:|ERROR:)',line)]
    evidence=(errors[-1] if errors else log[-500:]).replace(str(ROOT)+'/','')[:500]
    command=[part.replace(str(ROOT)+'/','') for part in row['command'][1:]] if row['command'][0]!='installed-identity-manifest' else row['command']
    item=dict(index=i,lane=row['lane'],command=command,category=category,initial_returncode=before['returncode'],returncode=row['returncode'],note=note,evidence=evidence,log=row.get('log'),skipped=row.get('skipped',0))
    classified.append(item)
    for path in re.findall(r"No such file or directory: (?:PosixPath\()?['\"]([^'\"]+)['\"]",log):
        local=Path(path)
        try:alternate=main_assets()/local.relative_to(ROOT)
        except ValueError:alternate=None
        missing[path]=dict(local_exists=local.exists(),main_alternative=str(alternate) if alternate else None,main_exists=alternate.exists() if alternate else None)
summary=dict(final_counts=dict(collections.Counter(str(r['returncode']) for r in rows)),skipped=sum(r.get('skipped',0) for r in rows),categories=dict(collections.Counter(r['category'] for r in classified)),commands=classified,missing_inputs=missing)
(ROOT/'orchestra/reports/F36-command-triage.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['| ID | Lane | Command (Python prefix omitted) | Class | Evidence / attribution |','|---:|---|---|:---:|---|']
for row in classified:
    command=' '.join(row['command']).replace('|','\\|')
    lines.append(f"| {row['index']:03d} | {row['lane']} | `{command}` | ({row['category']}) | {row['note']} |")
(ROOT/'orchestra/reports/F36-failure-table.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('commands','missing_inputs')}))
