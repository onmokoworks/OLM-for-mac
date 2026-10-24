#!/usr/bin/env python3
"""Serial P05b contract campaigns; logs and build files stay in ticket scratch."""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT/'orchestra/state/P05b-radialblur-rotation-performance'
STATE.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, TMPDIR=str(STATE), TMP=str(STATE), TEMP=str(STATE), OLM_TEST_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
commands = []
for label, flags in [
 ('default', ['--seed','1','--n','300']),
 ('realistic-1', ['--geometry','realistic','--seed','1','--n','100']),
 ('realistic-fresh', ['--geometry','realistic','--seed','20261025','--n','100']),
 ('odd-2026', ['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080','--seed','2026','--n','150']),
 ('odd-2027', ['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080','--seed','2027','--n','150']),
 ('replay-default', ['--replay','tests/fuzz_corpus/radialblur']),
 ('replay-realistic', ['--replay','tests/fuzz_corpus/radialblur_realistic_P02d','--geometry','realistic']),
 ('replay-P05b', ['--replay','tests/fuzz_corpus/radialblur/P05b-rotation-performance']),
 ('replay-odd', ['--replay','tests/fuzz_corpus/radialblur/T15b-odd-even-realistic','--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080']),
]:
 command=[sys.executable,'tools/fuzz/run.py','--plugin','radialblur','--jobs','1','--shrink-attempts','0','--scratch',str(STATE/label),'--corpus',str(STATE/(label+'-corpus')),'--report',str(STATE/(label+'.json'))]+flags
 with (STATE/(label+'.log')).open('w') as log:
  result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
 commands.append(dict(label=label,command=command,returncode=result.returncode))
 (STATE/'verify-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 print(label,result.returncode,flush=True)
