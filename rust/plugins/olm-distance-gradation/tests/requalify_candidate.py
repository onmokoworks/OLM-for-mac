"""Re-render a final candidate against immutable, hash-recorded oracle witnesses.

Uses the shared oracle process ownership, decoding and bit comparator unchanged.
No reference failure is counted. Never overwrites the source campaign.
"""
import argparse,json,sys,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/oracle'))
import olm_oracle as o
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
src=a.source.resolve();out=a.out.resolve();out.mkdir(exist_ok=False)
old=json.loads((src/'summary.json').read_text());assert old['complete']
for key in ['reference','harness','tool']:
 assert o.sha256(old[key]['path'])==old[key]['sha256'],key+' identity changed'
candidate=o.identity(a.candidate)
summary={k:v for k,v in old.items() if k not in ['results','routes','complete','exit_code','candidate']}
summary.update(candidate=candidate,source_summary=o.identity(src/'summary.json'),comparison_method='final candidate render versus retained original output',complete=False,results=[],routes={})
def run(row):
 result={'case':row['case'],'route':row['route'],'status':row['status'],'directory':row['directory'],'source_directory':str(src/row['directory'])}
 base=src/row['directory'];manifest=json.loads((base/'case.json').read_text())
 for relative,digest in manifest['assets'].items():assert o.sha256(base/relative)==digest
 refprocess=json.loads((base/'reference.process.json').read_text());result['processes']={'reference':row['processes']['reference']}
 result['reference_process']=o.identity(base/'reference.process.json')
 if row['status'].startswith('reference_'):return result
 directory=out/row['directory'];directory.mkdir();(directory/'requests').mkdir()
 shutil.copy2(base/'input.png',directory/'input.png');shutil.copy2(base/'requests/reference.json',directory/'requests/candidate.json')
 argv=list(refprocess['argv']);argv[3]=candidate['path'];argv[4]=str(directory/'input.png');argv[5]=str(directory/'candidate.png');argv[6]=str(directory/'requests/candidate.json')
 depth=int(row['route'][5:]);reference=base/'reference.png'
 result['reference_outputs']=[o.identity(reference)]
 if depth!=8:result['reference_outputs'].append(o.identity(reference.with_suffix('.rgba16le' if depth==16 else '.rgba32f-le')))
 proc=o.run_process(argv,300,{'AEXCOMPAT_FRAME_DEADLINE_MS':'300000'});o.write_json(directory/'candidate.process.json',proc)
 result['processes']['candidate']={k:v for k,v in proc.items() if k not in ['argv','stdout','stderr']}
 result['processes']['candidate']['ok']=False
 try:
  if proc['timeout'] or proc['returncode']!=0:raise RuntimeError('candidate harness failed')
  comparison=o.compare_samples(o.load_output(reference,depth),o.load_output(directory/'candidate.png',depth),depth)
  result.update(comparison=comparison,status='exact' if comparison['exact'] else 'mismatched');result['processes']['candidate']['ok']=True
 except Exception as e:result.update(status='candidate_failure',error=repr(e))
 for identity in result['reference_outputs']:assert o.sha256(identity['path'])==identity['sha256']
 o.write_json(directory/'case.json',{**manifest,'candidate':candidate,'source_manifest':o.identity(base/'case.json'),'reference_outputs':result['reference_outputs']})
 o.write_json(directory/'diff.json',result)
 return result
app={r:None for r in old['routes']}
with ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(run,r) for r in old['results']]
 try:
  for f in as_completed(futures):
   summary['results'].append(f.result());summary['routes']=o.summarize(summary['results'],app);o.write_json(out/'summary.json',summary)
   if len(summary['results'])%30==0:print('requalified',len(summary['results']), '/',len(futures),flush=True)
 except KeyboardInterrupt:
  o.CANCELLED.set()
  for f in futures:f.cancel()
  raise
summary['results'].sort(key=lambda r:(r['case'],r['route']));summary['complete']=True;summary['exit_code']=o.exit_code(summary);o.write_json(out/'summary.json',summary);o.print_table(summary)
sys.exit(summary['exit_code'])
