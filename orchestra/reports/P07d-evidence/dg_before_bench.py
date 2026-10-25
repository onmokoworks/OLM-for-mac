"""Measure and profile the unchanged DistanceGradation bundle under one lock."""
from pathlib import Path
import os,sys,subprocess,time
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading'
e=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
if '--locked' not in sys.argv:
 subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),sys.executable,__file__,'--locked'],env=e,check=True)
else:
 cache=s/'dg-bundle-before'
 with (s/'dg-before.log').open('w') as log:
  subprocess.run([sys.executable,str(r/'tools/fuzz/ae_realism_audit.py'),'--phase','matrix','--plugins','olmdistancegradation','--cases','default','corpus02','--situations','full','4k','--jobs','1','--cache',str(cache),'--state',str(s/'dg-before')],env=e,stdout=log,stderr=subprocess.STDOUT,check=True)
 config=s/'dg-profile-parameters.txt';config.write_text('')
 cmd=[str(cache/'plugin-host'),str(cache/'xcode/OLMDistanceGradation/products/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation'),'3840','2160','16','1','1','0','0','0','1','1','0',str(config),'0']
 with (s/'dg-profile.stdout').open('w') as o,(s/'dg-profile.stderr').open('w') as er,(s/'dg-profile.log').open('w') as log:
  p=subprocess.Popen(cmd,env=e,stdout=o,stderr=er)
  try:
   time.sleep(.01)
   sample=subprocess.run(['sample',str(p.pid),'1','1','-file',str(s/'dg-profile-before.txt')],env=e,stdout=log,stderr=subprocess.STDOUT)
   print('sample',sample.returncode,'host',p.wait(timeout=60),flush=True)
  finally:
   if p.poll() is None:p.kill();p.wait()
