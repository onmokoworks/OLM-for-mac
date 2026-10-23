# Recovery of DistanceGradation seed 105 cases 50 and 123

The initial run raised `PermissionError` in `core.command` while killing a timed-out shrinking subprocess. This invokes unchanged runner functions with the same default worker, 10-second case timeout and 32-attempt/10-second shrinking. It does not modify production or framework code.

Write the following to `orchestra/state/S01-wide-mismatch-sweep/retry_dg.py` and run `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/state/S01-wide-mismatch-sweep/retry_dg.py > orchestra/state/S01-wide-mismatch-sweep/retry-dg105.log 2>&1`.

```python
import sys,os,time,json,tempfile,importlib
from pathlib import Path
root=Path.cwd();base=root/'orchestra/state/S01-wide-mismatch-sweep/retry-dg105';base.mkdir(exist_ok=True)
sys.dont_write_bytecode=True;sys.path.insert(0,str(root/'tools/fuzz'))
import run
sys.argv=['run.py','--plugin','olmdistancegradation','--n','300','--seed','105','--jobs','1','--scratch',str(base/'work'),'--report',str(base/'report.json'),'--corpus',str(base/'corpus'),'--corpus-max-bytes','64000000']
args=run.options();args.scratch.mkdir(parents=True,exist_ok=True);args.corpus.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch),PYTHONDONTWRITEBYTECODE='1');tempfile.tempdir=str(args.scratch)
start=time.monotonic();deadline=start+1800
with tempfile.TemporaryDirectory(dir=args.scratch) as td:
 adapter=importlib.import_module('adapters.olmdistancegradation').Adapter(args)
 provenance=run.prepare(adapter,Path(td),deadline,args.case_timeout)
 rows=[]
 for index in [50,123]:
  rows.append(run.run_one(adapter,105,index,Path(td),deadline,args,provenance));print('RETRIED',index,flush=True)
 d={'plugin':'olmdistancegradation','seed':105,'retry_indices':[50,123],'provenance':provenance,'cases':rows,'summary':run.summarize(rows)[0],'elapsed_seconds':time.monotonic()-start}
 args.report.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print('RESULT',d['summary'],flush=True)
```
