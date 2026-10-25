"""Candidate-only seed1/n300 baseline comparison; original oracle run is separate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'tools/fuzz'))
from adapters import olmkirakira as module
from geometry import sample
parser=argparse.ArgumentParser()
parser.add_argument('--baseline',default='31c7f256d7f19099d64136c39c93c93370737246')
args=parser.parse_args()
main=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
scratch=root/'orchestra/state/U02-kirakira-ramp-editor/render-unchanged'
scratch.mkdir(parents=True,exist_ok=True)
os.environ['TMPDIR']=str(scratch)
options=SimpleNamespace(max_size=256,case_timeout=10,main=main,
                        worker=Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker')
original_source=module.SOURCE
baseline_dir=scratch/'baseline';baseline_dir.mkdir(exist_ok=True)
body=subprocess.check_output(['git','show',args.baseline+':mac/OLMKiraKira/OLMKiraKira.cpp'],cwd=root,text=True)
body=body.replace('"../../','"'+str(root)+'/')
(baseline_dir/'OLMKiraKira.cpp').write_text(body)
for filename in ('OLMKiraKira.h','OLMKiraKira_Strings.cpp','OLMKiraKira_Strings.h'):
    link=baseline_dir/filename
    if not link.exists():link.symlink_to(original_source.parent/filename)
adapters=[]
deadline=time.monotonic()+1800
for name,source in [('baseline',baseline_dir/'OLMKiraKira.cpp'),('candidate',original_source)]:
    directory=scratch/name;directory.mkdir(exist_ok=True)
    module.SOURCE=source
    adapter=module.Adapter(options)
    adapter.env['TMPDIR']=str(scratch)
    adapter.binary,_=adapter.build(directory,deadline)
    adapters.append(adapter)
module.SOURCE=original_source
checks=0;differences=[]
for i in range(300):
    case=sample(adapters[1].generate(1,i),'default')
    for route in ('classic','smart'):
        results=[]
        for name,adapter in zip(('baseline','candidate'),adapters):
            directory=scratch/(name+'-case');directory.mkdir(exist_ok=True)
            metadata,raw,*_=adapter.candidate(case,directory,route,deadline)
            results.append({'metadata':metadata,'raw_sha256':hashlib.sha256(raw).hexdigest()})
        if results[0]!=results[1]: differences.append({'index':i,'route':route,'results':results})
        checks+=1
    if (i+1)%50==0:print(i+1,'cases',len(differences),'differences',flush=True)
report={'baseline':args.baseline,'cases':300,'route_checks':checks,'differences':differences}
(scratch/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print('RESULT',checks,'route checks;',len(differences),'differences')
sys.exit(bool(differences))
