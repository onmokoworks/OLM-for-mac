"""Render a new candidate against hash-bound, already-rendered original evidence.

No reference process is simulated. Each row explicitly identifies the retained
original run, validates its input/request manifest, and records output/log hashes.
Only the new candidate is rendered. Execution, job cleanup, loading, comparison,
inventory and summaries use the unchanged shared oracle.
"""
import argparse,copy,json,shutil,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/oracle'))
import olm_oracle as o

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
 baseline=args.baseline.resolve();old=read(baseline/'summary.json');assert old['complete']
 for key in ['harness','reference','tool']:assert o.sha256(old[key]['path'])==old[key]['sha256'],key
 assert not old['inventory_diff']
 identities={k:old[k] for k in ['harness','reference','tool']};identities['candidate']=o.identity(args.candidate)
 out=args.out.resolve();out.mkdir(exist_ok=False)
 inventory={side:o.inspect(Path(identities['harness']['path']),Path(identities[side]['path']),120) for side in ['reference','candidate']}
 diff=o.inventory_diff(inventory['reference'],inventory['candidate']);assert not diff,diff
 for side,inv in inventory.items():o.write_json(out/f'{side}.inventory.json',inv)
 cases=read(baseline/'cases.json');o.write_json(out/'cases.json',cases)
 summary={**identities,'schema_version':1,'seed':old['seed'],'cases':len(cases),'sizes':old['sizes'],'downsample':old['downsample'],'jobs':3,'timeout_seconds':120,
  'render_environment_overrides':o.frame_deadline_environment(120),'inventory_diff':diff,'complete':False,'results':[],
  'reference_evidence':{'summary':str(baseline/'summary.json'),'summary_sha256':o.sha256(baseline/'summary.json'),'mode':'retained actual original render; no reference relaunch'},
  'revalidation_tool':o.identity(__file__)}
 def run(prior):
  assert prior['processes']['reference']['ok']
  source=baseline/prior['directory'];manifest=read(source/'case.json');route=prior['route'];depth,command=o.ROUTES[route]
  assert manifest['reference']['sha256']==identities['reference']['sha256']
  for relative,sha in manifest['assets'].items():
   asset=(source/relative).resolve();assert asset.is_relative_to(source) and o.sha256(asset)==sha,relative
  assert read(source/'requests/reference.json')==read(source/'requests/candidate.json')
  reference_process=read(source/'reference.process.json');assert reference_process['returncode']==0 and not reference_process['timeout']
  directory=out/prior['directory'];directory.mkdir();(directory/'requests').mkdir()
  shutil.copyfile(source/'input.png',directory/'input.png');shutil.copyfile(source/'requests/candidate.json',directory/'requests/candidate.json')
  result=o.run_process([identities['harness']['path'],'--headless',command,identities['candidate']['path'],directory/'input.png',directory/'candidate.png',directory/'requests/candidate.json'],120,env_overrides=o.frame_deadline_environment(120))
  o.write_json(directory/'candidate.process.json',result)
  reference=source/'reference.png';raw=reference if depth==8 else reference.with_suffix('.rgba16le' if depth==16 else '.rgba32f-le')
  ref_evidence={'reused_actual_render':True,'ok':True,'directory':str(source),'process_sha256':o.sha256(source/'reference.process.json'),'output_path':str(raw),'output_sha256':o.sha256(raw),'input_sha256':o.sha256(source/'input.png'),'request_sha256':o.sha256(source/'requests/reference.json')}
  row={'case':prior['case'],'route':route,'directory':directory.name,'processes':{'reference':ref_evidence,'candidate':{k:v for k,v in result.items() if k not in ['stdout','stderr','argv']}}}
  row['processes']['candidate']['ok']=result['returncode']==0 and not result['timeout']
  if row['processes']['candidate']['ok']:
   row['comparison']=o.compare_samples(o.load_output(reference,depth),o.load_output(directory/'candidate.png',depth),depth);row['status']='exact' if row['comparison']['exact'] else 'mismatched'
  else:row['status']='candidate_failure'
  o.write_json(directory/'case.json',{**identities,'case':manifest['case'],'route':route,'reference_evidence':ref_evidence,'input_sha256':o.sha256(directory/'input.png'),'request_sha256':o.sha256(directory/'requests/candidate.json')})
  o.write_json(directory/'diff.json',row);return row
 applicability={r:None for r in old['routes']}
 with ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(run,row) for row in old['results']]
  try:
   for future in as_completed(futures):
    summary['results'].append(future.result());summary['routes']=o.summarize(summary['results'],applicability);o.write_json(out/'summary.json',summary)
    if len(summary['results'])%30==0:print(f"completed {len(summary['results'])}/{len(futures)} candidate rerenders",flush=True)
  except BaseException:
   o.CANCELLED.set()
   for f in futures:f.cancel()
   raise
 summary['results'].sort(key=lambda r:(r['case'],r['route']));summary['complete']=True;summary['routes']=o.summarize(summary['results'],applicability);summary['exit_code']=o.exit_code(summary)
 o.write_json(out/'summary.json',summary);o.print_table(summary);return summary['exit_code']
if __name__=='__main__':raise SystemExit(main())
