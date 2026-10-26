import argparse, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import load_corpus,sha
parser=argparse.ArgumentParser()
parser.add_argument('--mode',choices=['geometry','legacy','normalized'],required=True)
args=parser.parse_args()
out=ROOT/'orchestra/state/N02-radialblur-nightly-20261025'/('recheck-'+args.mode)
out.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1')
worker_name='worker-F53-geom' if args.mode=='geometry' else 'worker-C53b-trace'
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=60,worker=Path.home()/'.cache/olm-emu'/worker_name/'aex-guest-worker'))
for name in ['403be984da1ad8593fa159b4','ab18858afb75411545de86c7']:
 case,saved=load_corpus(ROOT/f'orchestra/reports/nightly-20261025/witnesses/{name}.json',a)
 if args.mode=='normalized': case={k:v for k,v in case.items() if k not in ('geometry_sampler','full_geometry','downsample','request_rect','extent_hint','pixel_aspect','rowbytes_padding')}
 d=out/name;d.mkdir(exist_ok=True);w,h=case['geometry']
 watches=[]
 for fn,reg in [(0x65c0,'rcx'),(0x6aa0,'rcx'),(0x56f0,'rdx')]:
  for label,offset,size in [('context',None,0x110),('size',0x88,w*h*4),('span',0x90,w*h*4),('final',0xa0,w*h*16)]:
   watches.append(dict(id=f'{fn:x}-{label}',function_rva=fn,register=reg,dereference_offset=offset,size=size,occurrence=1))
 wp=d/'watches.json';wp.write_text(json.dumps(watches))
 a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(d/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
 result,raw=a.oracle(case,d,time.monotonic()+120,'smart')
 report=dict(mode=args.mode,worker_sha256=sha(a.worker.read_bytes()),aex_sha256=sha(a.aex.read_bytes()),input_sha256=sha(case['pixels']),result=result,sha256=sha(raw),bound=sha(raw)==saved['result']['oracle']['raw_sha256'],trace_exists=(d/'trace.json').exists())
 (d/'result.json').write_text(json.dumps(report,indent=2));print(name,report,flush=True)
