#!/usr/bin/env python3
"""Reproduce the missing ceilf/floorf providers in the second Smoother host."""
import hashlib,json,math,os,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F32-smoother-oracle-deep-pixels/hosts'
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'tools/fuzz'),str(ROOT/'tools/emulation')]
from adapters.olmsmoother import Adapter
from core import load_corpus
import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as owner
from unicorn.x86_const import UC_X86_REG_RSP
Original=owner.AexLoader

def main():
 S.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
 worker=Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
 adapter=Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=worker,max_size=256,case_timeout=30))
 owner.AEX=adapter.aex
 # This experiment installs instrumented providers in Traced, including the old no-op.
 owner.register_smoother_math=lambda loader: None
 code=owner.guest_code(S,4)
 rows=[]
 for path in sorted((ROOT/'tests/fuzz_corpus/olmsmoother').glob('*.json')):
  case,_=load_corpus(path,adapter);owner.W,owner.H=case['geometry'];owner.KEY=tuple(case['parameters'][1]['value'][1:])
  runs=[]
  for fixed in (False,True):
   imports=[];scans=[]
   class Traced(Original):
    def __init__(self,*args,**kwargs):
     super().__init__(*args,**kwargs)
     for name,fn in [('ceilf',math.ceil),('floorf',math.floor)]:
      def callback(uc,args,name=name,fn=fn):
       value=self.read_xmm_f32(0);out=float(fn(value)) if fixed else value
       imports.append(dict(name=name,input=value,output=out,implemented=fixed))
       if fixed:self.write_xmm_f32(0,out)
       return 0
      self.register_import_impl(name,callback)
     def scan(*_):
      scans.append(int.from_bytes(self.read_bytes(self.uc.reg_read(UC_X86_REG_RSP)+0x30,4),'little'))
     self.add_code_hook(0x180006710,scan)
   owner.AexLoader=Traced
   raw,_=owner.actual(8,case['pixels'],owner.W*4,case['parameters'][0]['value'],case['parameters'][2]['value'],code)
   runs.append(dict(sha256=hashlib.sha256(raw).hexdigest(),imports=imports,scans=scans))
  status,raw=adapter.oracle(case,S,time.monotonic()+60);assert status['status']=='ok'
  digest=hashlib.sha256(raw).hexdigest()
  rows.append(dict(corpus=path.name,worker_sha256=digest,unimplemented=runs[0],implemented=runs[1],fixed_equal=runs[1]['sha256']==digest))
 # Capture the frozen worker at the classifier-to-executor boundary.
 from PIL import Image
 path=ROOT/'tests/fuzz_corpus/olmsmoother/seed1_case000006_92552f06afe6.json'
 case,_=load_corpus(path,adapter)
 rgba=bytes(v for i in range(0,len(case['pixels']),4) for v in (*case['pixels'][i+1:i+4],case['pixels'][i]))
 ip=S/'boundary.png';Image.frombytes('RGBA',tuple(case['geometry']),rgba).save(ip)
 frozen=Path.home()/'.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker'
 trace_path=S/'frozen-boundary.json'
 cmd=[str(frozen),'render-trace-png',str(owner.AEX),str(ip),str(S/'boundary-out.png'),'--pixel-format','argb8','--watch','function=0x6710,arg=stack6,size=1','param_1@1=0','param_2@2=255,255,255,255','param_3@3=6']
 with trace_path.open('w') as log:
  subprocess.run(cmd,stdout=log,stderr=subprocess.PIPE,check=True)
 traced=json.loads(trace_path.read_text())
 render=next(t for t in traced['execution_traces'] if t['selector']=='RENDER')
 assert not render['truncated'] and not render['dropped_memory_witnesses']
 boundary=dict(worker_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),output_sha256=traced['raw_pixel_sha256'],classifier_results=[w['before']['address'] for w in render['memory_witnesses'] if w['watch_id']=='watch-1'])
 selected=next(r for r in rows if r['corpus']==path.name)
 assert boundary['classifier_results']==selected['implemented']['scans']
 assert boundary['output_sha256']==selected['worker_sha256']
 report=dict(frozen_boundary=boundary,total=len(rows),fixed_equal=sum(r['fixed_equal'] for r in rows),unimplemented_equal=sum(r['unimplemented']['sha256']==r['worker_sha256'] for r in rows),rows=rows)
 (S.parent/'host-import-differential.json').write_text(json.dumps(report,indent=2)+'\n')
 print({k:v for k,v in report.items() if k!='rows'})
 assert report['fixed_equal']==report['total']
if __name__=='__main__':main()
