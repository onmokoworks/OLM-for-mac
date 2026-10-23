#!/usr/bin/env python3
"""Serial raw oracle differential on every saved non-Smoother-v1 corpus."""
import hashlib, importlib, json, os, sys, tempfile, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F32-smoother-oracle-deep-pixels'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import load_corpus

def main():
 S.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
 cache=Path.home()/'.cache/olm-emu'
 workers=[cache/'worker-F30-ucrtmath/aex-guest-worker',cache/'worker-F32-deep/aex-guest-worker']
 rows=[]
 for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
  for path in sorted(corpus.glob('*.json')):
   data=json.loads(path.read_text());plugin=data['plugin']
   if plugin=='olmsmoother':continue
   adapters=[importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=w,max_size=data['max_size'],case_timeout=30)) for w in workers]
   case,_=load_corpus(path,adapters[0]); results=[]
   with tempfile.TemporaryDirectory(dir=S,prefix='replay-') as td:
    for a in adapters:
     status,raw=a.oracle(case,Path(td),time.monotonic()+60)
     results.append(dict(status=status,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
   equal=results[0]==results[1]
   rows.append(dict(corpus=str(path.relative_to(ROOT)),results=results,equal=equal))
  print(corpus.name,len(rows),sum(not r['equal'] for r in rows),flush=True)
 report=dict(worker_sha256=[hashlib.sha256(w.read_bytes()).hexdigest() for w in workers],total=len(rows),changed=sum(not r['equal'] for r in rows),rows=rows)
 (S/'corpus-differential.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['changed']==0
if __name__=='__main__':main()
