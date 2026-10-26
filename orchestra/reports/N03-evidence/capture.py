"""Capture original IPP input planes from the six retained public witnesses."""
import argparse, gzip, json, os, sys, time
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'orchestra/state/N03-distancegradation-bilateral-refusals'
S.mkdir(parents=True,exist_ok=True)
os.environ['TMPDIR']=str(S)
sys.path[:0]=[str(R/'tools/fuzz'),str(R/'tools/emulation')]
from adapters.olmdistancegradation import Adapter
from core import load_corpus,sha,raw_diff
from run import main_checkout
worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker'
args=argparse.Namespace(max_size=1920,case_timeout=120,main=main_checkout(),worker=worker,geometry='realistic-v2')
a=Adapter(args);deadline=time.monotonic()+1800
build=S/'build';build.mkdir(exist_ok=True);a.prepare(build,deadline)
rows=[]
for p in sorted((R/'tests/fuzz_corpus/olmdistancegradation_N02').rglob('*.json')):
 a.max_size=json.loads(p.read_text())["max_size"]
 c,_=load_corpus(p,a)
 if p.stem.startswith('cce92'):continue
 d=S/p.stem;d.mkdir(exist_ok=True)
 trace=d/'trace.json'
 a.env.update(AEXCOMPAT_SMART_TRACE=str(trace),AEXCOMPAT_SMART_TRACE_WATCH=f"c2f0,{c['geometry'][0]*c['geometry'][1]*4},all")
 oracle,raw=a.oracle(c,d,deadline,'smart')
 oracle["raw_sha256"]=sha(raw)
 status,actual,guards=a.candidate(c,d,'smart',deadline)
 row=dict(id=p.stem,geometry=c['geometry'],depth=c['depth'],parameters=c['parameters'],oracle=oracle,candidate=status,guards=guards,trace_exists=trace.exists(),diff=raw_diff(raw,actual,c["depth"]) if raw is not None and actual is not None else None)
 if trace.exists():
  with gzip.open(R/'orchestra/reports/N03-evidence'/f'{p.stem}-trace.json.gz','wt') as f:f.write(trace.read_text())
 rows.append(row);print(p.stem,oracle,status,flush=True)
(R/'orchestra/reports/N03-evidence/capture.json').write_text(json.dumps(dict(source_sha256=sha((R/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp').read_bytes()),worker_sha256=sha(worker.read_bytes()),aex_sha256=sha(a.aex.read_bytes()),rows=rows),indent=2)+'\n')

assert len(rows)==6 and all(r['oracle']['status']=='ok' and r['candidate']['status']=='ok' and r['diff']['different_words']==0 for r in rows)
