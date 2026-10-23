#!/usr/bin/env python3
"""Native-arm64 vs pinned Rosetta pow. Bounded 4096-row stream, two processes."""
import argparse, hashlib, json, os
from pathlib import Path
import subprocess, time
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/F43c-ucrtmath-ms-pow'
DLL=Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
p=argparse.ArgumentParser()
p.add_argument('dataset',choices=['random','ranges','file'])
p.add_argument('--count',type=int,default=1_000_000)
p.add_argument('--inputs',type=Path)
p.add_argument('--tag')
a=p.parse_args()
assert a.count>0
STATE.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(STATE),PYTHONDONTWRITEBYTECODE='1')
build=STATE/'build';build.mkdir(exist_ok=True)
with (STATE/'build.log').open('w') as log:
 for arch,output,sources in [('arm64','native',['pow_native.c','pow.c']),('x86_64','compare',['pow_compare.c'])]:
  subprocess.run(['clang','-arch',arch,'-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-Wno-deprecated-declarations',*[str(ROOT/'ucrtmath/ms'/s) for s in sources],'-o',str(build/output)],env=env,stdout=log,stderr=log,check=True)
tag=a.tag or f'{a.dataset}-{a.count}'
start=time.monotonic()
with (STATE/(tag+'.json')).open('w') as out,(STATE/(tag+'.log')).open('w') as err,(a.inputs or Path(os.devnull)).open('rb') as src:
 prod=subprocess.Popen([str(build/'native'),a.dataset,str(a.count)],stdin=src,stdout=subprocess.PIPE,stderr=err,env=env)
 try:
  comp=subprocess.run([str(build/'compare'),str(DLL),'pow',str(a.count)],stdin=prod.stdout,stdout=out,stderr=err,env=env)
  prod.stdout.close();rc=prod.wait()
 finally:
  if prod.poll() is None:prod.kill();prod.wait()
result=json.loads((STATE/(tag+'.json')).read_text())
result['seconds']=round(time.monotonic()-start,3)
result['exits']=[rc,comp.returncode]
files=[DLL,*[ROOT/'ucrtmath/ms'/s for s in ['pow.c','pow_tables.h','pow_native.c','pow_compare.c','pow_check.py']],ROOT/'tools/ucrt_math_probe/rosetta/oracle.c',build/'native',build/'compare']
if a.inputs: files.append(a.inputs.resolve())
result['sha256']={str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
(STATE/(tag+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='sha256'}),flush=True)
raise SystemExit(int(bool(rc or comp.returncode)))
