"""Stream full-frame raw Smart renders to disk for original/1/2/8 comparisons.
Run under lockf -k ~/.cache/olm-emu/bench.lock.
"""
import hashlib,json,os,struct,subprocess,sys,time,types
from pathlib import Path
r=Path(__file__).resolve().parents[3];sys.path.insert(0,str(r/'tools/fuzz'))
sys.dont_write_bytecode=True
from adapters.olmkirakira import Adapter
s=r/'orchestra/state/P07a-parallel-helper-kirakira';d=s/'frame-hashes';d.mkdir(exist_ok=True)
a=Adapter(types.SimpleNamespace(max_size=256,case_timeout=60,main=(r.parent.parent if r.parent.name=='worktrees' else r),worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
manifest=json.loads((s/'before/matrix-manifest.json').read_text())
heavy=json.loads((r/manifest['samples']['olmkirakira']['paths'][5]).read_text())['case']['parameters']
rows=[]
for w,h in [(1920,1080),(3840,2160)]:
 for depth in (8,16,32):
  fmt,top={8:('B',255),16:('H',32768),32:('f',1.)}[depth]
  with (d/'input.raw').open('wb') as f:
   for y in range(h):
    row=bytearray()
    for x in range(w):row.extend(struct.pack('<4'+fmt,*([top]+[int((x*k+y)%251)*top//250 if depth!=32 else ((x*k+y)%251)/250 for k in (1,3,7)])))
    f.write(row)
  for label in ('default','corpus05'):
   params=a.defaults(w,h)
   if label=='corpus05':params=heavy
   case=dict(geometry=[w,h],depth=depth,parameters=params,input_padding=0,output_padding=0)
   expected=None
   for cap in ('original','1','2','8'):
    a.binary=s/('original/mac' if cap=='original' else 'threads/normal/mac')
    cmd,_=a.candidate_command(dict(case,pixels=b''),d,'smart')
    env=dict(a.env,TMPDIR=str(d),OLM_PARALLEL_MAX='1' if cap=='original' else cap)
    with (d/'input.raw').open('rb') as inp,(d/'output.raw').open('wb') as out,(d/'stderr.log').open('w') as err:
     start=time.monotonic();p=subprocess.run(list(map(str,cmd)),stdin=inp,stdout=out,stderr=err,env=env,timeout=60);seconds=time.monotonic()-start
    assert p.returncode==0 and 'ERROR 0\n' in (d/'stderr.log').read_text()
    assert (d/'output.raw').stat().st_size==w*h*depth//8*4
    with (d/'output.raw').open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    if expected is None:expected=sha
    assert sha==expected,(label,w,h,depth,cap,sha,expected)
    rows.append(dict(case=label,width=w,height=h,depth=depth,cap=cap,sha256=sha,wall_seconds=seconds))
    (d/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
   print(label,w,h,depth,'original/1/2/8 exact',flush=True)
(d/'input.raw').unlink();(d/'output.raw').unlink()
