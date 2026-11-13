"""Three fixed serial replay pairs plus unchanged pre-optimization control."""
import argparse, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('triage',ROOT/'rust/plugins/olm-radial-blur/triage.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
p=argparse.ArgumentParser();p.add_argument('sources',type=Path,nargs='+');p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--repeats',type=int,default=3)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for source in a.sources:
 summary={'results':[{'directory':'.','status':'mismatched'}]} if (source/'case.json').exists() else json.loads((source/'summary.json').read_text())
 for r in summary['results']:
  directory=source/r['directory']
  authority=directory/'per-process-authority'
  if (authority/'diff.json').exists() and json.loads((authority/'diff.json').read_text()).get('status')=='mismatched':
   directory=authority
  elif r['status']!='mismatched':continue
  tag=source.name if r['directory']=='.' else source.name+'-'+r['directory']
  replay=a.out/tag;replay.mkdir()
  result=t.one(directory,replay,None,a.repeats)
  manifest=json.loads((directory/'case.json').read_text())
  ids={k:manifest[k] for k in ('reference','candidate','harness','tool')}
  ids['reference']=t.oracle.identity(a.before)
  control=a.out/(tag+'-before');control.mkdir()
  result['before_control']=t.oracle.run_case(control,manifest['case'],manifest['route'],ids,(),None,120)
  rows.append(result)
  print(result['source'],result['reference_unique'],result['candidate_unique'],result['has_exact_replay'],result['before_control']['status'],flush=True)
  t.oracle.write_json(a.out/'summary.json',{'results':rows})

qualified=all(r['reference_unique']>1 and r['candidate_unique']==1 and r['all_replays_succeeded'] and r['has_exact_replay'] and r['before_control']['status']=='exact' for r in rows)
t.oracle.write_json(a.out/'summary.json',{'results':rows,'qualified_original_instability':qualified})
raise SystemExit(0 if qualified else 1)
