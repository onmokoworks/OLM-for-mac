#!/usr/bin/env python3
"""Independent streamed-call check of in-process dispatch, counts and resume."""
import argparse,csv,itertools,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);a=p.parse_args();s=a.state.resolve()
dll=str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll')
names=['ucrt0','ucrt1','apple','amd-off','amd-fma'];mask=(1<<64)-1

def mix(n):
 x=((n^0xf27c)+0x9e3779b97f4a7c15)&mask;x=((x^(x>>30))*0xbf58476d1ce4e5b9)&mask;x=((x^(x>>27))*0x94d049bb133111eb)&mask;return x^(x>>31)
def outputs(fn,inputs):
 text=''.join(f'{x:08x} {y:08x}\n' for x,y in inputs)
 cmds=[[str(s/'oracle'),dll,str(m),fn] for m in (0,1)]+[[str(s/'apple'),fn]]+[[str(s/'apple'),fn,str(s/'amd'/f'amd-{m}.dylib')] for m in ('off','fma')]
 return [[int(x,16) for x in subprocess.run(c,input=text,text=True,capture_output=True,check=True).stdout.split()] for c in cmds]
for fn in ('expf','sinf','cosf','atan2f','powf'):
 inputs=[(mix(n)&0xffffffff,mix(n)>>32) if fn in ('atan2f','powf') else (n,0) for n in range(4096)]
 out=outputs(fn,inputs)
 for label,ends,chunk in [('once',[4096],4096),('resume',[2048,4096],997)]:
  d=s/'check'/fn/label;d.mkdir(parents=True,exist_ok=True)
  # Never silently reuse an old test checkpoint.
  if (d/'checkpoint.bin').exists():(d/'checkpoint.bin').unlink()
  for end in ends:
   subprocess.run([str(s/'sweep'),dll,fn,str(s/'amd/amd-off.dylib'),str(s/'amd/amd-fma.dylib'),str(d),str(end),str(chunk)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  actual=list(csv.DictReader((d/'counts.csv').open()));buckets=[];first=[]
  for k,(i,j) in enumerate(itertools.combinations(range(5),2)):
   bad=[n for n in range(4096) if out[i][n]!=out[j][n]];pair=f'{names[i]}/{names[j]}'
   assert actual[k]==dict(pair=pair,processed='4096',mismatches=str(len(bad)))
   for arg in (0,1):
    for e in range(256):
     count=sum((inputs[n][arg]>>23)&255==e for n in bad)
     if count:buckets.append(dict(pair=pair,argument=str(arg),biased_exponent=str(e),mismatches=str(count)))
   for n in bad[:2000]:first.append(dict(pair=pair,a=f'{inputs[n][0]:08x}',b=f'{inputs[n][1]:08x}',left=f'{out[i][n]:08x}',right=f'{out[j][n]:08x}'))
  assert list(csv.DictReader((d/'buckets.csv').open()))==buckets
  assert list(csv.DictReader((d/'first.csv').open()))==first
 for name in ('checkpoint.bin','counts.csv','buckets.csv','first.csv'):
  assert (s/'check'/fn/'once'/name).read_bytes()==(s/'check'/fn/'resume'/name).read_bytes()
 print('PASS',fn,'4096 inputs, five engines, counts/buckets/witnesses/resume')
paper=json.loads((pathlib.Path(__file__).parent/'results-f27c/paper-inputs.json').read_text());rows=[]
for fn in ('atan2f','powf'):
 cases=[r for r in paper['cases'] if r['function']==fn];out=outputs(fn,[[int(v,16) for v in r['bits']] for r in cases])
 for n,r in enumerate(cases):rows.append(dict(**r,outputs={name:f'{out[i][n]:08x}' for i,name in enumerate(names)}))
(s/'paper-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS paper corpus:',len(rows),'pairs,',5*len(rows),'results')
