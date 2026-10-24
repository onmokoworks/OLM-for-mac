"""Run only when all candidate builds/campaigns are finished; always restore header."""
import os,subprocess,time
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07a-parallel-helper-kirakira';p=r/'core/kirakira_warp.h'
while (s/'correction-running').exists():time.sleep(1)
saved=p.read_bytes()
try:
 p.write_bytes(subprocess.check_output(['git','show','c101e2880a4b423e5e285c36baf120cbedd609b3:core/kirakira_warp.h'],cwd=r))
 with (s/'units-original-clean.log').open('w') as log:
  result=subprocess.run(['python3','-m','unittest','discover','-s','tests','-p','test_*kirakira*.py'],cwd=r,env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT)
 print('original unit returncode',result.returncode)
finally:p.write_bytes(saved)
