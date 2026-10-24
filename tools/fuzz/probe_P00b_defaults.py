#!/usr/bin/env python3
"""Original no-override DistanceGradation default versus real bundle; no rebuild."""
import hashlib,json,os,struct,subprocess,time
from pathlib import Path
from types import SimpleNamespace
import ae_realism_audit as audit
from adapters.olmdistancegradation import Adapter
ROOT=audit.ROOT;STATE=ROOT/'orchestra/state/P00b-ae-realism-audit-rerun/default-probe'
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
WORKER=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker'
def main():
 STATE.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(STATE),TMP=str(STATE),TEMP=str(STATE))
 a=Adapter(SimpleNamespace(max_size=64,case_timeout=60,main=MAIN,worker=WORKER))
 out={'worker_sha256':audit.sha(WORKER),'aex_sha256':audit.sha(a.aex),'rows':[]}
 for depth in (8,16,32):
  if audit.memory()<30:raise RuntimeError('memory free <30%')
  d=STATE/str(depth);d.mkdir(exist_ok=True);w,h=32,24
  pixels=bytearray()
  for y in range(h):
   for x in range(w):
    for c in range(4):
     v=255 if c==0 else (x*17+y*29+c*53)%256
     pixels+=bytes([v]) if depth==8 else struct.pack('<H',v*32768//255) if depth==16 else struct.pack('<f',v/255)
  case=dict(geometry=[w,h],depth=depth,pixels=bytes(pixels),parameters=[])
  original,raw=a.oracle(case,d,time.monotonic()+60,route='smart')
  config=d/'params.txt';config.write_text('')
  cache=Path.home()/'.cache/olm-emu/P00b';exe=cache/'xcode/OLMDistanceGradation/products/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation'
  cmd=[str(cache/'plugin-host'),str(exe),str(w),str(h),str(depth),'1','1','0','0','0','1','1','0',str(config),'0']
  trace=d/'refusal.txt';env=dict(os.environ,OLM_REFUSAL_TRACE=str(trace))
  with (d/'stdout').open('w') as stdout,(d/'stderr').open('w') as stderr:
   r=subprocess.run(cmd,env=env,stdout=stdout,stderr=stderr,timeout=60)
  row=dict(depth=depth,original=original,original_bytes=len(raw) if raw is not None else None,original_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,mac_returncode=r.returncode,mac=json.loads((d/'stdout').read_text()),tags=trace.read_text().splitlines() if trace.exists() else [])
  out['rows'].append(row); print(row,flush=True)
  (ROOT/'orchestra/reports/P00b-evidence/original-default-probe.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
