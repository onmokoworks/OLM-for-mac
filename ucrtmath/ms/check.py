#!/usr/bin/env python3
"""F28 bounded stream comparison, two processes, both mode results per input."""
import argparse,json,pathlib,subprocess,time,hashlib,os
p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('functions',nargs='*',default=['sinf','cosf','log2f']);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];state=root/'orchestra/state/F42-ucrtmath-ms-float';state.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(state),PYTHONDONTWRITEBYTECODE='1')
with (state/'build.log').open('w') as log:subprocess.run(['sh',str(root/'ucrtmath/tests/build.sh'),str(state/'build')],env=env,stdout=log,stderr=log,check=True)
inputs=state/'targets.txt'
if not a.full:
 import random
 rng=random.Random(42)
 edges=[0,0x800000,0x39000000,0x3c000000,0x3f330000,0x3f490fdb,0x3f800000,0x48f42400,0x4b742400,0x4b800456,0x4f490fdb,0x7f800000]
 words={rng.getrandbits(32) for _ in range(100000)}
 for e in edges:
  for d in range(-128,129):
   for sign in [0,0x80000000]:words.add(((e+d)&0x7fffffff)|sign)
 with inputs.open('w') as f:
  for v in sorted(words):f.write(f'{v:08x} 0\n')
 count=len(words)
else:count=2**32
failed=False
for fn in a.functions:
 tag=('full-' if a.full else 'targeted-')+fn
 start=time.monotonic()
 with (state/(tag+'.json')).open('w') as out,(state/(tag+'.log')).open('w') as err,inputs.open('rb') if not a.full else open(os.devnull,'rb') as src:
  prod=subprocess.Popen([str(state/'build/native'),fn,'sweep' if a.full else 'file',str(count)],stdin=src,stdout=subprocess.PIPE,stderr=err)
  try:
   comp=subprocess.run([str(state/'build/compare'),str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'),fn,str(count)],stdin=prod.stdout,stdout=out,stderr=err)
   prod.stdout.close();rc=prod.wait()
  finally:
   if prod.poll() is None:prod.kill();prod.wait()
 result=json.loads((state/(tag+'.json')).read_text());print(tag,result,'seconds',round(time.monotonic()-start,3),flush=True)
 failed|=bool(rc or comp.returncode)
raise SystemExit(int(failed))
