"""Profile the final 4K heavy PF32 cell with macOS sample; retain process result."""
import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P05a-directionalblur-performance';E=R/'orchestra/reports/P05a-evidence'
b=S/'final2';env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
cmd=[str(b/'plugin-host'),str(b/'xcode/OLMDirectionalBlur/products/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur'),'3840','2160','32','1','1','0','0','0','1','1','0',str(S/'timing-final2/parameters.txt'),'0']
with (E/'final-profile.stdout').open('w') as out,(E/'final-profile.stderr').open('w') as err:
 p=subprocess.Popen(cmd,env=env,stdout=out,stderr=err)
 try:
  time.sleep(0.5)
  with (E/'final-profile.log').open('w') as log:r=subprocess.run(['sample',str(p.pid),'2','1','-file',str(E/'final.sample.txt')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=10)
  rc=p.wait(timeout=60)
 finally:
  if p.poll() is None:p.kill()
  p.wait()
(E/'profile.json').write_text(json.dumps(dict(command=cmd,sample_returncode=r.returncode,returncode=rc),indent=2)+'\n')
print('sample',r.returncode,'render',rc)
