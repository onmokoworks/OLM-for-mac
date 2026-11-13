"""Isolate one retained case by directional ray; uses shared owned-job runner."""
import argparse,copy,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/oracle'))
import olm_oracle as o

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--case',type=int,required=True);p.add_argument('--candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 j=json.loads((a.run/'summary.json').read_text());case=json.loads((a.run/'cases.json').read_text())[a.case]
 identities={k:j[k] for k in ['harness','reference','candidate','tool']}
 if a.candidate:identities['candidate']={'path':str(a.candidate.resolve()),'sha256':o.sha256(a.candidate)}
 a.out=a.out.resolve();a.out.mkdir();cases=[]
 for label,slots in [('all',[10,16,22,28,34]),('vertical',[10]),('horizontal',[16]),('diagonal',[22]),('diagonal2',[28]),('highlight',[34]),('no-highlight',[10,16,22,28])]:
  c=copy.deepcopy(case);c['index']=len(cases);c['label']=label
  for v in c['assignments']:
   if v['slot'] in [10,16,22,28,34] and v['slot'] not in slots:v['value']=0
  cases.append(c)
 o.write_json(a.out/'cases.json',cases)
 def run(c):
  r=o.run_case(a.out,c,'smart32',identities,[],None,120);print(c['label'],r['status'],r.get('comparison',{}),flush=True);return r
 with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,cases))
 o.write_json(a.out/'results.json',results)
if __name__=='__main__':main()
