#!/usr/bin/env python3
"""P00b driver plus a bounded sample profile; no oracle is built or modified."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--situations',nargs='+',default=['eighth','quarter','full','4k']);args=ap.parse_args()
state=ROOT/'orchestra/state/P05b-radialblur-rotation-performance'/args.label;state.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(state),TMP=str(state),TEMP=str(state))
cmd=[sys.executable,'tools/fuzz/ae_realism_audit.py','--phase','matrix','--plugins','radialblur','--cases','corpus05','--situations',*args.situations,'--cache',str(args.cache),'--state',str(state),'--jobs','1','--timeout','60']
with (state/'driver.log').open('w') as log:result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
print('driver returncode',result.returncode)
for line in (state/'matrix.jsonl').read_text().splitlines():
 r=json.loads(line);print(r['situation'],r['depth'],r['status'],r.get('result',{}).get('render_seconds'))
# Use the exact driver command for the completed eighth/PF8 cell. Profiling is
# intentionally stopped after the sample; this is never counted as a timing.
rows=[json.loads(line) for line in (state/'matrix.jsonl').read_text().splitlines()]
r=next((r for r in rows if r['situation']=='eighth' and r['depth']==8),None)
if r:
 manifest=json.loads((state/'matrix-manifest.json').read_text())
 config=state/'parameters.txt'
 params=json.loads((ROOT/manifest['samples']['radialblur']['paths'][5]).read_text())['case']['parameters']
 config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in params))
 exe=args.cache/'xcode/OLMRadialBlur/products/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur'
 command=[str(args.cache/'plugin-host'),str(exe),'1920','1080','8','8','8','0','0','0','1','1','0',str(config),'0']
 with (state/'profile.stdout').open('w') as out,(state/'profile.stderr').open('w') as err:
  proc=subprocess.Popen(command,env=env,stdout=out,stderr=err)
  try:
   time.sleep(1)
   with (state/'sample.log').open('w') as log:
    subprocess.run(['sample',str(proc.pid),'2','1','-file',str(state/'profile.sample.txt')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=15)
  finally:
   if proc.poll() is None:proc.kill()
   proc.wait()
 print('profile intentionally stopped after sample')
