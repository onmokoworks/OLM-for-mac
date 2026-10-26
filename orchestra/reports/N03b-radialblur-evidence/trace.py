"""F54c full cropped source and polar boundary captures, bound to saved output."""
import json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import load_corpus,sha
out=ROOT/'orchestra/state/N03b-radialblur-v2-mismatch/trace'
out.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=60,worker=Path.home()/'.cache/olm-emu/worker-F54c/aex-guest-worker'))
for name,size in [('403be984da1ad8593fa159b4',1708800),('ab18858afb75411545de86c7',713760)]:
 case,saved=load_corpus(ROOT/f'orchestra/reports/nightly-20261025/witnesses/{name}.json',a)
 d=out/name;d.mkdir(exist_ok=True);w,h=case['geometry']; h=10 if name.startswith('ab') else h
 watches=[dict(id='source_world',function_rva=0x56f0,register='rdx',dereference_offsets=[8],size=128,occurrence=1),dict(id='world_pixels',function_rva=0x56f0,register='rdx',dereference_offsets=[8,24],size=160,occurrence=1)]
 watches.extend([dict(id='builder-context',function_rva=0x8690,register='r9',size=272,occurrence=1),dict(id='layer-dest',function_rva=0xd9d0,register='r9',size=120,occurrence=1),dict(id='copy-dest',function_rva=0x19f20,register='rdx',size=120,occurrence=1)])
 for fn in (0x6d10,0x7d30):
  watches.append(dict(id=f'{fn:x}-input',function_rva=fn,register='r8',size=128,occurrence=1))
  watches.append(dict(id=f'{fn:x}-owner',function_rva=fn,register='stack5',size=272,occurrence=1))
 for label,off,n in [('noise-owner',None,272),('noise-source',0x98,w*h*16),('noise-world',8,128)]:
  watch=dict(id=label,function_rva=0x65c0,register='rcx',size=n,occurrence=1)
  if off is not None:watch['dereference_offset']=off
  watches.append(watch)
 for fn in (0x17290,0x172c0):
  watches.append(dict(id=f'{fn:x}-world',function_rva=fn,register='rcx',size=128,occurrence=1))
 for fn in (0x17360,0x173d0):
  watches.append(dict(id=f'{fn:x}-pixel',function_rva=fn,register='stack5',size=16,occurrence=1))
 for label,off,n in [('owner',None,272),('source',0x98,w*h*16),('source_size',0x88,w*h*4),('source_span',0x90,w*h*4),('final',0xa0,w*h*16)]:
  watch=dict(id=label,function_rva=0x56f0,register='rdx',size=n,occurrence=1)
  if off is not None:watch['dereference_offset']=off
  watches.append(watch)
 for label,off,n in [('context',None,16944),('polar',0x38,size),('scalar',0x40,size//4),('prepass',0x48,size//4),('span',0x50,size//4),('accum',0x4210,size),('maximum',0x4218,size//4)]:
  watch=dict(id=label,function_rva=0xb150,register='rcx',size=n,occurrence=1)
  if off is not None:watch['dereference_offset']=off
  watches.append(watch)
 watches.append(dict(id='normalized',function_rva=0x9d80,register='rcx',size=size,occurrence=1))
 watches.append(dict(id='scatter-accum',function_rva=0xa9d0,register='rcx',dereference_offset=0x4210,size=size,occurrence=1))
 wp=d/'watches.json';wp.write_text(json.dumps(watches,indent=2))
 a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(d/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
 result,raw=a.oracle(case,d,time.monotonic()+120,'smart')
 report=dict(worker_sha256=sha(a.worker.read_bytes()),aex_sha256=sha(a.aex.read_bytes()),input_sha256=sha(case['pixels']),result=result,sha256=sha(raw),bound=sha(raw)==saved['result']['oracle']['raw_sha256'])
 (d/'result.json').write_text(json.dumps(report,indent=2));print(name,report,flush=True)
 assert report['bound']
 trace=json.loads((d/'trace.json').read_text())
 print([(x['watch_id'],x['before']['status'],x['after']['status']) for x in trace['memory_witnesses']],flush=True)
