#!/usr/bin/env python3
"""Replay saved exact Smart pixels through ASan/UBSan production code."""
import json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from geometry import require_host
from core import load_corpus,sha
from run import main_checkout
os.environ['OLM_RADIAL_CANDIDATE_SANITIZE']='1'
s=ROOT/'orchestra/state/P02d-radialblur-geometry/sanitized';s.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=60));a.routes=('smart',)
a.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
deadline=time.monotonic()+1800;p=a.prepare(s,deadline);rows=[]
for path in sorted((ROOT/'tests/fuzz_corpus/radialblur_realistic_P02d').glob('*.json')):
 c,saved=load_corpus(path,a);require_host(a,c);out=a.candidate(c,s,'smart',deadline);r,raw=out[:2]
 expected=saved['result']['oracle'];ok=r['status']=='ok' and sha(raw)==expected['raw_sha256'] and r.get('output_rect')==expected.get('output_rect')
 rows.append(dict(file=path.name,exact=ok,result=r,sha256=sha(raw)));print(path.name,ok,flush=True)
(ROOT/'orchestra/reports/P02d-evidence/sanitized.json').write_text(json.dumps(dict(provenance=p,cases=rows),indent=2)+'\n')
assert all(r['exact'] for r in rows)
