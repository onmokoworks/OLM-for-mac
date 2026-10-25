import json, os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
state=root/'orchestra/state/P07b-smoother2-threading'/sys.argv[1]
state.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(state),TMP=str(state),TEMP=str(state),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
results=[]
for path in sorted((root/'tests').glob('test_*smoother2*.py')):
 with (state/(path.stem+'.log')).open('w') as log:
  p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',path.name],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 results.append(dict(test=path.name,exit=p.returncode))
 (state/'results.json').write_text(json.dumps(results,indent=2))
 print(path.name,p.returncode,flush=True)
