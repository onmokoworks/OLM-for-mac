"""Must run under lockf -k ~/.cache/olm-emu/bench.lock."""
import json,os,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07b-smoother2-threading';e=r/'orchestra/reports/P07b-evidence'
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
commands=[]
for name,cache in [('reference','P07b-smoother2-before'),('after','P07b-smoother2')]:
 cmd=[sys.executable,'tools/fuzz/ae_realism_audit.py','--phase','matrix','--situations','full','4k','--plugins','olmsmoother2','--cases','default','corpus03','corpus05','--jobs','1','--cache',str(Path.home()/'.cache/olm-emu'/cache),'--state',str(s/name)]
 with (s/(name+'.log')).open('w') as log:subprocess.run(cmd,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 commands.append(cmd);print(name,'completed',flush=True)
(e/'benchmark-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
subprocess.run([sys.executable,str(e/'concurrent.py')],cwd=r,env=env,check=True)
