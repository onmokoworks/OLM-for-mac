#!/usr/bin/env python3
"""Summarize completed measurements without promoting blocked gates."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings'
def read(name):return json.loads((S/name).read_text())
generic=read('generic-after.json');assert generic['status']!='RUNNING'
perf=read('performance-current.json');assert perf['run_state']=='COMPLETED'
assert len(perf['results'])==20 and all(r['status']=='passed' for r in perf['results'])
assert perf['provenance']['post_run_dependency_match'] and perf['provenance']['post_run_toolchain_match']
blur=read('blur-after.json');assert len(blur)==6 and all(r['exit']==0 for r in blur)
result=dict(status='blocked',release_aggregate_rerun=False,contracts=read('contracts.json'),
 f40_baseline_counts=dict(Counter(str(r['exit']) for r in read('f40.json'))),
 f40_dispositions=dict(Counter(r['status'] for r in read('f40-adjudication.json')['rows'])),
 blur_after=blur,bindings_before=read('bindings-before.json'),bindings_after=read('bindings.json'),
 generic_counts=generic['counts'],generic_status=generic['status'],
 generic_failures=[dict(test=r['test'],exit=r['exit_code']) for r in generic['entries'] if r['status']!='PASS'],
 performance=dict(cells=len(perf['results']),status=perf['outcome'],measurement_source_identity=perf['provenance']['measurement_source_identity'],report_sha256=hashlib.sha256((ROOT/'reports/generic_beta_perf_smoke.json').read_bytes()).hexdigest()),
 colorkeep=read('colorkeep-oracle/mac.json'),
 reserved_radial_fixtures=[162,163,164],
 boundary='No release promotion, native AE renewal, installed identity renewal, or all-input exactness claim.')
(ROOT/'orchestra/reports/R07-results.json').write_text(json.dumps(result,indent=2)+'\n')
print('generic',generic['counts'],'performance20/20; Blur6/6; ticket blocked')
