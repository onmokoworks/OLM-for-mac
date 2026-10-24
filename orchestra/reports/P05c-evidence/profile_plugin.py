"""Sample one plugin in the P00b host; wait for render completion."""
import pathlib,subprocess,os,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
s=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance'
label,name,cache,params,depth=sys.argv[1:]
e=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
cmd=[str(pathlib.Path.home()/'.cache/olm-emu/P00b/plugin-host'),str(s/cache/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name),'3840','2160',depth,'1','1','0','0','0','1','1','0',str(s/params/'parameters.txt'),str(int(name=='OLMSmoother'))]
with (s/(label+'.stdout')).open('w') as o,(s/(label+'.stderr')).open('w') as err,(s/(label+'.log')).open('w') as log:
 p=subprocess.Popen(cmd,env=e,stdout=o,stderr=err)
 try:
  time.sleep(.2)
  r=subprocess.run(['sample',str(p.pid),'2','1','-file',str(s/(label+'.txt'))],stdout=log,stderr=subprocess.STDOUT,env=e)
  print('sample',r.returncode,'host',p.wait(timeout=60))
 finally:
  if p.poll() is None:p.kill();p.wait()
