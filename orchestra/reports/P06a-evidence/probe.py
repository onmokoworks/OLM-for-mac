import copy,json,os,sys,time,struct
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
S=R/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch/probe';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
import adapters.olmdirectionalblur as module
from core import evaluate,load_corpus
from geometry import require_host
from run import main_checkout
rows=[]
for version in ('baseline','zero-divisor','wrapped-zero-divisor'):
 s=S/version;s.mkdir(exist_ok=True)
 from baseline import cores
 cores(module,R,s,divisor=version!='baseline',wrap=version=='wrapped-zero-divisor')
 ad=module.Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));ad.routes=('smart',)
 require_host(ad,{'geometry_sampler':'realistic-v1'});deadline=time.monotonic()+500;ad.prepare(s,deadline)
 c,_=load_corpus(R/'orchestra/reports/P06a-evidence/reduced.json',ad)
 cases=[('reduced',c)]
 orig,_=load_corpus(R/'tests/fuzz_corpus/olmdirectionalblur/P05a-performance/preexisting-realistic-v1-seed2053-case9.json',ad);cases.append(('original',orig))
 for a in (-1.0,0.0,1.0):
  t=copy.deepcopy(c);t['pixels']=struct.pack('<4f',a,0.25,0.5,1.0);cases.append((f'alpha{a}',t))
 t=copy.deepcopy(c);t.update(downsample=[[1,1],[1,1]],full_geometry=[1,1]);cases.append(('unscaled',t))
 for name,case in cases:
  r=evaluate(ad,case,s,deadline);rows.append(dict(version=version,name=name,result=r));print(version,name,r['routes']['smart']['status'],r['routes']['smart'].get('diff'),flush=True)
(R/'orchestra/reports/P06a-evidence/probe.json').write_text(json.dumps(rows,indent=2)+'\n')
