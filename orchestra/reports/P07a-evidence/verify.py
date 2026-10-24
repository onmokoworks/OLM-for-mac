"""Sequential contract campaigns; retained oracle workers are never rebuilt."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P07a-parallel-helper-kirakira'
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
commands=[]
campaigns=[('default',['--seed','1','--n','300'])]
for g in ('realistic','realistic-v2'):
 for seed in ('1','20261025'):
  campaigns.append((g+'-'+seed,['--geometry',g,'--seed',seed,'--n','100']))
campaigns.append(('odd',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080','--seed','2026','--n','150']))
campaigns.extend([
 ('replay-default',['--replay','tests/fuzz_corpus/olmkirakira']),
 ('replay-gate-off',['--replay','tests/fuzz_corpus/olmkirakira_gate_off_T06']),
 ('replay-gate-reductions',['--replay','tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions']),
 ('replay-realistic',['--replay','tests/fuzz_corpus/olmkirakira_realistic_P02c','--geometry','realistic']),
 ('replay-odd',['--replay','tests/fuzz_corpus/olmkirakira/T15b-odd-even-realistic','--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080']),
])
for label,flags in campaigns:
 if '--replay-only' in sys.argv and not label.startswith('replay-'):continue
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin','olmkirakira','--jobs','1','--shrink-attempts','0','--scratch',str(S/label),'--corpus',str(S/(label+'-corpus')),'--report',str(S/(label+'.json'))]+flags
 with (S/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
 commands.append(dict(label=label,command=cmd,returncode=r.returncode))
 (S/('replay-commands.json' if '--replay-only' in sys.argv else 'verify-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
 print(label,r.returncode,flush=True)
 if r.returncode:break
