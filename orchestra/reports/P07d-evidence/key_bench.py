"""Hold the shared benchmark lock across the matrix and concurrent-render run."""
from pathlib import Path
import os,subprocess,sys
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading'
e=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
if '--locked' not in sys.argv:
 subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),sys.executable,__file__,'--locked'],env=e,check=True)
else:
 with (s/'key-after.log').open('w') as log:
  subprocess.run([sys.executable,str(r/'tools/fuzz/ae_realism_audit.py'),'--phase','matrix','--plugins','olmcolorkey','--cases','default','corpus05','--situations','full','4k','--jobs','1','--cache',str(s/'key-bundle-after'),'--state',str(s/'key-after')],env=e,stdout=log,stderr=subprocess.STDOUT,check=True)
 with (s/'key-concurrent.log').open('w') as log:subprocess.run([str(s/'key-concurrent')],env=e,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
