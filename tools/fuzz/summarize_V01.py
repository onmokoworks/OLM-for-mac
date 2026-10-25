#!/usr/bin/env python3
"""Summarize V01 observations without treating refusals/errors as exact renders."""
import argparse,collections,gzip,json,shutil
from pathlib import Path
from verify_V01 import STATE,ROOT,PLUGINS,THREADED

def rows(path):
 if path.exists():
  with path.open() as f:return [json.loads(line) for line in f]
 with gzip.open(str(path)+'.gz','rt') as f:return [json.loads(line) for line in f]

def retain_rows(path,dest):
 with path.open('rb') as source,(dest/(path.name+'.gz')).open('wb') as target:
  with gzip.GzipFile(filename='',fileobj=target,mode='wb',mtime=0) as out:shutil.copyfileobj(source,out)

def main():
 p=argparse.ArgumentParser();p.add_argument('--retain',action='store_true');p.add_argument('--evidence',action='store_true',help='Check committed compressed observations without scratch files');a=p.parse_args()
 if a.evidence and a.retain:p.error('--evidence and --retain are mutually exclusive')
 base=ROOT/'orchestra/reports/V01-evidence' if a.evidence else STATE
 summary={}
 for phase in ('default','realistic-v1','realistic-v2','odd-even-v1','heavy','default-oracle','realistic-v1-oracle'):
  path=base/(phase+'.jsonl')
  if not path.exists() and not Path(str(path)+'.gz').exists():continue
  counts=collections.Counter();pairs=collections.Counter();plugins={};bad=[];identities=set()
  for r in rows(path):
    assert r['identity'] not in identities;identities.add(r['identity'])
    counts[r['verdict']]+=1;plugins.setdefault(r['plugin'],collections.Counter())[r['verdict']]+=1
    for pair in r['results']:
     pairs['equal_'+pair['arm64']['status'] if pair['equal'] else 'difference_or_error']+=1
    if r['verdict'] not in ('equal','exact'):bad.append(dict(identity=r['identity'],verdict=r['verdict'],first_byte=r.get('first_byte'),**({k:r[k] for k in ('oracle','x86_64') if k in r})))
    # A missing/timed-out output is not a numerical thread-cap difference.
    for arch in ('arm64','x86_64'):
     completed=[p[arch] for p in r['results'] if p[arch]['status'] in ('ok','refusal')]
     assert not completed or all(x==completed[0] for x in completed),r['identity']
  summary[phase]=dict(cases=len(identities),verdicts=dict(counts),pairs=dict(pairs),plugins={k:dict(v) for k,v in plugins.items()},non_equal=bad)
  print(phase,len(identities),dict(counts),dict(pairs))
 for phase in ('default-oracle','realistic-v1-oracle'):
  retry=base/'retry-60'/(phase+'.jsonl')
  if not retry.exists() and not Path(str(retry)+'.gz').exists():continue
  merged={r['identity']:r for r in rows(base/(phase+'.jsonl'))}
  retries=rows(retry)
  for r in retries:
   assert merged[r['identity']]['oracle']['status']=='budget'
   merged[r['identity']]=r
  counts=collections.Counter(r['verdict'] for r in merged.values())
  summary[phase+'-after-retry']=dict(cases=len(merged),retried=len(retries),verdicts=dict(counts),oracle_statuses=dict(collections.Counter(r['oracle']['status'] for r in merged.values())))
  print(phase+'-after-retry',dict(counts))
 if a.evidence:
  assert summary==json.loads((base/'summary.json').read_text()),'retained summary differs'
  for phase,n in (('default',100),('realistic-v1',100),('realistic-v2',100),('odd-even-v1',50),('heavy',6)):
   data=rows(base/(phase+'.jsonl'))
   cells=[f'{size}/{depth}' for size in ('full','4k') for depth in (8,16,32)] if phase=='heavy' else list(map(str,range(n)))
   assert {r['identity'] for r in data}=={plugin+'/'+cell for plugin in PLUGINS for cell in cells},phase
   for r in data:
    assert r['verdict']=='equal',r['identity']
    assert [p['cap'] for p in r['results']]==([1,2,8] if r['plugin'] in THREADED else [1]),r['identity']
    assert all(p['equal'] and p['first_byte'] is None and p['arm64']==p['x86_64'] for p in r['results']),r['identity']
  print('complete requested slice coverage: 3560 cases, 8544 pairs')
  bindings=0
  for phase in ('default','realistic-v1'):
   native={r['identity']:r for r in rows(base/(phase+'.jsonl'))}
   for original in rows(base/(phase+'-oracle.jsonl')):
    r=native[original['identity']]
    assert (r['case'],r['input_sha256'])==(original['case'],original['input_sha256']),r['identity']
    assert r['results'][0]['x86_64']==original['x86_64'],r['identity']
    bindings+=1
  print('same inputs, parameters and Intel cap-1 outputs:',bindings)
  assert bindings==2000
 else:(STATE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 if a.retain:
  dest=ROOT/'orchestra/reports/V01-evidence';dest.mkdir(exist_ok=True)
  shutil.copy2(STATE/'summary.json',dest/'summary.json')
  for path in STATE.glob('*.jsonl'):
   retain_rows(path,dest)
  for path in STATE.glob('*-provenance.json'):shutil.copy2(path,dest/path.name)
  retry_dest=dest/'retry-60';retry_dest.mkdir(exist_ok=True)
  for path in (STATE/'retry-60').glob('*.jsonl'):
   retain_rows(path,retry_dest)
  for path in (STATE/'retry-60').glob('*-provenance.json'):shutil.copy2(path,retry_dest/path.name)
if __name__=='__main__':main()
