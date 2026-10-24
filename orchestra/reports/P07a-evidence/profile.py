import os,subprocess
from pathlib import Path
s=Path(__file__).resolve().parents[3]/'orchestra/state/P07a-parallel-helper-kirakira'
s.mkdir(parents=True,exist_ok=True)
(s/'empty.txt').write_text('')
c=Path.home()/'.cache/olm-emu/P00b'
env=dict(os.environ,TMPDIR=str(s))
with (s/'profile-host.log').open('w') as log:
 p=subprocess.Popen([str(c/'plugin-host'),str(c/'xcode/OLMKiraKira/products/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira'),'3840','2160','32','1','1','0','0','0','1','1','0',str(s/'empty.txt'),'0'],stdout=log,stderr=log,env=env)
 try:
  with (s/'sample.log').open('w') as out:subprocess.run(['sample',str(p.pid),'1','1','-file',str(s/'before.sample.txt')],stdout=out,stderr=out,env=env)
 finally:p.wait()
