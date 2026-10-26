"""Bind every retained-corpus replay's original hashes to the final Mac build."""
import argparse,json,os,sys,tempfile,time
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';E=R/'orchestra/reports/N03-evidence'
os.environ['TMPDIR']=str(S);sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import load_corpus,sha
from run import main_checkout
args=argparse.Namespace(max_size=1920,size_sampler='odd-even-v1',size_max_height=1080,case_timeout=120,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker',geometry='realistic-v2')
a=Adapter(args);deadline=time.monotonic()+3600;rows=[];counts=Counter();transitions=Counter()
with tempfile.TemporaryDirectory(dir=S) as td:
 hd=Path(td);provenance=a.prepare(hd,deadline)
 for path in sorted(S.glob('replay-[0-9]*.json')):
  d=json.loads(path.read_text())
  for row in d['replays']:
   saved_path=Path(row['path']);saved=json.loads(saved_path.read_text());a.max_size=saved['max_size'];c,_=load_corpus(saved_path,a)
   routes={}
   for route in ('classic','smart'):
    status,raw,guards=a.candidate(c,hd,route,deadline);digest=sha(raw);oracle=row['result']['oracles'][route]
    state='uncompared' if oracle['status']!='ok' else 'refusal' if status['status']=='refusal' else 'exact' if status['status']=='ok' and digest==oracle['raw_sha256'] else 'mismatch'
    old=saved['result']['routes'].get(route,{})
    counts[route+'_'+state]+=1;transitions[route+':'+old.get('status','unrecorded')+'->'+state]+=1
    routes[route]=dict(status=state,candidate=status,original_status=oracle['status'],original_sha256=oracle.get('raw_sha256'),raw_sha256=digest,saved_status=old.get('status'),saved_hash=old.get('raw_sha256'))
   rows.append(dict(path=str(saved_path.resolve().relative_to(R)),input_sha256=sha(c['pixels']),routes=routes))
report=dict(provenance=provenance,completed=len(rows),counts=dict(counts),transitions=dict(transitions),cases=rows)
(S/'replay-final.json').write_text(json.dumps(report,indent=2)+'\n')
print('completed',len(rows),'counts',dict(counts),'transitions',dict(transitions))

assert len(rows)==461 and counts['smart_exact']==461
assert all(not (r['routes'][route]['saved_status']=='exact' and r['routes'][route]['status']!='exact') for r in rows for route in ('classic','smart'))
