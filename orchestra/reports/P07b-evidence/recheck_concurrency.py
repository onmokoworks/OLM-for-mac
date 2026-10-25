"""Locked repeated check of the noisy 256x256 boundary and 1080p concurrency."""
import json,os,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07b-smoother2-threading';rows=[]
for repeat in range(5):
 for w,h in ((256,256),(1920,1080)):
  for cap in ((1,2,8) if repeat%2==0 else (8,2,1)):
   cmd=[str(s/'concurrent'),str(w),str(h),'50' if w==256 else '3',str(s/'threads/case-0-1/params.txt')]
   p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=60,env=dict(os.environ,OLM_PARALLEL_MAX=str(cap),TMPDIR=str(s),TMP=str(s),TEMP=str(s)))
   rows.append(dict(json.loads(p.stdout),cap=cap,repeat=repeat))
   (s/'concurrent-recheck.json').write_text(json.dumps(rows,indent=2)+'\n')
   print(w,cap,repeat,flush=True)
