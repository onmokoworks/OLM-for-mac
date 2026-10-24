"""Diagnose fresh realistic-v1 seed 2053 index 9 against parent and final kernels."""
import importlib,json,os,sys,time,subprocess
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from core import evaluate,save_corpus,sha
from geometry import sample,require_host
from run import main_checkout
S=R/'orchestra/state/P05a-directionalblur-performance/boundary';S.mkdir(parents=True,exist_ok=True);E=R/'orchestra/reports/P05a-evidence'
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
module=importlib.import_module('adapters.olmdirectionalblur');original=list(module.CORES);rows=[]
for version in ('parent','final'):
 s=S/version;s.mkdir(exist_ok=True);module.CORES=list(original)
 if version=='parent':
  for i,p in enumerate(module.CORES):
   if p.name not in ('dblur_rowdriver.cpp','dblur_rotate.cpp'):continue
   text=subprocess.check_output(['git','show','9123f22a0cee8a7592ca7a89ec4f0a962d02b9a8:core/'+p.name],cwd=R,text=True)
   # All local includes resolve to unchanged production headers.
   for header in ('x86_float.h','dblur_rowdriver.h','dblur_noise.h','dblur_rotate.h'):
    text=text.replace('"'+header+'"','"'+str(R/'core'/header)+'"')
   text=text.replace('../ucrtmath/include/ucrtmath.h',str(R/'ucrtmath/include/ucrtmath.h'))
   dst=s/p.name;dst.write_text(text);module.CORES[i]=dst
 ad=module.Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
 require_host(ad,{'geometry_sampler':'realistic-v1'});deadline=time.monotonic()+600;p=ad.prepare(s,deadline)
 c=sample(ad.generate(2053,9),'realistic-v1');assert sha(c['pixels'])=='a00e2a48d78a781f74f6f566c28e1113d57941d2e993841dc2159006f312b365'
 for repeat in range(3):
  r=evaluate(ad,c,s,deadline,{});rows.append(dict(version=version,repeat=repeat,result=r));print(version,repeat,r['oracle']['raw_sha256'],r['routes']['smart']['status'],r['routes']['smart'].get('raw_sha256'),flush=True)
  if version=='final' and repeat==0:save_corpus(E/'boundary-case.json',ad,c,c,r,dict(accepted=[],attempts=0),p)
(E/'boundary-check.json').write_text(json.dumps(rows,indent=2)+'\n')
