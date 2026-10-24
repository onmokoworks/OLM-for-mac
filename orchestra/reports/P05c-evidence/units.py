"""Serial plugin unittest modules, with scratch and concise result capture."""
import os,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
plugin,label=sys.argv[1:]
s=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance'/label
s.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,OLM_TEST_JOBS='1',TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
rows=[]
for path in sorted((ROOT/'tests').glob('test_'+plugin+'*.py')):
 with (s/(path.stem+'.log')).open('w') as log:
  r=subprocess.run([sys.executable,'-m','unittest',str(path.relative_to(ROOT))],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
 rows.append(dict(file=str(path.relative_to(ROOT)),returncode=r.returncode))
(s/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print('modules',len(rows),'failed',sum(r['returncode']!=0 for r in rows))
