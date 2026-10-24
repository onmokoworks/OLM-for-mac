#!/usr/bin/env python3
"""Replay saved exact Smart pixels through ASan/UBSan production code."""
import json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from geometry import require_host
from core import load_corpus,sha
from run import main_checkout
original_compile=Adapter.compile
def sanitized_compile(self, command, deadline):
 if command[0]=='clang++':command=[command[0],'-fsanitize=address,undefined','-fno-omit-frame-pointer',*command[1:]]
 return original_compile(self,command,deadline)
Adapter.compile=sanitized_compile
s=ROOT/'orchestra/state/P02j-directionalblur-geometry/sanitized';s.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=60));a.routes=('smart',)
a.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
deadline=time.monotonic()+1800;p=a.prepare(s,deadline);rows=[]
for path in sorted((ROOT/'tests/fuzz_corpus/olmdirectionalblur_realistic_P02j').glob('*.json')):
 c,saved=load_corpus(path,a);require_host(a,c);out=a.candidate(c,s,'smart',deadline);r,raw=out[:2]
 expected=saved['result']['oracle'];ok=r['status']=='ok' and sha(raw)==expected['raw_sha256'] and r.get('output_rect')==expected.get('output_rect')
 rows.append(dict(file=path.name,exact=ok,result=r,sha256=sha(raw)));print(path.name,ok,flush=True)
(ROOT/'orchestra/reports/P02j-evidence/sanitized.json').write_text(json.dumps(dict(provenance=p,cases=rows),indent=2)+'\n')
assert all(r['exact'] for r in rows)
