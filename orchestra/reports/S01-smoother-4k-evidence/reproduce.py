import os, sys, json, hashlib, subprocess, time, struct, gzip
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
STATE=ROOT/'orchestra/state/S01-smoother-4k-two-sample-diff'
STATE.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(STATE),TMP=str(STATE),TEMP=str(STATE))
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmsmoother import Adapter
EVIDENCE=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
pixels=gzip.decompress((EVIDENCE/'input.argb.gz').read_bytes())
ae=gzip.decompress((EVIDENCE/'ae.argb.gz').read_bytes())
manifest=json.loads((EVIDENCE/'manifest.json').read_text())
assert sha(pixels)==manifest['input']['raw_sha256']
assert sha(ae)==manifest['ae']['raw_sha256']
(STATE/'input.argb').write_bytes(pixels)
results={'input_sha256':sha(pixels),'ae_sha256':sha(ae),'runs':{}}
def record(name,raw,**extra):
    a=np.frombuffer(ae,dtype=np.uint8); b=np.frombuffer(raw,dtype=np.uint8)
    idx=np.flatnonzero(a!=b)
    results['runs'][name]=dict(sha256=sha(raw),differing_samples=len(idx),mismatches=[dict(x=int(i//4%3840),y=int(i//4//3840),channel='ARGB'[i%4],ae=int(a[i]),host=int(b[i])) for i in idx[:10]],**extra)
    (STATE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(name,results['runs'][name],flush=True)
params=[{'slot':1,'kind':'b','value':0},{'slot':2,'kind':'c','value':[255]*4},{'slot':3,'kind':'i','value':6}]
case=dict(geometry=[3840,2160],depth=8,input_padding=0,output_padding=0,pixels=pixels,parameters=params)
schema=STATE/'schema'; schema.write_text('4\n0\n4\n5\n1\n')
config=STATE/'params'; config.write_text('1 b 0\n2 c 255 255 255 255\n3 i 6\n')
bundle=Path('/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMSmoother.plugin/Contents/MacOS/OLMSmoother')
assert sha(bundle.read_bytes())=='47d02cbb8325bd7885e95e89201615436de05eacb3c34a62fdfcc2dfc2e17b41', 'Installed bundle changed; use the recorded bundle'
for arch in ('arm64','x86_64'):
 for parallel in ('default','1'):
    name=arch+'-'+parallel
    argv=['arch','-'+arch,str(Path.home()/'.cache/olm-emu/worker-V01-universal/full'),str(bundle),'3840','2160','8','0','0',str(schema),str(config)]
    env=dict(os.environ); env.pop('OLM_PARALLEL_MAX',None)
    if parallel=='1': env['OLM_PARALLEL_MAX']='1'
    out=STATE/(name+'.out')
    with (STATE/'input.argb').open('rb') as i,out.open('wb') as o,(STATE/(name+'.log')).open('wb') as e:
        subprocess.run(argv,stdin=i,stdout=o,stderr=e,env=env,check=True,timeout=120)
    raw=out.read_bytes(); assert struct.unpack('<i',raw[:4])[0]==0
    record(name,raw[4:],command=argv,bundle_sha256=sha(bundle.read_bytes()))
options=SimpleNamespace(plugin='olmsmoother',main=ROOT.parent.parent,worker=Path.home()/'.cache/olm-emu/worker-F54/aex-guest-worker',max_size=4096,case_timeout=180,reference_build=True)
adapter=Adapter(options)
d=STATE/'reference'; d.mkdir(exist_ok=True)
adapter.prepare(d,time.monotonic()+180)
status,raw,guards=adapter.candidate(case,d,'classic',time.monotonic()+180)
assert status['status']=='ok',status
record('R10-reference',raw,status=status)
d=STATE/'oracle'; d.mkdir(exist_ok=True)
adapter.session_observed=lambda out,err: ((d/'stdout').write_bytes(out),(d/'stderr').write_bytes(err))
status,raw=adapter.oracle(case,d,time.monotonic()+180,'classic')
if status['status']=='ok': record('F54-original',raw,status=status)
else:
 results['runs']['F54-original']=status
 (STATE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(status,flush=True)
