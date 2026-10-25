"""Run under lockf; profile the registered sequential Smoother bundle."""
import os, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P07c-smoother-threading'
C=Path.home()/'.cache/olm-emu/P05c-smooth'
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
for depth in (8,16):
    with (S/f'profile-{depth}.stdout').open('w') as out, (S/f'profile-{depth}.stderr').open('w') as err:
        cmd=[str(C/'plugin-host'),str(C/'xcode/OLMSmoother/products/OLMSmoother.plugin/Contents/MacOS/OLMSmoother'),'3840','2160',str(depth),'1','1','0','0','0','1','1','0',str(S/'before/parameters.txt'),'1']
        p=subprocess.Popen(cmd,env=env,stdout=out,stderr=err)
        try:
            time.sleep(.2)
            r=subprocess.run(['sample',str(p.pid),'2','1','-file',str(S/f'profile-{depth}.txt')],env=env)
            print('depth',depth,'sample',r.returncode,'host',p.wait(timeout=60),flush=True)
        finally:
            if p.poll() is None:p.kill();p.wait()
