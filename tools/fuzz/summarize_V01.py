#!/usr/bin/env python3
"""Summarize V01 observations without treating refusals/errors as exact renders."""
import argparse,collections,gzip,json,shutil
from pathlib import Path
from verify_V01 import STATE,ROOT

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
    assert not r.get('thread_cap_difference'),r['identity']
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
