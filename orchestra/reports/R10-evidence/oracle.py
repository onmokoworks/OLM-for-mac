"""Serial reference n100 / fast n300 AEX campaigns for one plugin."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'orchestra/state/R10-reference-fast-split'
p=argparse.ArgumentParser();p.add_argument('--plugin',required=True);p.add_argument('--label',required=True);a=p.parse_args()
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
commands=[]
for kind,n in [('reference',100),('fast',300)]:
 label=('' if kind=='reference' else 'fast-')+'oracle-'+a.label
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin',a.plugin,'--n',str(n),'--seed','1','--jobs','1','--shrink-attempts','0','--scratch',str(S/label),'--corpus',str(S/(label+'-corpus')),'--report',str(S/(label+'.json'))]
 if kind=='reference':cmd.append('--reference-build')
 with (S/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
 commands.append(dict(command=cmd,returncode=r.returncode))
 (S/('oracle-'+a.label+'-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
 print(label,r.returncode,flush=True)
