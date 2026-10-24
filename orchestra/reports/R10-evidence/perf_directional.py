"""Spot-check the already-built fast Universal bundle under the shared lock."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'orchestra/state/R10-reference-fast-split'
cache=S/'release-directional';host=cache/'plugin-host'
if not host.exists():host.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
command=['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),sys.executable,'tools/fuzz/ae_realism_audit.py','--phase','matrix','--cache',str(cache),'--state',str(S/'timing-directional'),'--plugins','olmdirectionalblur','--cases','default','corpus09','--situations','full','--jobs','1','--timeout','60']
with (S/'timing-directional.log').open('w') as log:subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
