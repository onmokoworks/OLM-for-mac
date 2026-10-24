#!/usr/bin/env python3
"""Rerun the 18 R05 commands sequentially, redirecting artifacts into R08 scratch."""
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R08-radial-fullsize-trace/legacy';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
# Run each original module with only artifact destinations redirected. Do not rewrite assertions.
CHILD='''import importlib,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]); out=Path(sys.argv[2]); name=sys.argv[3]
sys.path[:0]=[str(root),str(root/'tools/emulation')];tempfile.tempdir=str(out)
m=importlib.import_module(name)
for mod in list(sys.modules.values()):
 if not str(getattr(mod,'__file__','')).startswith(str(root/'tools/emulation')):continue
 for key in ('REPORT','DOC'):
  p=getattr(mod,key,None)
  if isinstance(p,Path):setattr(mod,key,out/p.name)
 # FIXTURE is an output for the typed base generators; full-size FIXTURE is read-only input.
 if hasattr(mod,'FIXTURE') and 'case0010_rotation_mac_production_planes' not in mod.__name__:
  dest=out/(mod.__name__+'-fixture');dest.mkdir(exist_ok=True);mod.FIXTURE=dest
raise SystemExit(m.main())
'''
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--index',type=int);args=ap.parse_args()
 results_path=S/('results.json' if args.index is None else f'results-{args.index}.json')
 rows=json.loads((ROOT/'orchestra/reports/R05-results.json').read_text())['fixtures'];ids={r['command_index'] for r in json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text())};results=[]
 for row in rows:
  if row['index'] not in ids or (args.index is not None and row['index']!=args.index):continue
  i=row['index'];out=S/str(i);out.mkdir(exist_ok=True);name=Path(row['command'][1]).stem
  command=[sys.executable,'-B','-c',CHILD,str(ROOT),str(out),name];start=time.monotonic()
  with (out/'command.log').open('w') as log:
   try:rc=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=1800).returncode
   except subprocess.TimeoutExpired:rc=124
  results.append(dict(index=i,module=name,returncode=rc,seconds=round(time.monotonic()-start,2),log=str((out/'command.log').relative_to(ROOT))))
  results_path.write_text(json.dumps(results,indent=2)+'\n');print(i,rc,flush=True)
if __name__=='__main__':main()
