#!/usr/bin/env python3
"""Try the registered F46 worker against the unchanged historical owner contract."""
import inspect
import hashlib, importlib.util, json, os, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings/colorkeep-oracle'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S));tempfile.tempdir=str(S)
spec=importlib.util.spec_from_file_location('ck9',ROOT/'tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
index=json.loads(Path('/Users/onmk/.cache/olm-emu/INDEX.json').read_text())
worker=next(x for x in index['links'] if x['name']=='worker-F46-pow')
m.WORKER=Path(worker['worker_path'])
with m.WORKER.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==worker['worker_sha256']
original_run=subprocess.run
rows=[]
for repeat in range(2):
 calls=[]
 def run(command,**kwargs):
  result=original_run(command,**kwargs)
  if command[0]==str(m.WORKER):
   prefix=S/f'{repeat}-{len(calls)}'
   prefix.with_suffix('.stdout.json').write_text(result.stdout)
   prefix.with_suffix('.stderr.log').write_text(result.stderr)
   calls.append(dict(command=[str(a) for a in command],exit=result.returncode,stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest()))
  return result
 m.subprocess.run=run
 try:
  inputs,outputs,owner=m.fresh_oracle()
  rows.append(dict(repeat=repeat,status='passed',owner=owner,calls=calls))
 except Exception as error:
  rows.append(dict(repeat=repeat,status='blocked',error=str(error),calls=calls))
 finally: m.subprocess.run=original_run
(S/'result.json').write_text(json.dumps(dict(worker=worker,rows=rows),indent=2)+'\n')
assert rows[0].get('owner')==rows[1].get('owner') and all(r['status']=='passed' for r in rows)
print('Original owner: 6 executions, 3 twice-identical depth hashes and suite sequences')
# Build in ticket scratch; never install or turn this candidate into an oracle.
build=S/'build';build.mkdir(exist_ok=True);product=build/'Product'
command=['xcodebuild','-project','mac/ColorKeep/Mac/ColorKeep.xcodeproj','-target','ColorKeep','-configuration','Release','-jobs','1','ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','CODE_SIGNING_ALLOWED=NO',f'CONFIGURATION_BUILD_DIR={product}',f'OBJROOT={build/"Obj"}',f'SYMROOT={build/"Sym"}','build']
with (S/'build.log').open('w') as out: built=subprocess.run(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
mac={'build_command':command,'build_exit':built.returncode}
if built.returncode==0:
 binary=product/'ColorKeep.plugin/Contents/MacOS/ColorKeep'
 mac['binary_sha256']=m.sha(binary)
 capture_prefix=''
 def capture(command,**kwargs):
  r=original_run(command,**kwargs)
  if len(command)>1 and str(command[1])==str(binary):
   name=capture_prefix+('negative' if command[-1]=='negative' else 'positive')
   (S/(name+'.stdout')).write_bytes(r.stdout.encode() if isinstance(r.stdout,str) else r.stdout)
   (S/(name+'.stderr')).write_bytes(r.stderr.encode() if isinstance(r.stderr,str) else r.stderr)
   mac[name+'_exit']=r.returncode
  return r
 m.subprocess.run=capture
 try:
  observed,negative=m.probe(binary,inputs)
  mac['negative']=negative
  mac['all_positive_bytes_equal']=observed==b''.join(outputs[d] for d in ['PF8','PF16','PF8','PF16','PF32'])
 except Exception as error: mac['error']=str(error)
 finally: m.subprocess.run=original_run
# Diagnostic-only host-header completion; keep every historical assertion.
if built.returncode==0 and mac.get('positive_exit'):
 source=inspect.getsource(m.probe)
 old='PF_InData in{};PF_OutData out{};'
 new='PF_InData in{};in.width=W;in.height=H;in.downsample_x={1,1};in.downsample_y={1,1};in.pixel_aspect_ratio={1,1};PF_OutData out{};'
 assert source.count(old)==1
 source=source.replace(old,new)
 marker='if(rc||!life||phase_bad||!pads||!unchanged||!request_unchanged||ih!=1)return false;'
 diagnostic='if(rc||!life||phase_bad||!pads||!unchanged||!request_unchanged||ih!=1){std::fprintf(stderr,"depth=%d smart=%d rc=%d life=%d phase=%d pads=%d unchanged=%d request=%d iterate=%d\\n",depth,smart,(int)rc,life,phase_bad,pads,unchanged,request_unchanged,ih);if(rc==0&&pads&&unchanged)std::fwrite(dst,1,sz,stdout);return false;}'
 assert source.count(marker)==1
 exec(source.replace(marker,diagnostic),m.__dict__)
 capture_prefix='header-'
 m.subprocess.run=capture
 try:
  observed,negative=m.probe(binary,inputs)
  mac['completed_header']={'negative':negative,'exact':observed==b''.join(outputs[d] for d in ['PF8','PF16','PF8','PF16','PF32'])}
 except Exception as error: mac['completed_header']={'error':str(error)}
 finally: m.subprocess.run=original_run
 expected=b''.join(outputs[d] for d in ['PF8','PF16','PF8','PF16','PF32'])
 observed=(S/'header-positive.stdout').read_bytes()
 mac['header_diagnostic_pixels']={'bytes':len(observed),'expected_bytes':len(expected),'exact':observed==expected,'sha256':hashlib.sha256(observed).hexdigest(),'first_mismatch':next((i for i,(a,b) in enumerate(zip(observed,expected)) if a!=b),None)}
(S/'mac.json').write_text(json.dumps(mac,indent=2)+'\n')
print({k:v for k,v in mac.items() if k!='build_command'})

import shutil
shutil.rmtree(build)
