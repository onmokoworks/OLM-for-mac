#!/usr/bin/env python3
"""Isolated retained-fixture probe across first-parent DistanceGradation changes."""
import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; S=ROOT/'orchestra/state/I02-integration-finish'; BASE='d027fd4d'
paths=['core','mac/OLMDistanceGradation','tools/emulation/dg_renderbits_real_harness_20260716','tools/emulation/dg_pf32_effectmain_fixture_harness_20260805.cpp','tools/emulation/test_olmdistancegradation_pf32_effectmain_fixture_20260805.py','refs/fixtures/olmdistancegradation_pf32_owner_17x11_20260805','refs/fixtures/olmdistancegradation_pf32_owner_17x11_controlled_source_20260805']
results=[]
def probe(rev):
 rev=subprocess.check_output(['git','rev-parse',rev],cwd=ROOT,text=True).strip(); checkout=S/'distance-checkout'; shutil.rmtree(checkout,ignore_errors=True); checkout.mkdir()
 with (S/f'distance-{rev[:8]}.log').open('w') as log:
  archive=subprocess.Popen(['git','archive',rev,*paths],cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
  extract=subprocess.run(['tar','-xf','-','-C',str(checkout)],stdin=archive.stdout,stdout=log,stderr=log); archive.stdout.close()
  assert archive.wait()==0 and extract.returncode==0
  env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1')
  rc=subprocess.run([sys.executable,'-B',str(checkout/paths[4])],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  results.append(dict(revision=rev,exit=rc,log=f'distance-{rev[:8]}.log'))
 shutil.rmtree(checkout)
 (S/'distance-bisect.json').write_text(json.dumps(results,indent=2)+'\n')
 print(rev,rc,flush=True); return rc
paths.append('tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h')
old=probe(BASE); new=probe('HEAD')
if old==0 and new!=0:
 changes=subprocess.check_output(['git','log','--first-parent','--reverse','--format=%H',BASE+'..HEAD','--',*paths[:2]],cwd=ROOT,text=True).splitlines()
 lo,hi=-1,len(changes)-1
 while hi-lo>1:
  mid=(lo+hi)//2
  if probe(changes[mid])==0: lo=mid
  else: hi=mid
 probe(changes[hi]+'^1'); probe(changes[hi]); print('FIRST_BAD',changes[hi],flush=True)
else:
 print('NO_GOOD_BASELINE' if old else 'NO_CURRENT_FAILURE',flush=True)
