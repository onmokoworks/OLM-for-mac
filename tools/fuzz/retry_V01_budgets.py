#!/usr/bin/env python3
"""Retry only measured F53 10-second budget failures at a 60-second limit."""
import json,subprocess,sys
from verify_V01 import ROOT,STATE
for phase in ('default','realistic-v1'):
 for line in (STATE/(phase+'-oracle.jsonl')).open():
  row=json.loads(line)
  if row['oracle']['status']!='budget':continue
  plugin,index=row['identity'].split('/')
  cmd=[sys.executable,str(ROOT/'tools/fuzz/verify_V01.py'),'--state',str(STATE/'retry-60'),'--phase',phase,'--oracle','--jobs','1','--timeout','60','--plugins',plugin,'--indices',index]
  print('RETRY',phase,row['identity'],flush=True)
  subprocess.run(cmd,check=True)
