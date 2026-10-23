#!/usr/bin/env python3
"""Render the F40 review proposal; never change executable assertions."""
import collections,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'orchestra/reports';S=ROOT/'orchestra/state/F40-stale-bindings-adjudication'
j=json.loads((OUT/'F40-adjudication.json').read_text());rows=j['commands']
plugins={'blur':'OLMBlur','colorkeep':'ColorKeep','colorkey':'OLMColorKey','directionalblur':'OLMDirectionalBlur','distancegradation':'OLMDistanceGradation','kirakira':'OLMKiraKira','radialblur':'OLMRadialBlur','smoother':'OLMSmoother','smoother2':'OLMSmoother2','toondilate':'OLMToonDilate'}
installed_ids={35,36,40,65,66,91,92,99,100,119,120,134,135,183,197,198,200,201,202,203}
missing_ids={10,11,30,31,32,33,34,42,43,44,45,46,48,49,50,53,54,97,98,101,102,103,104,112,127,199}
contract_ids={20,47,95,126,128,137,162,163}
host_ids={83,164,184}
# Retirement here is limited to explicitly superseded old rejection assertions, not whole numerical suites.
retire={126:('9fd48fe8 / 0790258a','refs/conformance/olmkirakira_mode3_32x18_public_closure_20260814.json','Retire only old blanket Mode3 rejection; retain exact-output closure.'),162:('1e3be713','docs/COMPATIBILITY_ANALYSIS_PLAN_JA.md','Retire only rejection of now-legal Quality/variation cells after matching each negative to the current control contract; retain invalid-input rejection.'),163:('C33','orchestra/reports/C33-radial-smart-r5.md','Retire only the now-admitted geometry/center negatives overlapping C33; retain other safety negatives.')}
unique={};catalog=[]
for r in rows:
 r['binding_ids']=[]
 for b in r['mapped_stale_bindings']:
  k=(b['path'],b['bound'],b['current'])
  if k not in unique:
   unique[k]='B%03d'%(len(unique)+1);catalog.append((unique[k],b))
  r['binding_ids'].append(unique[k])
def esc(s):return str(s).replace('|','\\|').replace('\n',' ') 
def commit(c):
 if not c:return 'unknown'
 m=c.get('reviewed_merge');return '`'+c['commit']+'` ('+esc(c['subject'])+'); '+('reviewed merge `'+m['commit']+'` '+esc(m['subject']) if m else 'no reviewed orch merge on selected first-parent history')
lines=['status: blocked','summary:','- Inventoried all 72 F36 class-(b) and 38 class-(d) command entries at base `'+j['base']+'`.','- Proposed changes only; one deterministic two-helper metadata refresh applied after two identical original-AEX executions.','- Installed build provenance, source pins absent from selected path history and absent historical assets prevent complete per-item causal adjudication.','- No assertion, expected byte file, release gate, ledger, plugin implementation, installed binary or MAIN asset changed.','','facts:','','The F36 categories are historical command-level results, not freshly rerun outcomes. The full fixture suite was not rerun. `F40-adjudication.json` retains each command, F36 evidence/note, inspected consumer files, binding occurrence files, every subsequent file change and reviewed merge attribution. Static dependency discovery is deliberately labeled: it can include secondary pins and is not proof that every discovered hash is the first assertion.','','Commands actually run:','','- `python3 -B orchestra/reports/F40-adjudicate.py`: read tracked files at the fixed base, hash present files and installed binaries, and run `git log --raw --no-abbrev BASE -- FILE` plus `git cat-file blob BLOB` for historical SHA-256.','- `git log --first-parent --merges --reverse` plus `git rev-list MERGE^1..MERGE^2`: map changes to the first introducing orchestration merge. Merge subjects naming orchestration tickets are the recorded reviewed-merge evidence. A null mapping means no such introducing merge found, not an assertion that nobody reviewed it.','- `F40-regenerate-owner.py --apply` with MAIN emulation Python: two original-AEX live generations identical; 2 rows; every non-identity field unchanged; output JSON SHA-256 `2077fd254c1c31c4ab8456f9c6c1ac513c1133346402f1c5c0d77be3d0daab7c`.','- `tests/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py -v`: 4 tests passed, including authority and row tamper checks.','','Proposal semantics: **repin** means conditional proposal for review, not authorization to replace history with a present-day PASS. An unavailable new value stays `unavailable`, with recovery required. **retire** below targets only the specified superseded predicate; numerical and safety assertions remain. Rows without a justified replacement are blocked, not falsely counted as adjudicated. A source last-change commit does not establish the first failing boundary. Historical installed observations do not prove a rebuild from current sources.','','| Group | Commands |','|---|---:|']
groups=collections.Counter()
for r in rows:
 i=r['index'];group='installed identity / build provenance' if i in installed_ids else 'historical asset missing' if i in missing_ids else 'copy-dependent package test' if i in {106,190} else 'host refusal before byte comparison' if i in host_ids else 'documentation / topology / rejection contract' if i in contract_ids else 'source / helper / evidence binding'
 r['group']=group;groups[group]+=1
