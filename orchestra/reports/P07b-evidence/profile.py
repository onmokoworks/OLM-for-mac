"""Run under lockf -k ~/.cache/olm-emu/bench.lock."""
import os, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[3]
state=root/'orchestra/state/P07b-smoother2-threading'
cache=Path.home()/'.cache/olm-emu/P00b'
config=state/'default.txt'; config.write_text('')
env=dict(os.environ,TMPDIR=str(state),TMP=str(state),TEMP=str(state))
command=[str(cache/'plugin-host'),str(cache/'xcode/OLMSmoother2/products/OLMSmoother2.plugin/Contents/MacOS/OLMSmoother2'),'3840','2160','32','1','1','0','0','0','1','1','0',str(config),'0']
with (state/'profile-host.log').open('w') as log:
 p=subprocess.Popen(command,stdout=log,stderr=log,env=env)
 try:
  result=subprocess.run(['sample',str(p.pid),'1','1','-file',str(state/'before.sample.txt')],env=env)
  print('sample exit',result.returncode,'host exit',p.wait(timeout=30))
 finally:
  if p.poll() is None: p.kill(); p.wait()
