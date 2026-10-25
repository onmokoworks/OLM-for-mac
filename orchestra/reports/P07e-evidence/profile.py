"""Run under lockf; profile retained P05b rotation without completing a timing."""
import json, os, subprocess, time
from pathlib import Path
root=Path(__file__).resolve().parents[3]
state=root/'orchestra/state/P07e-radialblur-rotation-parallel'
cache=Path.home()/'.cache/olm-emu/P05b-radialblur-simd'
env=dict(os.environ,TMPDIR=str(state),TMP=str(state),TEMP=str(state))
case=json.loads((root/'tests/fuzz_corpus/radialblur/C45_seed1_case000108.json').read_text())['case']
config=state/'parameters.txt'
config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
cmd=[str(cache/'plugin-host'),str(cache/'xcode/OLMRadialBlur/products/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur'),'1920','1080','8','8','8','0','0','0','1','1','0',str(config),'0']
with (state/'profile.stdout').open('w') as out,(state/'profile.stderr').open('w') as err:
 p=subprocess.Popen(cmd,env=env,stdout=out,stderr=err)
 try:
  subprocess.run(['sample',str(p.pid),'24','1','-file',str(state/'baseline.sample.txt')],env=env,check=True)
 finally:
  if p.poll() is None:p.kill()
  p.wait()
print('Profile completed; render intentionally stopped, no timing result')
