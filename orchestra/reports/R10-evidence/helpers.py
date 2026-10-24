"""Check exactly-once visits, rounding mode, and reference caller-thread execution."""
import json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/R10-reference-fast-split/helpers';S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S));rows=[]
with (S/'build.log').open('w') as log:
 for kind in ('fast','reference'):
  cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I'+str(R),str(Path(__file__).with_name('reference_helpers.cpp')),'-framework','Cocoa','-o',str(S/kind)]
  if kind=='reference':cmd.append('-DOLM_REFERENCE_BUILD=1')
  subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  result=subprocess.run([str(S/kind)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  rows.append(dict(kind=kind,command=cmd,returncode=result.returncode,parallel_rows_combinations=385,blur_cap_combinations=3))
(S/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('fast and reference helper assertions passed')
