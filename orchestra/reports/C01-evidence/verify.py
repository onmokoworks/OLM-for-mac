"""C01 serial AEX differential: retained witness, nightly siblings, nonfinite, regressions."""
import base64, collections, copy, json, os, random, re, shutil, struct, subprocess, sys, time, zlib
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmcolorkey import Adapter, SOURCE
from core import evaluate, load_corpus, save_corpus, sha
from geometry import sample, require_host
from run import main_checkout
S=R/'orchestra/state/C01-colorkey-pf32-nan-passthrough'; E=R/'orchestra/reports/C01-evidence'
S.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
mode=sys.argv[1]; D=S/mode;D.mkdir(exist_ok=True)
def adapter(worker='worker-F46-pow',baseline=False):
 a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path(worker) if str(worker).startswith('/') else Path.home()/'.cache/olm-emu'/worker/'aex-guest-worker',max_size=256,case_timeout=10))
 a.routes=('smart',);a.oracle_routes={'smart':'smart'}
 if baseline:
  source=subprocess.check_output(['git','show','6a6074aa620ade3813ee4f6b181a8a5e58b9526a:mac/OLMColorKey/OLMColorKey.cpp'],cwd=R).decode()
  source=re.sub(r'#include "([^"]+)"',lambda m:'#include "'+str((SOURCE.parent/m[1]).resolve())+'"' if (SOURCE.parent/m[1]).exists() else m[0],source)
  path=D/'baseline.cpp';path.write_text(source);geometry_host=a.geometry_host
  a.geometry_host=lambda body:geometry_host(body).replace(str(SOURCE),str(path))
 b=D/('before' if baseline else sha(str(worker).encode())[:12]);b.mkdir(exist_ok=True)
 p=a.prepare(b,time.monotonic()+300)
 if baseline:p.update(baseline_commit='6a6074aa620ade3813ee4f6b181a8a5e58b9526a',baseline_compiled_source_sha256=sha(path.read_bytes()))
 return a,p
out=(E/(mode+'.jsonl')).open('w')
def check(a,c,label):
 t=D/'case';t.mkdir(exist_ok=True)
 try:r=evaluate(a,c,t,time.monotonic()+60)
 finally:shutil.rmtree(t)
 row=dict(label=label,input_sha256=sha(c['pixels']),result=r);out.write(json.dumps(row)+'\n');out.flush();return r
if mode=='scan':
 a,p=adapter(baseline=True); b,q=adapter(); corpus=R/'tests/fuzz_corpus/olmcolorkey/C01-pf32-nan';corpus.mkdir(exist_ok=True)
 c,_=load_corpus(R/'orchestra/reports/N01-evidence/witnesses/c2d799e6b17314d055e78508.json',a)
 candidates=[('reduced-2081',c)]
 # N01 retained only one signature, so regenerate all observed indices and
 # evaluate the PF32 Lab component boundary implicated by the instruction proof.
 for i in range(18377):
  c=a.generate(812324792801853187,i); ps={v['slot']:v['value'] for v in c['parameters']}
  if c['depth']==32 and ps[5] in (3,4) and ps[8]:candidates.append((str(i),c))
 counts=collections.Counter();found=[]
 for label,c in candidates:
  before=check(a,c,'before-'+label);counts[before['routes']['smart']['status']]+=1
  if before['routes']['smart']['status']=='mismatch':
   after=check(b,c,'after-'+label);found.append(dict(index=label,before=before,after=after))
   save_corpus(corpus/(label+'.json'),b,c,c,after,dict(accepted=[],attempts=0,bounded=True,minimality_claimed=False),q)
   print(label,before['routes']['smart'].get('diff'),after['routes']['smart']['status'],flush=True)
  if sum(counts.values())%50==0:print('scan',dict(counts),flush=True)
 summary=dict(provenance_before=p,provenance_after=q,counts=counts,found=found)
