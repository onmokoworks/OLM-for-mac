"""Record F54b indirect-body watch limitations; these watches are unhookable."""
import argparse,gzip,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';E=R/'orchestra/reports/N03-evidence'
os.environ['TMPDIR']=str(S);sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import load_corpus,sha
from run import main_checkout
args=argparse.Namespace(max_size=256,case_timeout=120,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker',geometry='realistic-v2')
a=Adapter(args);deadline=time.monotonic()+1800;rows=[]
for p in sorted((R/'tests/fuzz_corpus/olmdistancegradation_N02').rglob('*.json')):
 a.max_size=json.loads(p.read_text())['max_size'];c,_=load_corpus(p,a)
 params={v['slot']:v['value'] for v in c['parameters']}
 if params[11]!=5:continue
 rva={0:'6bd600',2:'6bd9a0',2740:'6be1e0'}[params[12]]
 d=S/(p.stem+'-body');d.mkdir(exist_ok=True);trace=d/'trace.json'
 a.env.update(AEXCOMPAT_SMART_TRACE=str(trace),AEXCOMPAT_SMART_TRACE_WATCH=f'{rva},16,all')
 oracle,raw=a.oracle(c,d,deadline,'smart')
 row=dict(id=p.stem,rva=rva,oracle=oracle,raw_sha256=sha(raw))
 if trace.exists():
  t=json.loads(trace.read_text());row['unhookable']=t['trace_configuration']['unhookable_watches'];row['watches']=[dict(register=m['register'],address=m['before'].get('address'),hex=m['before'].get('hex')) for m in t['memory_witnesses']]
  with gzip.open(E/f'{p.stem}-body.json.gz','wt') as f:f.write(trace.read_text())
 rows.append(row);print(p.stem,oracle,'watches',len(row.get('watches',[])),flush=True)
(E/'public-dispatch.json').write_text(json.dumps(rows,indent=2)+'\n')
