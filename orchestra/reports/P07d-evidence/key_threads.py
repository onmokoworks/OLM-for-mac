"""Compare raw Smart outputs at 1/2/8 tasks, then repeat 50 cases under TSan."""
import hashlib,json,os,sys,time,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
sys.dont_write_bytecode=True
from adapters.olmcolorkey import Adapter
S=ROOT/'orchestra/state/P07d-distancegradation-blur-colorkey-threading/key-threads'
S.mkdir(parents=True,exist_ok=True)
o=types.SimpleNamespace(max_size=256,case_timeout=60,main=(ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT),
 worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker')
a=Adapter(o)
a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),TSAN_OPTIONS='halt_on_error=1')
results=[]
for sanitized in (False,True):
 build=S/('tsan' if sanitized else 'normal');build.mkdir(exist_ok=True)
 if sanitized:
  original=a.compile
  def compile(argv,deadline):
   if str(argv[0])=='clang++':argv=[*argv,'-fsanitize=thread','-g']
   return original(argv,deadline)
  a.compile=compile
 a.binary,_=a.build(build,time.monotonic()+180)
 for index in range(50):
  case=a.generate(2026102507,index)
  # Exercise parallel dispatch on alternating cases, retaining generated raw
  # values (including PF32 nonfinites) and original per-pixel arithmetic.
  if index%2==0:
   w,h=case['geometry'];pixels=case['pixels'];n=257*259*case['depth']//8*4
   case['geometry']=[257,259];case['pixels']=(pixels*((n+len(pixels)-1)//len(pixels)))[:n]
   a.resize(case,[w,h])
  row=dict(index=index,sanitized=sanitized,geometry=case['geometry'],depth=case['depth'],runs=[])
  for tasks in ((8,) if sanitized else (1,2,8)):
   d=S/f'case-{index}-{tasks}';d.mkdir(exist_ok=True)
   a.env['OLM_PARALLEL_MAX']=str(tasks)
   result,raw,*_=a.candidate(case,d,'smart',time.monotonic()+90)
   row['runs'].append(dict(tasks=tasks,result=result,sha256=hashlib.sha256(raw).hexdigest()))
   assert result['status'] in ('ok','refusal'),row
  if not sanitized:assert len({(v['result']['status'],v['sha256']) for v in row['runs']})==1,row
  else:assert row['runs'][0]['sha256']==results[index]['runs'][0]['sha256'],row
  results.append(row)
  (S/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print('TSan' if sanitized else 'forced tasks','50 cases passed',flush=True)