for k,v in groups.items():lines.append(f'| {k} | {v} |')
lines+=['','Per-command proposal table (110 rows; B references resolve to full old/new hashes and commit evidence below):','','| ID / F36 class | Command | Group; proposal | Bound → current / evidence |','|---|---|---|---|']
for r in rows:
 i=r['index'];bs=', '.join(r['binding_ids']) or 'No mapped reachable historical hash; unresolved'
 if i in installed_ids:bs+='; I-'+plugins[r['lane']]
 if i in {16,17}:proposal='Repin APPLIED: only regenerated report helper identities; 2 identical runs, 4 tests pass.'
 elif i in retire:
  t,p,n=retire[i];proposal=f'Retire proposal: {n} Superseding {t}, `{p}`; per-negative overlap still requires review.'
 elif i in missing_ids:proposal='Repin BLOCKED: restore exact historical asset/worker first; no equivalent replacement established. Do not retire a numerical test merely because its asset is missing.'
 elif i in {106,190}:proposal='Repin BLOCKED: package tamper setup requires a writable package; MAIN-copy prohibition applies. Keep original generator/provenance assertions.'
 elif i in host_ids:proposal='Repin BLOCKED: no new successful host contract value. Investigate refusal; no proven superseding fixture. '+('C36 records unresolved allocator-dependent refusals.' if i==83 else '')
 elif i in contract_ids:proposal='Repin BLOCKED: update predicate only after equivalent current behavior proof; '+r['note']
 elif i in installed_ids:proposal='Repin proposal to observed installed SHA in I table, conditional on matching build/install receipt and live closure; build commit UNKNOWN.'
 else:proposal='Repin proposal to B current values after live closure; preserve all AEX outputs and negatives. '+('Source pin absent from file history: exact old→new attribution BLOCKED.' if any(b.get('unresolved') for b in r['mapped_stale_bindings']) else 'Not applied; determinism/behavior not established for this generator.')
 evidence=r['evidence']
 if i in missing_ids or i in host_ids or i in contract_ids or i in {106,190}:bs+='; F36: '+evidence[:350]
 lines.append(f"| {i:03d} / {r['category']} | `{esc(' '.join(r['command']))}` | {esc(r['group']+'; '+proposal)} | {esc(bs)} |")
lines+=['','Binding catalogue. Current values are proposals, not accepted identities. Full intervening history (including merges for each commit) is in the JSON; this table gives first known change after the pinned version and last change. An literal pin absent from selected path history has no invented boundary.','','| Binding | File | Bound SHA-256 → current SHA-256 | File-history evidence / reviewed merge |','|---|---|---|---|']
for bid,b in catalog:
 changes=b['changes_since_bound']
 if changes:e='First change after most recent matching blob: '+commit(changes[-1])+'; last change: '+commit(changes[0])
 else:e=b.get('unresolved','History boundary unresolved')+' Last current change: '+commit(b.get('current_last_change'))
 lines.append(f"| {bid} | `{b['path']}` | `{b['bound']}` → `{b['current']}` | {e} |")
