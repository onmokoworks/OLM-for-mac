"""Fifty fuzz-generated frames above the threading threshold, under TSan."""
import importlib.util,sys,os,time,json
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P07c-smoother-threading/tsan';S.mkdir(exist_ok=True)
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('ref',R/'tools/perf/ref_vs_fast.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from adapters.olmsmoother import Adapter
options=SimpleNamespace(case_timeout=180,main=R.parent.parent,worker=Path('/unused'),max_size=64,size_sampler='default',size_max_height=64)
a=Adapter(options);a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),TSAN_OPTIONS='halt_on_error=1')
original=a.compile
a.compile=lambda argv,deadline: original([*argv,'-fsanitize=thread','-g'] if str(argv[0])=='clang++' else argv,deadline)
a.binary,_=a.build(S,time.monotonic()+300)
rows=[]
for index in range(50):
    case=a.generate(20261025,index)
    # PF32 is unsupported; use a generated integer case so every run threads.
    while case['depth']==32:case=a.generate(20261025,index+100000*(1+len(rows)));index+=100000
    old=case['geometry'];payload=case['pixels'];case['geometry']=[257+index%7,259+index%5]
    n=case['geometry'][0]*case['geometry'][1]*case['depth']//8*4
    case['pixels']=(payload*((n+len(payload)-1)//len(payload)))[:n];a.resize(case,old)
    result,_=m.run(a,case,S,8,180)
    stderr=(S/'stderr').read_text();assert 'ThreadSanitizer' not in stderr,stderr
    assert result['error']==0,result
    rows.append(dict(index=index,depth=case['depth'],geometry=case['geometry'],**result))
    (S/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('50 fuzz renders; no TSan reports')
