"""Python AEX stage trace cross-checked against retained F52c typed output.
F52c's watch CLI accepts promoted RGBA8 PNGs, not this signed input.
P06_VARIANT=candidate selects the rejected experiment without editing production.
"""
import json,os,sys,time,types
from pathlib import Path
from types import SimpleNamespace
from baseline import cores,BASELINE
R=Path(__file__).resolve().parents[3];sys.path[:0]=[str(R/'tools/emulation'),str(R/'tools/fuzz')]
S=R/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch/stages';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
p=R/'tools/emulation/probe_directionalblur_c02_stages.py'
m=types.ModuleType('tracer');m.__file__=str(p)
body=p.read_text().replace("'--downsample-den','1'","'--downsample-den','3'")
body=body.replace('            self.traced_core_sha256=sha(body.encode())', '''            if os.environ.get('P06_VARIANT')=='candidate':
                pos=body.index('static int render_minimal_argb32(')
                body=body[:pos]+body[pos:].replace('if (component_divisor <= 0.0f) component_divisor = 1.0f;', '// Preserve zero divisor.')
            self.traced_core_sha256=sha(body.encode())''')
body=body.replace("trace['work_geometry']=[ww,wh]", """trace['work_geometry']=[ww,wh]
                trace['fade_back_storage_hex']=ld.read_bytes(ctx+0x7ee8,400).hex()
                trace['source_offset']=[fixture.u32(ld,ctx+0x809c),fixture.u32(ld,ctx+0x8098)]""")
exec(compile(body,str(p),'exec'),m.__dict__)
from core import load_corpus,sha
from run import main_checkout
from geometry import require_host
import adapters.olmdirectionalblur as module
candidate=os.environ.get('P06_VARIANT')=='candidate'
cores(module,R,S,wrap=candidate)
module.CORES=[R/'core/dblur_frontonly.cpp' if p.name=='dblur_frontonly.cpp' else p for p in module.CORES]
ad=m.TracedAdapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=20,core_ref=BASELINE,gate_off=False,nonfinite_off=False))
require_host(ad,{'geometry_sampler':'realistic-v1'});deadline=time.monotonic()+500;ad.prepare(S,deadline)
c,_=load_corpus(R/'orchestra/reports/P06a-evidence/reduced.json',ad)
trace,stages,raw=m.run_fixture(c,S,ad.aex)
o,reference=ad.oracle(c,S,deadline,'smart')
ad.env['OLM_C02_TRACE']=str(S);cr,actual,*_=ad.candidate(c,S,'smart',deadline)
rows={}
for key,value in stages.items():
 f=S/key
 if f.exists():rows[key]=m.compare(value,f.read_bytes(),4)
rows.update(fixture_sha256=sha(raw),F52c_sha256=sha(reference),fixture_matches_F52c=raw==reference,mac_sha256=sha(actual),trace=trace)
label='after' if candidate else 'before'
(R/f'orchestra/reports/P06a-evidence/stages-{label}.json').write_text(json.dumps(rows,indent=2)+'\n')
print('fixture_matches_F52c',raw==reference,'stages', {k:v['different_units'] for k,v in rows.items() if isinstance(v,dict) and 'different_units' in v},flush=True)
