"""F54b read-only watches with original cropped geometry and saved-output binding."""
import argparse, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import load_corpus,sha
parser=argparse.ArgumentParser()
parser.add_argument('--watch', default='56f0,272,first')
args=parser.parse_args()
out=ROOT/'orchestra/state/N03-radialblur-v2-mismatch'/('watch-'+args.watch.replace(',', '-'))
out.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1')
worker_name='worker-F54b'
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=60,worker=Path.home()/'.cache/olm-emu'/worker_name/'aex-guest-worker'))
for name in ['403be984da1ad8593fa159b4','ab18858afb75411545de86c7']:
 case,saved=load_corpus(ROOT/f'orchestra/reports/nightly-20261025/witnesses/{name}.json',a)
 d=out/name;d.mkdir(exist_ok=True);w,h=case['geometry']
 a.env.update(AEXCOMPAT_SMART_TRACE=str(d/'trace.json'),AEXCOMPAT_SMART_TRACE_WATCH=args.watch)
 result,raw=a.oracle(case,d,time.monotonic()+120,'smart')
 report=dict(watch=args.watch,worker_sha256=sha(a.worker.read_bytes()),aex_sha256=sha(a.aex.read_bytes()),input_sha256=sha(case['pixels']),result=result,sha256=sha(raw),bound=sha(raw)==saved['result']['oracle']['raw_sha256'],trace_exists=(d/'trace.json').exists())
 (d/'result.json').write_text(json.dumps(report,indent=2));print(name,report,flush=True)
