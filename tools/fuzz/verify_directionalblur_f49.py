#!/usr/bin/env python3
"""O2/ASan/UBSan public Smart agreement for the three F49 n300 campaigns."""
import json,os,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from adapters.olmdirectionalblur import ROOT
from core import sha
from verify_directionalblur_c02 import Build
S=ROOT/'orchestra/state/F49-dblur-nonfinite-pf32'
def main():
 S.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1');tempfile.tempdir=str(S)
 args=SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=30,worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker')
 deadline=time.monotonic()+1800;report={'builds':[],'cases':[]}
 with tempfile.TemporaryDirectory(prefix='san_',dir=S) as tmp:
  d=Path(tmp);adapters=[Build(args),Build(args,sanitizer=True)]
  for i,a in enumerate(adapters):
   path=d/str(i);path.mkdir();report['builds'].append(a.prepare(path,deadline))
  for seed in (1,104,219):
   for index in range(300):
    case=adapters[0].generate(seed,index)
    with tempfile.TemporaryDirectory(prefix='case_',dir=d) as directory:
     result,raw,guards=adapters[0].candidate(case,Path(directory),'smart',deadline)
     sanitized,sanraw,sanguards=adapters[1].candidate(case,Path(directory),'smart',deadline)
     assert result==sanitized and raw==sanraw and guards==sanguards,(seed,index,result,sanitized)
     assert result['status']=='ok',(seed,index,result)
     report['cases'].append(dict(seed=seed,index=index,input_sha256=sha(case['pixels']),output_sha256=sha(raw),sanitizer_same=True))
   (S/'sanitizer.json').write_text(json.dumps(report,indent=2)+'\n');print('verified',seed,300,flush=True)
  report['commands']=[a.commands for a in adapters]
 (S/'sanitizer.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS',len(report['cases']))
if __name__=='__main__':main()
