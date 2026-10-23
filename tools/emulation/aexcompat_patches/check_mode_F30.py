#!/usr/bin/env python3
"""Check unset mode matches explicit FMA and malformed modes fail closed."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F30-oracle-worker-ucrtmath'
probe=Path.home()/'.cache/olm-emu/worker-F30-ucrtmath/f30_import_probe'
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S));env.pop('OLM_UCRT_FMA',None)
rows=[]
for fn in ['expf','atan2f','powf']:
 outputs=[]
 for mode in [None,'1','invalid']:
  selected=env if mode is None else dict(env,OLM_UCRT_FMA=mode)
  with (S/'mode.log').open('ab') as err:
   run=subprocess.run([str(probe),fn,'ucrtbase.dll','1024'],env=selected,stdout=subprocess.PIPE,stderr=err)
  if mode=='invalid':
   assert run.returncode!=0 and not run.stdout
   rows.append({'function':fn,'default_equals_fma1':True,'count':1024,'raw_sha256':hashlib.sha256(outputs[0]).hexdigest(),'invalid_exit':run.returncode})
  else:
   assert run.returncode==0 and len(run.stdout)==16384
   outputs.append(run.stdout)
   if len(outputs)==2:assert outputs[0]==outputs[1]
Path(__file__).with_name('F30-evidence').joinpath('mode-results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS default=FMA1 for three functions; invalid values rejected')