lines+=['','Installed identity catalogue: actual installed artifacts were hashed read-only. No git commit changes these untracked files; all exact build commits remain unknown. The listed receipt commits only recorded the observed hashes.','','| ID | Bound → current SHA-256 | Receipt / reviewed merge |','|---|---|---|']
for x in j['installed']:
 es=[]
 for e in x['evidence']:
  es.append('`'+e['path']+'`: `'+e['introduced_by']+'`; '+('reviewed merge `'+e['reviewed_merge']['commit']+'`' if e['reviewed_merge'] else 'no introducing reviewed merge found'))
 lines.append('| I-'+x['plugin']+' | `'+x['pinned']+'` → `'+str(x['current'])+'` | '+'; '.join(es)+' |')
lines+=['','Missing-input inventory (F36 names, existence rechecked in F40; no assets copied):','','| Bound path | Current worktree / MAIN alternative |','|---|---|']
f36=json.loads((OUT/'F36-command-triage.json').read_text())
main=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
for p,v in f36['missing_inputs'].items():
 oldroot='/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/F36-fixture-runner-worktree-and-triage/'
 q=ROOT/p[len(oldroot):] if p.startswith(oldroot) else Path(p)
 if not q.is_absolute():q=ROOT/q
 alt=Path(v['main_alternative']) if v.get('main_alternative') else None
 lines.append(f'| `{esc(p)}` | local exists={q.exists()}; MAIN alternative `{esc(str(alt))}` exists={alt.exists() if alt else "n/a"} |')
lines+=['','inference:','','The fixed runner mixes historical evidence validation with current-install/current-source acceptance. Blanket repinning would silently promote obsolete contracts. F36’s 72 stale entries are not 72 proven safe metadata updates: several old source values were not found in the selected git-log file history, and source/binary observations alone cannot prove live acceptance. The applied owner report is narrower: the same original-AEX computations and all non-identity fields reproduced twice.','','This ticket is blocked rather than done because conditional proposals for unavailable assets and unbound installed builds lack the required new acceptance evidence, some literal source bindings lack exact change attribution, and predicate retirement still needs case-by-case replacement coverage. No two numerical hypotheses were attempted or refuted; this is a provenance blocker, not a numerical search.','','changed_files:','','- `orchestra/reports/F40-stale-bindings-adjudication.md`','- `orchestra/reports/F40-adjudication.json`','- `orchestra/reports/F40-adjudicate.py`','- `orchestra/reports/F40-render-report.py`','- `orchestra/reports/F40-regenerate-owner.py`','- `orchestra/reports/F40-verification.json` (retained regeneration result and focused test log)','- `refs/conformance/olmblur_pf16_worker_sources_exported_public_owner_20260813.json` (two helper hashes only)','','verify:','','From this worktree, run sequentially:','','```sh','export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1','export TMPDIR="$PWD/orchestra/state/F40-stale-bindings-adjudication"','export TMP="$TMPDIR" TEMP="$TMPDIR"','mkdir -p "$TMPDIR"','PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"','"$PY" -B orchestra/reports/F40-regenerate-owner.py > "$TMPDIR/verify-owner.log" 2>&1','"$PY" -B tests/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py -v > "$TMPDIR/verify-tests.log" 2>&1','python3 -B orchestra/reports/F40-adjudicate.py > "$TMPDIR/verify-inventory.log" 2>&1','python3 -B orchestra/reports/F40-render-report.py','git diff --check','```','','Expected: two identical generations with the report SHA above, all non-identity fields unchanged, 4 tests PASS; inventory 110 commands, categories b=72/d=38. Inventory values can change if installed binaries or tracked inputs change; inspect differences instead of accepting them. The inventory fixes consumer/history traversal to the recorded base; live current hashes are intentional. Rendering only writes this proposal report. No build tree is retained.','','next:','','1. Supply build/install receipts for observed installed binaries (especially KiraKira), and exact historical worker/handoff assets. Do not infer their build commits from receipt commits.','2. Recover old source blobs or contemporaneous source manifests for literal pins absent from reachable file history; then assign exact changes instead of last-change guesses.','3. A follow-up should replay each conditional repin against its unchanged AEX expectations, regenerate eligible evidence twice, and replace only documented superseded rejection predicates with equally strict current behavioral checks.','4. Investigate commands 083/164/184 separately as host/admission failures; recover writable tamper-test packages without copying MAIN assets.']
(OUT/'F40-stale-bindings-adjudication.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'commands':len(rows),'unique_bindings':len(catalog),'groups':groups},sort_keys=True))
