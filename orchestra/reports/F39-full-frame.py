#!/usr/bin/env python3
"""F32 public Smart replay of retained command 165; preserve all old assertions."""
import importlib.util,json,subprocess,time,contextlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('recheck',Path(__file__).with_name('F39-recheck.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
import test_olmradialblur_case0010_rotation_mac_production_planes_20260805 as f
from PIL import Image
import numpy as np
from types import SimpleNamespace
import zlib

def main():
 d=r.S/'165';d.mkdir(exist_ok=True)
 subprocess.run(['sh',str(r.ROOT/'ucrtmath/build.sh'),str(d/'ucrtmath')],check=True,capture_output=True)
 run=subprocess.run
 def capture(command,*args,**kwargs):
  if isinstance(command,list) and command[0]=='clang++':command=[*command,str(d/'ucrtmath/libucrtmath.a')]
  result=run(command,*args,**kwargs)
  if isinstance(command,list) and len(command)==10 and str(command[0]).endswith('/probe'):
   (d/'mac.raw').write_bytes(Path(command[-2]).read_bytes())
  return result
 subprocess.run=capture;f.REPORT=d/'mac-report.json'
 try:
  with (d/'mac.log').open('w') as log,contextlib.redirect_stdout(log):rc=f.main()
 finally:subprocess.run=run
 adapter=r.Adapter(SimpleNamespace(main=r.main_assets(),worker=r.WORKER,max_size=1920,case_timeout=1500))
 adapter.aex=r.resolve_asset(r.ROOT/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex')
 pixels=np.asarray(Image.open(f.INPUT).convert('RGBA'),dtype=np.uint8)[:,:,[3,0,1,2]].tobytes()
 params=adapter.defaults(1920,1080)
 values={1:2,2:[960,540],4:4,5:1,6:0,7:0,10:0,11:1,12:0,13:0,15:1,17:1,18:0,20:5,21:1,22:0,24:0,25:1,27:1,28:0,29:10}
 for p in params:p['value']=values[p['slot']]
 case=dict(geometry=[1920,1080],depth=8,parameters=params,pixels=pixels,input_padding=0,output_padding=0)
 status,raw=adapter.oracle(case,d,time.monotonic()+1520)
 (d/'F32.raw').write_bytes(raw)
 old=zlib.decompress(f.FULL_PF8_FIXTURE.read_bytes());mac=(d/'mac.raw').read_bytes()
 row=dict(command_index=165,oracle_status=status,mac_returncode=rc,geometry=case['geometry'],depth=8,parameters=params,source_sha256=r.sha(pixels),worker_sha256=r.sha(r.WORKER.read_bytes()),aex_sha256=r.sha(adapter.aex.read_bytes()),legacy_vs_mac=r.compare(old,mac))
 if status['status']=='ok':row.update(F32_vs_legacy=r.compare(raw,old),F32_vs_mac=r.compare(raw,mac))
 (d/'result.json').write_text(json.dumps(row,indent=2)+'\n');print(status,flush=True)
if __name__=='__main__':main()