elif mode=='witnesses':
 a,p=adapter();rows=[]
 for path in sorted((R/'tests/fuzz_corpus/olmcolorkey/C01-pf32-nan').glob('*.json')):
  c,old=load_corpus(path,a);r=check(a,c,path.stem);rows.append(dict(path=str(path.relative_to(R)),result=r))
  save_corpus(path,a,c,c,r,old['reduction'],p)
  print(path.stem,r['routes']['smart']['status'],r['routes']['smart'].get('diff'),flush=True)
 summary=dict(provenance=p,rows=rows)
elif mode=='campaign':
 a,p=adapter('worker-F52c-geom');counts={}
 for geom in ('default','realistic'):
  require_host(a,{'geometry_sampler':'realistic-v1'} if geom!='default' else {});a.routes=('smart',);a.oracle_routes={'smart':'smart'}
  for seed in (1,2026,2027):
   counter=collections.Counter();index=0
   for n in range(100):
    while True:
     c=a.generate(seed,index);index+=1
     if c['depth']==32:break
    # Keep generated controls/geometry; make every pixel contain a nonfinite
    # channel, rotating alpha/R/G/B and NaN/infinity signs and payloads.
    data=bytearray(c['pixels']);rng=random.Random(seed*1000+n)
    words=(0x7fc12345,0xffc12345,0x7f800000,0xff800000,0x7f812345)
    for at in range(0,len(data),16):struct.pack_into('<I',data,at+4*rng.randrange(4),rng.choice(words))
    c['pixels']=bytes(data);c=sample(c,geom)
    r=check(a,c,f'{geom}-{seed}-{n}');counter[r['routes']['smart']['status']]+=1
   counts[f'{geom}-{seed}']=dict(counter);print(geom,seed,dict(counter),flush=True)
 summary=dict(provenance=p,counts=counts)
elif mode=='default':
 a,p=adapter(baseline=True);b,q=adapter();counts=collections.Counter();regressions=[]
 for i in range(300):
  c=a.generate(1,i);before=check(a,c,f'before-{i}');after=check(b,c,f'after-{i}')
  pair=(before['routes']['smart']['status'],after['routes']['smart']['status']);counts['->'.join(pair)]+=1
  if pair[0]=='exact' and pair[1]!='exact':regressions.append(i)
  if (i+1)%50==0:print(i+1,dict(counts),flush=True)
 summary=dict(provenance_before=p,provenance_after=q,counts=counts,regressions=regressions)
elif mode=='corpus':
 cache={};counts=collections.Counter();changes=[]
 for path in sorted((R/'tests/fuzz_corpus/olmcolorkey').rglob('*.json')):
  saved=json.loads(path.read_text());worker=saved['provenance']['worker_path']
  assert sha(Path(worker).read_bytes()) == saved['provenance']['worker_sha256']
  if worker not in cache:cache[worker]=adapter(worker)
  a,p=cache[worker];a.max_size=saved['max_size'];c,_=load_corpus(path,a);require_host(a,c)
  # Preserve each historical route set and compare the same observations.
  a.routes=tuple(saved['result']['routes']);a.oracle_routes={r:r for r in a.routes}
  r=check(a,c,str(path.relative_to(R)));same=r==saved['result'];counts[str(same)]+=1
  if not same:changes.append(dict(path=str(path.relative_to(R)),before=saved['result'],after=r))
 summary=dict(counts=counts,changes=changes,provenance={k:v[1] for k,v in cache.items()});print(dict(counts),flush=True)
else:raise ValueError(mode)
(E/(mode+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n');out.close();shutil.rmtree(D)

if mode=='witnesses':assert all(r['result']['routes']['smart']['status']=='exact' for r in rows)
if mode=='campaign':assert all(set(c) <= {'exact','uncompared'} and sum(c.values())==100 for c in counts.values())
if mode=='default':assert not regressions
if mode=='corpus':assert not changes
