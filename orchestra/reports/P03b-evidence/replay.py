"""Replay every corpus directory for one ticket plugin, serially."""
import json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P03b-nonfinite-hdr-admission'
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
name=sys.argv[1];rows=[]
for root in sorted((R/'tests/fuzz_corpus').glob(name+'*')):
 for directory in [root,*sorted(p for p in root.rglob('*') if p.is_dir())]:
  files=sorted(directory.glob('*.json'))
  if not files:continue
  d=json.loads(files[0].read_text());label=str(directory.relative_to(R/'tests/fuzz_corpus')).replace('/','-')
  output=S/('replay-'+label+'.json');log=S/('replay-'+label+'.log')
  cmd=[sys.executable,str(R/'tools/fuzz/run.py'),'--plugin',name,'--jobs','1','--replay',str(directory),'--max-size',str(d['max_size']),'--scratch',str(S/('replay-'+label)),'--report',str(output)]
  if d.get('geometry_sampler')=='realistic-v1':cmd+=['--geometry','realistic']
  if d.get('size_sampler'):cmd+=['--size-sampler',d['size_sampler']]
  if d.get('size_max_height'):cmd+=['--size-max-height',str(d['size_max_height'])]
  with log.open('w') as f:rc=subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT)
  result=json.loads(output.read_text()) if output.exists() else {}
  rows.append(dict(directory=str(directory.relative_to(R)),command=cmd,returncode=rc,completed=result.get('completed'),replay_matches_saved=result.get('replay_matches_saved')))
  print(rows[-1],flush=True)
(S/('replay-summary-'+name+'.json')).write_text(json.dumps(rows,indent=2))
assert all(r['returncode']==0 and r['replay_matches_saved'] for r in rows)
