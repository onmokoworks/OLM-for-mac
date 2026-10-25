"""Serial wide-size coverage and final retained-heavy RadialBlur acceptance."""
import json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/R10-reference-fast-split'
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
runs=[]
for plugin in ('olmdirectionalblur','olmblur','olmcolorkey','olmsmoother','olmkirakira','radialblur'):
 if plugin=='olmsmoother':runs.append(('smooth-small-coverage',plugin,['--small','400','--hd','0','--uhd','0']))
 runs.append(('wide-'+plugin,plugin,['--small','40','--hd','0','--uhd','0','--max-size','3840','--max-height','2160']))
runs.append(('final-radial-literal', 'radialblur', []))
rows=[]
for label,plugin,extra in runs:
 cmd=[sys.executable,'tools/perf/ref_vs_fast.py','--plugin',plugin,'--jobs','1','--scratch',str(S/label),*extra]
 with (S/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,command=cmd,returncode=r.returncode))
 (S/'finish-native-commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(label,r.returncode,flush=True)
 # Do not retry a failing differential or expand investigation automatically.
 if r.returncode:break
sys.exit(rows[-1]['returncode'] if rows else 0)
