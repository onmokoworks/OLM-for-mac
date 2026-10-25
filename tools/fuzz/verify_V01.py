#!/usr/bin/env python3
"""Serial, resumable Universal bundle comparison with retained F53 AEX oracle."""
import argparse, collections, copy, fcntl, hashlib, importlib, json, os, re, shutil, struct, subprocess, time
from pathlib import Path
from types import SimpleNamespace
from ae_realism_audit import PLUGINS, memory
from adapters.public import geometry_environment
from geometry import sample
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/V01-universal-x86-arm-equality'
CACHE=Path.home()/'.cache/olm-emu/worker-V01-universal'
MAIN=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
THREADED={'olmblur','olmcolorkey','olmdirectionalblur','olmdistancegradation','olmkirakira','olmsmoother2','radialblur'}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def prepare():
 CACHE.mkdir(parents=True,exist_ok=True); STATE.mkdir(parents=True,exist_ok=True)
 record=dict(name=CACHE.name,source_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),hosts={},bundles={},commands=[],sources={})
 env=dict(os.environ,TMPDIR=str(STATE),TMP=str(STATE),TEMP=str(STATE))
 assert memory()>=30
 for name,source in [('full','F51-plugin-host.cpp'),('geometry','F52c-plugin-host.cpp')]:
  src=ROOT/'tools/emulation/aexcompat_patches'/source
  cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-arch','arm64','-arch','x86_64','-mmacosx-version-min=11.0','-Wno-pragma-pack','-I'+str(ROOT/'Headers'),'-I'+str(ROOT/'Headers/SP'),str(src),'-o',str(CACHE/name)]
  with (STATE/(name+'-build.log')).open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  record['commands'].append(cmd);record['hosts'][name]=digest(CACHE/name)
 for p in [ROOT/'tools/emulation/aexcompat_patches'/n for n in ('F51-plugin-host.cpp','F52c-plugin-host.cpp','F47d-native-bridge.cpp')]+list((ROOT/'tools/fuzz/harnesses').glob('*.hpp')):
  record['sources'][str(p.relative_to(ROOT))]=digest(p)
 for name in PLUGINS.values():
  rel=Path('xcode')/name/'products'/(name+'.plugin')
  shutil.copytree(STATE/'bundles'/rel,CACHE/rel,dirs_exist_ok=True)
  record['bundles'][name]=digest(CACHE/rel/'Contents/MacOS'/name)
 record.update(worker_path=str(CACHE/'geometry'),worker_sha256=record['hosts']['geometry'],bundles_path=str(CACHE),capability='V01 Universal plugin-only hosts and HEAD bundles; no AEX oracle',recipe='python3 tools/fuzz/verify_V01.py --prepare')
 (CACHE/'build.json').write_text(json.dumps(record,indent=2)+'\n')
 shutil.copy2(CACHE/'build.json',STATE/'build.json')
 shutil.copy2(STATE/'bundles/bundle-builds.json',STATE/'bundle-builds.json')
 with (CACHE.parent/'.index.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=CACHE.parent/'INDEX.json';d=json.loads(p.read_text());d['links']=[r for r in d['links'] if r['name']!=CACHE.name]+[record]
  q=CACHE/'index.new';q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
 shutil.rmtree(STATE/'bundles/xcode')
 print('retained hosts and 10 bundles',flush=True)
def cases(a,phase,n):
 if phase=='heavy':
  # Use each depth/size's actually measured P00b slowest corpus preset.
  import gzip
  rows=[json.loads(l) for l in gzip.open(ROOT/'orchestra/reports/P00b-evidence/matrix.jsonl.gz','rt')]
  manifest=json.loads((ROOT/'orchestra/reports/P00b-evidence/matrix-manifest.json').read_text())['samples'][a.name]
  corpus=[(ROOT/p,json.loads((ROOT/p).read_text())) for p in manifest['paths']]
  assert [digest(p) for p,_ in corpus]==manifest['sha256']
  for size,wh in [('full',[1920,1080]),('4k',[3840,2160])]:
   for depth in (8,16,32):
    choices=[r for r in rows if r['plugin']==a.name and r['situation']==size and r['depth']==depth and r['case']!='default']
    r=max(choices,key=lambda r:(r['status']=='timeout',r.get('result',{}).get('render_seconds',0),r.get('wall_seconds',0)))
    ix=int(r['case'].replace('corpus','')); path,saved=corpus[ix]
    c=a.generate(909,0);c.update(geometry=wh,depth=depth,input_padding=0,output_padding=0,parameters=copy.deepcopy(saved['case']['parameters']),parameter_source=str(path.relative_to(ROOT)),preset=r['case'])
    # Opaque deterministic P00b spatial pattern, normalized to AE integer/float scale.
    w,h=wh; buf=bytearray()
    for y in range(256):
     for x in range(w):
      values=[255,*[(17*x+29*y+53*k)%256 for k in range(1,4)]]
      buf.extend(bytes(values) if depth==8 else struct.pack('<4H',*[v*32768//255 for v in values]) if depth==16 else struct.pack('<4f',*[v/255 for v in values]))
    c['pixels']=(bytes(buf)*(h//256+1))[:w*h*depth//8*4]
    yield f'{size}/{depth}',c
 else:
  a.size_sampler='odd-even-v1' if phase=='odd-even-v1' else 'default'
  a.max_size=256;a.size_max_height=None
  if phase=='odd-even-v1':
   d=json.loads((ROOT/f'orchestra/reports/T15b-evidence/{a.name}-summary.json').read_text());a.max_size=d['maximum'];a.size_max_height=d['height_maximum']
  for i in range(n if n is not None else 50 if phase=='odd-even-v1' else 100):
   yield str(i),sample(a.generate(2026 if phase=='odd-even-v1' else 909,i),'realistic-v1' if phase=='odd-even-v1' else phase)
def render(a,c,arch,cap,d,timeout):
 d.mkdir(exist_ok=True);decl=getattr(a,'declarations',None) or a.binding['parameters'];types=[0]+[p['param_type'] for p in decl]
 (d/'decl').write_text(' '.join(map(str,[len(types),*types])))
 (d/'params').write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in c['parameters']))
 env={k:v for k,v in os.environ.items() if not k.startswith(('OLM','DBLUR','COLORKEEP'))};env.update(TMPDIR=str(d),TMP=str(d),TEMP=str(d),OLM_PARALLEL_MAX=str(cap),OLM_REFUSAL_TRACE=str(d/'refusals'))
 (d/'refusals').unlink(missing_ok=True)
 if a.name=='olmkirakira':env['OLM_NATIVE_PARAMETER_PROFILE']='kirakira-default-ramps'
 geometry_environment(c,d,env)
 name=PLUGINS[a.name];exe=CACHE/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
 cmd=['/usr/bin/arch','-'+arch,str(CACHE/('geometry' if c.get('geometry_sampler') else 'full')),str(exe),*map(str,c['geometry']),str(c['depth']),str(c.get('rowbytes_padding',c['input_padding'])),str(int(a.name!='olmsmoother')),str(d/'decl'),str(d/'params')]
 inp=d/'input';out=d/'output';err=d/'stderr';inp.write_bytes(c['pixels'])
 with inp.open('rb') as i,out.open('wb') as o,err.open('wb') as e:
  p=subprocess.Popen(cmd,env=env,stdin=i,stdout=o,stderr=e)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:p.kill();p.wait();return {'status':'timeout'},out
 trace=err.read_text();result={'status':'host_error','returncode':p.returncode}
 if p.returncode or out.stat().st_size<4 or 'unsupported/invalid callback:' in trace or 'F47c counters' not in trace:
  result['diagnostic']=trace[-1600:];return result,out
 with out.open('rb') as f:code=struct.unpack('<i',f.read(4))[0]
 rect=[0,0,*c['geometry']]
 for line in trace.splitlines():
  if line.startswith('GEOMETRY '):rect=list(map(int,line.split()[1:]))
 result.update(status='refusal' if code else 'ok',error=code,rect=rect,sha256=digest(out),bytes=out.stat().st_size-4,refusals=(d/'refusals').read_text().splitlines() if (d/'refusals').exists() else [])
 if not code and result['bytes']!=(rect[2]-rect[0])*(rect[3]-rect[1])*c['depth']//8*4:result['status']='host_error'
 return result,out
def first_difference(x,y,skip=0):
 offset=0
 with x.open('rb') as a,y.open('rb') as b:
  a.seek(skip);b.seek(skip)
  while True:
   aa,bb=a.read(1048576),b.read(1048576)
   if aa!=bb:return offset+next((i for i,(l,r) in enumerate(zip(aa,bb)) if l!=r),min(len(aa),len(bb)))
   if not aa:return None
   offset+=len(aa)
def main():
 global STATE
 ap=argparse.ArgumentParser();ap.add_argument('--state',type=Path,default=STATE);ap.add_argument('--prepare',action='store_true');ap.add_argument('--phase',choices=('default','realistic-v1','realistic-v2','odd-even-v1','heavy'),default='default');ap.add_argument('--plugins',nargs='+',default=list(PLUGINS),choices=PLUGINS);ap.add_argument('--n',type=int);ap.add_argument('--indices',nargs='+',type=int);ap.add_argument('--jobs',type=int,choices=(1,),default=1);ap.add_argument('--oracle',action='store_true');ap.add_argument('--timeout',type=float,default=60);args=ap.parse_args()
 STATE=args.state.resolve()
 if not STATE.is_relative_to(ROOT/'orchestra/state'):ap.error('state must be inside this worktree orchestra/state')
 STATE.mkdir(parents=True,exist_ok=True)
 if args.prepare:prepare();return
 phase=args.phase+('-oracle' if args.oracle else '');rows=STATE/(phase+'.jsonl');seen={json.loads(l)['identity'] for l in rows.read_text().splitlines()} if rows.exists() else set()
 for plugin in args.plugins:
  free=memory();assert free>=30,free
  print(plugin,phase,'memory_free',free,flush=True)
  d=STATE/('render-'+phase);d.mkdir(exist_ok=True)
  a=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=MAIN,worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',max_size=256,case_timeout=args.timeout))
  a.env.update(TMPDIR=str(d),TMP=str(d),TEMP=str(d))
  (STATE/(phase+'-'+plugin+'-provenance.json')).write_text(json.dumps(dict(worker_path=str(a.worker),worker_sha256=digest(a.worker),aex_path=str(a.aex),aex_sha256=digest(a.aex),timeout=args.timeout,host_build=digest(CACHE/'build.json')),indent=2)+'\n')
  for sequence,(identity,c) in enumerate(cases(a,args.phase,args.n)):
   if sequence%25==0:
    free=memory()
    with (STATE/(phase+'-memory.jsonl')).open('a') as f:f.write(json.dumps(dict(plugin=plugin,index=sequence,free_percent=free))+'\n')
    assert free>=30,free
   key=plugin+'/'+identity
   if args.indices is not None and identity not in set(map(str,args.indices)):continue
   if key in seen:continue
   row=dict(identity=key,plugin=plugin,phase=args.phase,case={k:v for k,v in c.items() if k!='pixels'},input_sha256=hashlib.sha256(c['pixels']).hexdigest(),results=[])
   if args.oracle:
    x,xp=render(a,c,'x86_64',1,d/'x86_64',args.timeout)
    original,raw=a.oracle(c,d,time.monotonic()+args.timeout,'classic' if plugin=='olmsmoother' else 'smart')
    row.update(x86_64=x,oracle=original)
    if x['status']=='ok' and original['status']=='ok':
     with xp.open('rb') as f:f.read(4);candidate_raw=f.read()
     equal=candidate_raw==raw
     row['first_byte']=next((i for i,(x,y) in enumerate(zip(candidate_raw,raw)) if x!=y),min(len(candidate_raw),len(raw)) if len(candidate_raw)!=len(raw) else None)
     row['verdict']='exact' if equal and x['rect']==original.get('output_rect',[0,0,*c['geometry']]) else 'difference'
     row['oracle_sha256']=hashlib.sha256(raw).hexdigest()
    else:row['verdict']='non_render'
   else:
    row['verdict']='equal';baseline=None
    for cap in ([1,2,8] if plugin in THREADED else [1]):
     x,xp=render(a,c,'arm64',cap,d/'arm64',args.timeout);y,yp=render(a,c,'x86_64',cap,d/'x86_64',args.timeout)
     diff=first_difference(xp,yp) if x['status'] in ('ok','refusal') and y['status'] in ('ok','refusal') else None
     equal=x==y and x['status'] in ('ok','refusal') and diff is None
     row['results'].append(dict(cap=cap,arm64=x,x86_64=y,first_byte=None if diff is None else diff-4,equal=equal))
     if not equal:row['verdict']='difference' if x['status'] in ('ok','refusal') and y['status'] in ('ok','refusal') else 'host_error'
     if baseline is not None and x!=baseline:row['thread_cap_difference']=True
     baseline=x
   if row['verdict']=='difference':
    failure=STATE/'failures'/phase/plugin
    if not failure.exists():
     failure.mkdir(parents=True);(failure/'case.json').write_text(json.dumps(row,indent=2)+'\n');(failure/'input.raw').write_bytes(c['pixels'])
     shutil.copy2(xp,failure/'first-output.bin')
     if args.oracle:(failure/'oracle.raw').write_bytes(raw)
     else:shutil.copy2(yp,failure/'second-output.bin')
   with rows.open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
   if row['verdict']=='difference':print('DIFFERENCE',key,flush=True)
  print(plugin,'complete',flush=True)
 print('TOTAL',dict(collections.Counter(json.loads(l)['verdict'] for l in rows.read_text().splitlines())),flush=True)
if __name__=='__main__':main()
