"""Instrument the original fixture; compare its final output to retained worker.
Run with MAIN tools/emulation/.venv/bin/python (Unicorn installed there).
"""
import json,os,sys,time,types,struct
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode = True
R=Path(__file__).resolve().parents[3];sys.path[:0]=[str(R/'tools/emulation'),str(R/'tools/fuzz')]
S=R/'orchestra/state/N02-olmdirectionalblur-nightly-20261025/trace';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
from core import load_corpus,sha
from run import main_checkout
from geometry import require_host
rows=[]
for p in sorted((R/'tests/fuzz_corpus/olmdirectionalblur/N02-nightly-20261025').glob('*.json')):
 d=json.loads(p.read_text());den=d['case']['downsample'][0][1]
 path=R/'tools/emulation/probe_directionalblur_c02_stages.py'
 m=types.ModuleType('tracer');m.__file__=str(path)
 body=path.read_text().replace("'--downsample-den','1'",f"'--downsample-den','{den}'")
 body=body.replace("trace['work_geometry']=[ww,wh]", """trace['work_geometry']=[ww,wh]
                trace['back_count']=fixture.u32(ld,ctx+0x54)
                trace['back_storage']=ld.read_bytes(ctx+0x7ee8,400).hex()
                ld.add_read_trace_range(ctx+0x7ee8,ctx+0x8078,'back')
                trace['reads']=ld.read_trace""")
 exec(compile(body,str(path),'exec'),m.__dict__)
 s=S/p.stem;s.mkdir(exist_ok=True)
 ad=m.TracedAdapter(SimpleNamespace(main=main_checkout(),worker=Path(d['provenance']['worker_path']),max_size=d['max_size'],case_timeout=20,core_ref=None,gate_off=False,nonfinite_off=False))
 require_host(ad,{'geometry_sampler':d['geometry_sampler']});deadline=time.monotonic()+500;provenance=ad.prepare(s,deadline)
 c,_=load_corpus(p,ad)
 trace,stages,raw=m.run_fixture(c,s,ad.aex)
 o,ref=ad.oracle(c,s,deadline,'smart')
 ad.env['OLM_C02_TRACE']=str(s);cr,actual,*_=ad.candidate(c,s,'smart',deadline)
 paired={key:m.compare(value,(s/key).read_bytes(),4) for key,value in stages.items() if (s/key).exists()}
 rows.append(dict(witness=p.name,provenance=provenance,fixture_matches_worker=raw==ref,fixture_sha256=sha(raw),worker_sha256=sha(ref),mac_sha256=sha(actual),paired=paired,trace=trace,divisor=struct.unpack('<f',stages['divisor'])[0]))
 print(p.name,raw==ref,'divisor',rows[-1]['divisor'],'count',trace['back_count'],'reads',trace['reads'],flush=True)
 (R/'orchestra/reports/N02-evidence/stages.json').write_text(json.dumps(rows,indent=2)+'\n')
