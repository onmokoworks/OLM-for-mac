"""Serial raw-byte comparisons and 50 TSan fuzz renders, including threaded sizes."""
import copy, hashlib, json, os, sys, time, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/perf'))
import ref_vs_fast as rf
S=ROOT/'orchestra/state/P07e-radialblur-rotation-parallel/threads'
S.mkdir(parents=True,exist_ok=True)
o=types.SimpleNamespace(plugin='radialblur',max_size=64,case_timeout=180,main=ROOT.parent.parent,
 worker=Path('/unused'),size_sampler='default',size_max_height=64)
results=[]
adapters={}
for kind in ('reference','fast','tsan'):
 d=S/kind;d.mkdir(exist_ok=True)
 if kind=='tsan':
  wrapper=S/'tsan-cxx'
  wrapper.write_text('#!/bin/sh\nexec /usr/bin/clang++ -g -fsanitize=thread "$@"\n')
  wrapper.chmod(0o755)
  os.environ['UCRT_CXX']=str(wrapper)
 adapters[kind]=rf.build('reference' if kind=='reference' else 'fast',o,d,time.monotonic()+300)
 adapters[kind].env['TSAN_OPTIONS']='halt_on_error=1'
 print('built',kind,flush=True)
os.environ.pop('UCRT_CXX',None)
for index in range(50):
 a=adapters['fast'];case=a.generate(20261026,index)
 # Retain fuzz values, force rotation, enlarge alternate cases across dispatch threshold.
 next(p for p in case['parameters'] if p['slot']==1)['value']=2
 if index%2==0:
  old=case['geometry'];payload=case['pixels'];case['geometry']=[129,129]
  n=129*129*case['depth']//8*4
  case['pixels']=(payload*((n+len(payload)-1)//len(payload)))[:n]
  a.resize(case,old)
 # Keep the independent sampler test bounded without selecting expected pixels.
 next(p for p in case['parameters'] if p['slot']==20)['value']=5
 record=dict(index=index,case={k:v for k,v in case.items() if k!='pixels'},input_sha256=hashlib.sha256(case['pixels']).hexdigest(),runs=[])
 ref,raw=rf.run(adapters['reference'],case,S/'reference',1,180)
 for kind,tasks in [('fast',1),('fast',2),('fast',8),('tsan',8)]:
  result,path=rf.run(adapters[kind],case,S/kind,tasks,180)
  first=rf.difference(raw,path)
  record['runs'].append(dict(kind=kind,tasks=tasks,result=result,first_mismatch=first))
  assert result==ref and first is None,record
 results.append(record)
 (S/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(index,case['depth'],case['geometry'],ref['error'],'exact',flush=True)
print('50 cases; 150 fast comparisons and 50 TSan comparisons passed',flush=True)
