#!/usr/bin/env python3
"""Record measured F40 outcomes and distinguish absent packages from bad paths."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MAIN=ROOT.parent.parent
S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings'
original=json.loads((ROOT/'orchestra/reports/F40-adjudication.json').read_text())['commands']
runs={r['key']:r for r in json.loads((S/'f40.json').read_text())}
after={r['key']:r for r in json.loads((S/'blur-after.json').read_text())}
rows=[]
for old in original:
 key=f"fixture-{old['index']:03d}";row=dict(key=key,legacy_category=old['category'],before=old['returncode'])
 if key not in runs:
  row.update(status='reserved for R08' if 152<=old['index']<=181 else 'requires real AE/Windows' if old['index']>=201 else 'group1 contract finding',reason='See group1 table; no acceptance inferred' if old['index']<201 else 'Installed identity preflight requires current installation receipts and host evidence; R05 remains historical, not a new R07 host run.')
 else:
  run=after.get(key,runs[key]);log=ROOT/run['log'];text=log.read_text(errors='replace')
  errors=[line[:800] for line in text.splitlines() if re.search(r'Error:|FAIL_|^FAIL:|^ERROR:',line)]
  missing=[]
  for value in sorted(set(re.findall(r"(?:No such file or directory: |can't open file )('.*?'|PosixPath\('.*?'\))",text))):
   p=Path(value.removeprefix('PosixPath(').removesuffix(')').strip("'"))
   if not p.is_absolute():p=ROOT/p
   try:main=MAIN/p.relative_to(ROOT)
   except ValueError:main=p
   missing.append(dict(requested=str(p),exists=p.exists(),main_candidate=str(main),main_exists=main.exists()))
  status='passed' if run['exit']==0 else 'blocked'
  reason='Current strict consumer passes; unchanged numerical assertions.' if status=='passed' else 'Current consumer rejects its retained binding/contract. No complete twice-original plus current-build replacement for this entire consumer was obtained; retain failure.'
  if missing:reason='Missing dependency; existence checked separately at MAIN. A path fix cannot reconstruct absent historical bytes or establish an equally strict replacement.'
  if any(m['main_exists'] for m in missing):reason='Some historical request inputs exist in MAIN but this consumer uses a worktree-only path. Remaining digest/source assertions also fail; no identity assertion was bypassed or input copied into the worktree.'
  if 'installed identity manifest' in text or 'installed Radial binary drift' in text:
   status='requires real AE/Windows';reason='Installed executable identity is stale. A source rebuild alone cannot renew the pinned install/host claim.'
  row.update(status=status,reason=reason,exit=run['exit'],before_refresh_exit=runs[key]['exit'],log=run['log'],errors=errors,missing=missing)
 rows.append(row)
result=dict(scope='All 110 F40 records; 100 fresh baseline commands, six focused after-refresh commands; reserved and installed preflights explicitly separate',rows=rows)
(S/'f40-adjudication.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# R07 F40 per-item adjudication','','Before is F40; current is a fresh R07 child exit unless explicitly reserved/host-only. Full diagnostics and missing-path checks are in the evidence archive. No blocked result is a pass.','','| Fixture | Before | R07 before → after refresh | Disposition / first diagnostic |','|---|---:|---|---|']
for r in rows:
 err=(r.get('errors') or [r['reason']])[0].replace('|','\\|').replace('\n',' ')[:240]
 lines.append(f"| {r['key']} | {r['before']} | {r.get('before_refresh_exit','—')} → {r.get('exit','—')} | {r['status']}: {err} |")
(ROOT/'orchestra/reports/R07-f40-items.md').write_text('\n'.join(lines)+'\n')
from collections import Counter
print(dict(Counter(r['status'] for r in rows)))
