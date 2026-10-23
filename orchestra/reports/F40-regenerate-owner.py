#!/usr/bin/env python3
"""Regenerate only the F36 016/017 metadata, retaining every AEX-derived row."""
import hashlib, importlib.util, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRATCH=ROOT/'orchestra/state/F40-stale-bindings-adjudication'
SCRATCH.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
import tempfile
tempfile.tempdir=str(SCRATCH)
p=ROOT/'tools/emulation/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py'
sys.path.insert(0,str(p.parent))
spec=importlib.util.spec_from_file_location('f40_owner',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
saved=json.loads(m.REPORT.read_text())
a=m.live();b=m.live()
assert a==b, 'non-deterministic regeneration'
for k in saved:
 if k!='identities':assert saved[k]==a[k], 'non-identity change: '+k
payload=json.dumps(a,indent=2,sort_keys=True)+'\n'
(SCRATCH/'owner-pass1.json').write_text(payload)
(SCRATCH/'owner-pass2.json').write_text(json.dumps(b,indent=2,sort_keys=True)+'\n')
if '--apply' in sys.argv:
 m.REPORT.write_text(payload)
 m.DOC.write_text(m.markdown(a))
print(json.dumps({'runs':2,'identical':True,'non_identity_fields_unchanged':True,'report_sha256':hashlib.sha256(payload.encode()).hexdigest(),'rows':len(a['rows']),'applied':'--apply' in sys.argv},sort_keys=True))
