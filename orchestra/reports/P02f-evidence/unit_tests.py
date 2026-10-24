"""Run plugin unit modules serially, with all temporary files in ticket scratch."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];label=sys.argv[1]
s=ROOT/'orchestra/state/P02f-smoother2-geometry'/label;s.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,OLM_TEST_JOBS='1',TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
rows=[]
for path in sorted((ROOT/'tests').glob('test_olmsmoother2*.py')):
 log=s/(path.stem+'.log')
 with log.open('w') as f:
  r=subprocess.run([sys.executable,'-m','unittest',str(path.relative_to(ROOT))],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(file=str(path.relative_to(ROOT)),returncode=r.returncode,tail=log.read_text()[-5000:]))
 print(path.name,r.returncode,flush=True)
(s/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
