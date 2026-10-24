#!/usr/bin/env python3
"""Profile slow full-size default and observed-heaviest corpus cells, serially."""
import collections,json,os,subprocess,time
from pathlib import Path
import ae_realism_audit as audit
ROOT=audit.ROOT
STATE=ROOT/'orchestra/state/P00b-ae-realism-audit-rerun'
CACHE=Path.home()/'.cache/olm-emu/P00b'
def main():
 rows=[json.loads(s) for s in (STATE/'matrix.jsonl').open()]
 manifest=json.loads((STATE/'matrix-manifest.json').read_text())
 dest=STATE/'profiles';dest.mkdir(exist_ok=True)
 env={k:v for k,v in os.environ.items() if not k.startswith(('OLM','DBLUR','COLORKEEP'))}
 env.update(TMPDIR=str(STATE),TMP=str(STATE),TEMP=str(STATE))
 selected=[]
 for plugin in audit.PLUGINS:
  for situation in ('full','4k'):
   for depth in (8,16,32):
    cells=[r for r in rows if (r['plugin'],r['situation'],r['depth'])==(plugin,situation,depth)]
    default=[r for r in cells if r['case']=='default']
    corpus=[r for r in cells if r['case']!='default' and r['status'] in ('ok','timeout')]
    def cost(r):return 60 if r['status']=='timeout' else r['result']['render_seconds']
    for label,rs in [('default',default),('heaviest',sorted(corpus,key=cost,reverse=True)[:1])]:
     if not rs:continue
     r=dict(rs[0]);r['selection']=label
     if label=='heaviest':r['timeout_ties']=[c['case'] for c in corpus if c['status']=='timeout']
     selected.append(r)
 (dest/'selected.json').write_text(json.dumps(selected,indent=2)+'\n')
 with (dest/'results.jsonl').open('w') as results:
  for r in selected:
   if r['status']!='timeout' and (r['status']!='ok' or r['result']['render_seconds']<=2):continue
   free=audit.memory()
   if free<30:raise RuntimeError(f'memory free {free}% <30%')
   plugin=r['plugin'];g=r['geometry'];identity=f'{plugin}-{r["selection"]}-{r["situation"]}-{r["depth"]}'
   params=[]
   if r['case']!='default':
    path=ROOT/manifest['samples'][plugin]['paths'][int(r['case'][6:])]
    params=json.loads(path.read_text())['case']['parameters']
   lines=[]
   for q in params:
    kind=q['kind'];v=q['value']
    if plugin=='olmkirakira' and kind=='a':kind='s';v*=65536
    lines.append(f'{q["slot"]} {kind} '+(' '.join(map(str,v)) if isinstance(v,list) else str(v))+'\n')
   config=dest/'parameters.txt';config.write_text(''.join(lines))
   name=audit.PLUGINS[plugin];exe=CACHE/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
   command=[str(CACHE/'plugin-host'),str(exe),str(g['w']),str(g['h']),str(r['depth']),*[str(g[k]) for k in ('dx','dy')],str(r['padding']),*[str(g[k]) for k in ('extent','roi','an','ad','expand')],str(config),str(int(plugin=='olmsmoother'))]
   start=time.monotonic();profile=dest/(identity+'.sample.txt');sample_rc=None
   with (dest/(identity+'.stdout')).open('w') as out,(dest/(identity+'.stderr')).open('w') as err:
    p=subprocess.Popen(command,stdout=out,stderr=err,env=env)
    try:
     try:p.wait(timeout=1)
     except subprocess.TimeoutExpired:
      with (dest/(identity+'.sample.log')).open('w') as log:
       sample_rc=subprocess.run(['sample',str(p.pid),'2','1','-file',str(profile)],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=10).returncode
     p.wait(timeout=max(0.01,60-(time.monotonic()-start)))
     status='completed'
    except subprocess.TimeoutExpired:
     status='timeout'
    finally:
     if p.poll() is None:p.kill()
     p.wait()
   record=dict(identity=identity,case=r['case'],profile=str(profile.relative_to(STATE)),sample_returncode=sample_rc,status=status,returncode=p.returncode,wall_seconds=time.monotonic()-start,memory_free=free)
   results.write(json.dumps(record)+'\n');results.flush();print(record,flush=True)
if __name__=='__main__':main()
