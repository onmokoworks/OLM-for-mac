#!/usr/bin/env python3
"""Serial ticket-local baseline/candidate verification."""
import argparse, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P02j-directionalblur-geometry'
E=ROOT/'orchestra/reports/P02j-evidence'
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--units',action='store_true');p.add_argument('--fresh',action='store_true');a=p.parse_args()
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
if a.units:
 rows=[]
 for f in sorted((ROOT/'tests').glob('test_olmdirectionalblur*.py')):
  r=subprocess.run([sys.executable,'-m','unittest',str(f.relative_to(ROOT))],cwd=ROOT,capture_output=True,text=True)
  rows.append(dict(file=str(f.relative_to(ROOT)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
 (E/('units-'+a.label+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 print({c:sum(r['returncode']==c for r in rows) for c in set(r['returncode'] for r in rows)})
else:
 for mode,n,seed in ([('realistic',100,20261026)] if a.fresh else [('realistic',100,1),('default',300,1)]):
  name=f'{a.label}-{mode}-{seed}'
  cmd=[sys.executable,'tools/fuzz/run.py','--plugin','olmdirectionalblur','--geometry',mode,'--n',str(n),'--seed',str(seed),'--jobs','1','--shrink-attempts','0','--scratch',str(S/name),'--corpus',str(S/(name+'-corpus')),'--report',str(E/(name+'.json'))]
  with (S/(name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  print(name,r.returncode,flush=True)
