#!/usr/bin/env python3
"""Twice bind full-size read-only R08 snapshots to F46 and current production."""
import base64,contextlib,hashlib,importlib,json,os,re,shutil,subprocess,sys,tempfile,time,zlib
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R08-radial-fullsize-trace';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1');tempfile.tempdir=str(S)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation'),str(ROOT/'tools/fuzz')]
from olm_assets import main_assets
from adapters.radialblur import Adapter
from PIL import Image
import numpy as np

def sha(b):return hashlib.sha256(b).hexdigest()
def pressure():
 p=subprocess.check_output(['memory_pressure'],text=True);free=int(re.search(r'System-wide memory free percentage: (\d+)%',p)[1]);assert free>=30,free;return free

def main():
 d=S/'165';d.mkdir(exist_ok=True)
 old=next(r for r in json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text()) if r['command_index']==165)
 f=importlib.import_module('test_olmradialblur_case0010_rotation_mac_production_planes_20260805')
 pixels=np.asarray(Image.open(f.INPUT).convert('RGBA'),dtype=np.uint8)[:,:,[3,0,1,2]].tobytes();assert sha(pixels)==old['source_sha256']
 case=dict(geometry=old['geometry'],depth=8,parameters=old['parameters'],pixels=pixels,input_padding=0,output_padding=0)
 n=1800*1104; watches=[]
 for name,fn,reg,off,size in [('polar',0x2780,'rcx',0x38,n*16),('source_scalar',0x2780,'rcx',0x40,n*4),('eligibility',0x24c0,'stack5',None,n),('accum',0x24c0,'rcx',0x3c940,n*16),('max_alpha',0x24c0,'rcx',0x3c948,n*4),('normalized',0x1000,'rcx',None,n*16)]:
  w=dict(id=name,function_rva=fn,register=reg,size=size,occurrence=1)
  if off is not None:w['dereference_offset']=off
  watches.append(w)
 wp=d/'watches.json';wp.write_text(json.dumps(watches,indent=2)+'\n')
 report=dict(command_index=165,input_sha256=sha(pixels),runs=[],planes={})
 for worker_name in ('worker-F46-pow','worker-R08-trace'):
  worker=Path.home()/'.cache/olm-emu'/worker_name/'aex-guest-worker'
  build=json.loads((worker.parent/('build.json' if worker_name=='worker-R08-trace' else '../F46-pow-build.json')).read_text()) if worker_name=='worker-R08-trace' else None
  expected=build['worker_sha256'] if build else '6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903'
  assert sha(worker.read_bytes())==expected
  for repeat in (1,2):
   rd=d/f'{worker_name}-{repeat}';rd.mkdir(exist_ok=True)
   a=Adapter(SimpleNamespace(main=main_assets(),worker=worker,max_size=1920,case_timeout=1500))
   if worker_name=='worker-R08-trace':a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(rd/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
   free=pressure();status,raw=a.oracle(case,rd,time.monotonic()+1520)
   (rd/'output.argb.zlib').write_bytes(zlib.compress(raw,9))
   row=dict(worker=worker_name,worker_sha256=expected,repeat=repeat,status=status,sha256=sha(raw),bytes=len(raw),memory_free_percent=free,aex_sha256=sha(a.aex.read_bytes()))
   report['runs'].append(row);(d/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(row),flush=True)
   assert status['status']=='ok' and status['guards_intact'] and status['session_clean']
   if worker_name=='worker-R08-trace':
    t=json.loads((rd/'trace.json').read_text());assert t['image_sha256']==row['aex_sha256'];assert not t['truncated'] and not t['dropped_memory_witnesses'] and not t['trace_configuration']['unhookable_watches']
    for w in watches:
     stage='after' if w['id'] in ('accum','max_alpha') else 'before'
     v=next(v for v in t['memory_witnesses'] if v['watch_id']==w['id'])[stage]
     b=bytes.fromhex(v['hex']);assert v['status']=='captured' and len(b)==w['size'] and sha(b)==v['sha256']
     (rd/(w['id']+'.zlib')).write_bytes(zlib.compress(b,9))
    for witness in t['memory_witnesses']:
     for stage in ('before','after'):witness.get(stage,{}).pop('hex',None)
    (rd/'trace-metadata.json').write_text(json.dumps(t,indent=2)+'\n');(rd/'trace.json').unlink();del t
 assert len({r['sha256'] for r in report['runs']})==1
 # Reuse the existing production seam and save files before its historical-pin checks.
 class Captured(Exception):pass
 original_run=subprocess.run
 def capture(argv,*args,**kwargs):
  value=original_run(argv,*args,**kwargs)
  if isinstance(argv,list) and len(argv)==10 and str(argv[0]).endswith('/probe'):
   assert value.returncode==0
   for name,path in zip(['polar','eligibility','source_scalar','accum','max_alpha','normalized','output','witness'],argv[2:]):shutil.copy2(path,d/('mac-'+name+'.bin'))
   raise Captured()
  return value
 subprocess.run=capture
 try:
  with (d/'mac.log').open('w') as log,contextlib.redirect_stdout(log):f.main()
 except Captured:pass
 finally:subprocess.run=original_run
 for name in ['polar','eligibility','source_scalar','accum','max_alpha','normalized','output']:
  mac=(d/('mac-'+name+'.bin')).read_bytes();filename='output.argb.zlib' if name=='output' else name+'.zlib'
  left=zlib.decompress((d/'worker-R08-trace-1'/filename).read_bytes());right=zlib.decompress((d/'worker-R08-trace-2'/filename).read_bytes());assert left==right and len(left)==len(mac)
  neq=np.flatnonzero(np.frombuffer(left,dtype=np.uint8)!=np.frombuffer(mac,dtype=np.uint8));first=int(neq[0]) if len(neq) else None
  report['planes'][name]=dict(bytes=len(left),original_sha256=sha(left),mac_sha256=sha(mac),repeat_identical=True,different_bytes=len(neq),first_byte=first,original_byte=left[first] if first is not None else None,mac_byte=mac[first] if first is not None else None)
  (d/('mac-'+name+'.zlib')).write_bytes(zlib.compress(mac,9));(d/('mac-'+name+'.bin')).unlink()
 if any(v['different_bytes'] for v in report['planes'].values()):
  witness=dict(schema='olm-fuzz-case/1',plugin='radialblur',generator_version=1,seed=0,index=165,max_size=1920,operations=[],case={k:v for k,v in case.items() if k!='pixels'},input_sha256=sha(pixels),pixels_zlib_base64=base64.b64encode(zlib.compress(pixels,9)).decode(),result=report,provenance=dict(ticket='R08',scope='full-size intermediate planes; final output separately bound to F46 twice'))
  (d/'witness.json').write_text(json.dumps(witness,indent=2)+'\n')
 (d/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['planes'],indent=2),flush=True)
if __name__=='__main__':main()
