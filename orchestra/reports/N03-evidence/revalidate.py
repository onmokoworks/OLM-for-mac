"""Revalidate final Mac bytes against each campaign's captured original hashes.

No original result is regenerated, tolerated, or replaced. Assert each complete
input hash and parameter/geometry record before comparing both route hashes.
"""
import argparse,json,os,sys,tempfile,time
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';E=R/'orchestra/reports/N03-evidence'
os.environ['TMPDIR']=str(S);sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import sha
from geometry import sample
from run import main_checkout
args=argparse.Namespace(max_size=1920,size_sampler='odd-even-v1',size_max_height=1080,case_timeout=120,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker',geometry='realistic-v2')
a=Adapter(args);reports=[];deadline=time.monotonic()+7200
with tempfile.TemporaryDirectory(dir=S) as td:
 hd=Path(td);provenance=a.prepare(hd,deadline)
 for path in sorted(p for p in S.glob('final-*.json') if not p.stem.endswith('-revalidated'))+[S/'default.json']:
  d=json.loads(path.read_text());rows=[];counts=Counter()
  a.max_size=d['max_size'];a.size_sampler=d['size_sampler'];a.size_max_height=d['size_max_height']
  for row in d['cases']:
   c=a.generate(d['seed'],row['index'])
   if path.stem!='default':
    for p in c['parameters']:
     if p['slot']==11:p['value']=5
   c=sample(c,{'realistic-v1':'realistic'}.get(row.get('geometry_sampler','default'),row.get('geometry_sampler','default')))
   assert sha(c['pixels'])==row['input_sha256'],(path.name,row['index'])
   for key in ('parameters','geometry','full_geometry','downsample','request_rect','input_padding','output_padding'):
    assert c.get(key)==row.get(key),(path.name,row['index'],key)
   routes={}
   for route in ('classic','smart'):
    result,raw,guards=a.candidate(c,hd,route,deadline)
    oracle=row['result']['oracles'][route];digest=sha(raw)
    state='uncompared' if oracle['status']!='ok' else 'refusal' if result['status']=='refusal' else 'exact' if result['status']=='ok' and digest==oracle['raw_sha256'] else 'mismatch'
    counts[route+'_'+state]+=1
    routes[route]=dict(status=state,candidate=result,raw_sha256=digest,original_sha256=oracle.get('raw_sha256'),original_status=oracle['status'],previous_status=row['result']['routes'][route]['status'])
   rows.append(dict(index=row['index'],depth=c['depth'],input_sha256=row['input_sha256'],routes=routes))
  report=dict(campaign=path.name,captured_report_sha256=sha(path.read_bytes()),provenance=provenance,completed=len(rows),counts=dict(counts),cases=rows)
  (S/(path.stem+'-revalidated.json')).write_text(json.dumps(report,indent=2)+'\n');reports.append({k:v for k,v in report.items() if k not in ('provenance','cases')})
  print(path.stem,len(rows),dict(counts),flush=True)
(E/'revalidated-summary.json').write_text(json.dumps(reports,indent=2)+'\n')

assert len(reports)==10 and all(r['counts'].get('smart_mismatch',0)==0 and r['counts'].get('smart_refusal',0)==0 for r in reports)
