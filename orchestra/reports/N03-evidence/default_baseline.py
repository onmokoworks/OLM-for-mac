"""Run baseline Mac routes against the final default campaign's original hashes."""
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';os.environ['TMPDIR']=str(S)
sys.path.insert(0,str(R/'tools/fuzz'))
import adapters.olmdistancegradation as dg
from core import sha
from run import main_checkout
report=json.loads((S/'default.json').read_text());source=dg.SOURCE
args=argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker')
rows=[]
with tempfile.TemporaryDirectory(dir=S) as td:
 p=Path(td);cpp=p/source.name
 code=subprocess.check_output(['git','show','41369ff07d1a785849597fe57f9b294cc0b3deb0:mac/OLMDistanceGradation/OLMDistanceGradation.cpp']).decode().replace('"../../core/','"'+str(R/'core')+'/').replace('"../../ucrtmath/','"'+str(R/'ucrtmath')+'/')
 code=code.replace('#include "OLMDistanceGradation.h"','#include "'+str(source.with_suffix('.h'))+'"')
 cpp.write_text(code);cpp.with_suffix('.h').write_text(source.with_suffix('.h').read_text());
 a=dg.Adapter(args);deadline=time.monotonic()+1800;a.binary,_=a.build(p,deadline)
 host=p/"host.cpp";host.write_text(host.read_text().replace(str(source),str(cpp)))
 a.compile(["clang++","-std=c++17","-O2","-fno-fast-math","-ffp-contract=off","-I",p/"geometry-shim",host,dg.FIELDGEN,"-o",a.binary],deadline)
 for row in report['cases']:
  c=a.generate(1,row['index']);assert sha(c['pixels'])==row['input_sha256']
  for route in ('classic','smart'):
   status,raw,_=a.candidate(c,p,route,deadline)
   oracle=row['result']['oracles'][route]
   baseline_exact=status['status']=='ok' and oracle.get('raw_sha256')==sha(raw)
   final=row['result']['routes'][route]['status']
   rows.append(dict(index=row['index'],route=route,baseline_exact=baseline_exact,final_status=final,regression=baseline_exact and final!='exact'))
(S/'default-baseline.json').write_text(json.dumps(rows,indent=2)+'\n')
print('routes',len(rows),'baseline exact',sum(r['baseline_exact'] for r in rows),'exact-to-non-exact',sum(r['regression'] for r in rows))
assert not any(r['regression'] for r in rows)
