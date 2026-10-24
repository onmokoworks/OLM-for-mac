#!/usr/bin/env python3
"""Serial F52c host qualification/campaign driver. Unqualified probes stay explicit."""
import argparse,importlib,json,time,shutil
from pathlib import Path
from types import SimpleNamespace
from core import evaluate,sha
from geometry import sample,require_host
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F52c-geometry-hosts-and-campaigns'
PLUGINS=('colorkeep','olmdistancegradation','olmkirakira','radialblur','olmtoondilate','olmsmoother2','olmsmoother','olmblur')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plugin',choices=PLUGINS,required=True);ap.add_argument('--n',type=int,default=100);ap.add_argument('--probe-unqualified',action='store_true');ap.add_argument('--geometry',choices=['realistic'],default='realistic');ap.add_argument('--jobs',type=int,choices=[1],default=1);args=ap.parse_args()
 s=S/'campaigns'/args.plugin;s.mkdir(parents=True,exist_ok=True);deadline=time.monotonic()+2400
 a=importlib.import_module('adapters.'+args.plugin).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
 a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
 if args.plugin=='olmsmoother':a.routes=('classic',)
 if not args.probe_unqualified:require_host(a,sample(a.generate(1,0),'realistic'))
 if (s/'build').exists():shutil.rmtree(s/'build')
 provenance=a.prepare(s,deadline)
 (s/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 with (s/'results.jsonl').open('w') as f:
  for i in range(args.n):
   c=sample(a.generate(1,i),'realistic');attr={};r=evaluate(a,c,s,deadline,attr)
   row=dict(case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),result=r,refusals=attr,qualified=not args.probe_unqualified)
   f.write(json.dumps(row)+'\n');f.flush()
   print(i,{k:v['status'] for k,v in r['routes'].items()},flush=True)
if __name__=='__main__':main()
