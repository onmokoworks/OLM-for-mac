#!/usr/bin/env python3
"""Two bounded processes, real Unicorn import hooks versus pinned F27c UCRT."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F30-oracle-worker-ucrtmath'
W=Path.home()/'.cache/olm-emu/worker-F30-ucrtmath'
DLL=Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
subprocess.run(['clang','-arch','x86_64','-O2','-Wno-deprecated-declarations',str(Path(__file__).with_name('compare_F30.c')),'-o',str(S/'compare')],env=env,check=True)
results=[]
for mode in [1,0]:
 for lib in ['api-ms-win-crt-math-l1-1-0.dll','ucrtbase.dll']:
  for fn in ['expf','atan2f','powf']:
   with (S/'shim.log').open('a') as log:
    stream=S/'shim-stream.bin'
    with stream.open('wb') as out:
     p=subprocess.run([str(W/'f30_import_probe'),fn,lib,'1000000'],env=dict(env,OLM_UCRT_FMA=str(mode)),stdout=out,stderr=log)
    assert p.returncode==0,(lib,fn,mode,p.returncode)
    with stream.open('rb') as inp:
     q=subprocess.run(['/usr/bin/arch','-x86_64',str(S/'compare'),str(DLL),fn,str(mode),'1000000'],stdin=inp,stdout=subprocess.PIPE,stderr=log,text=True)
    stream.unlink()
   assert q.returncode==0,(lib,fn,mode,q.returncode,q.stdout)
   row=json.loads(q.stdout);row['library']=lib;results.append(row)
   (S/'shim-results.json').write_text(json.dumps(results,indent=2)+'\n')
   print(lib,fn,mode,row['count'],row['mismatches'],flush=True)
