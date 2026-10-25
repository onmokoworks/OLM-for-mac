#!/usr/bin/env python3
"""Summarize V01 observations without treating refusals/errors as exact renders."""
import argparse,collections,gzip,json,shutil
from pathlib import Path
from verify_V01 import STATE,ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--retain',action='store_true');a=p.parse_args()
 summary={}
 for phase in ('default','realistic-v1','realistic-v2','odd-even-v1','heavy','default-oracle','realistic-v1-oracle'):
  path=STATE/(phase+'.jsonl')
  if not path.exists():continue
  counts=collections.Counter();pairs=collections.Counter();plugins={};bad=[];identities=set()
  with path.open() as f:
   for line in f:
    r=json.loads(line);assert r['identity'] not in identities;identities.add(r['identity'])
    counts[r['verdict']]+=1;plugins.setdefault(r['plugin'],collections.Counter())[r['verdict']]+=1
    for pair in r['results']:
     pairs['equal_'+pair['arm64']['status'] if pair['equal'] else 'difference_or_error']+=1
    if r['verdict'] not in ('equal','exact'):bad.append(dict(identity=r['identity'],verdict=r['verdict'],first_byte=r.get('first_byte'),**({k:r[k] for k in ('oracle','x86_64') if k in r})))
    assert not r.get('thread_cap_difference'),r['identity']
  summary[phase]=dict(cases=len(identities),verdicts=dict(counts),pairs=dict(pairs),plugins={k:dict(v) for k,v in plugins.items()},non_equal=bad)
  print(phase,len(identities),dict(counts),dict(pairs))
 for phase in ('default-oracle','realistic-v1-oracle'):
  retry=STATE/'retry-60'/(phase+'.jsonl')
  if not retry.exists():continue
  merged={r['identity']:r for r in map(json.loads,(STATE/(phase+'.jsonl')).read_text().splitlines())}
  retries=list(map(json.loads,retry.read_text().splitlines()))
  for r in retries:
   assert merged[r['identity']]['oracle']['status']=='budget'
   merged[r['identity']]=r
  counts=collections.Counter(r['verdict'] for r in merged.values())
  summary[phase+'-after-retry']=dict(cases=len(merged),retried=len(retries),verdicts=dict(counts),oracle_statuses=dict(collections.Counter(r['oracle']['status'] for r in merged.values())))
  print(phase+'-after-retry',dict(counts))
 (STATE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 if a.retain:
  dest=ROOT/'orchestra/reports/V01-evidence';dest.mkdir(exist_ok=True)
  shutil.copy2(STATE/'summary.json',dest/'summary.json')
  for path in STATE.glob('*.jsonl'):
   with path.open('rb') as source,gzip.open(dest/(path.name+'.gz'),'wb') as out:shutil.copyfileobj(source,out)
  for path in STATE.glob('*-provenance.json'):shutil.copy2(path,dest/path.name)
  retry_dest=dest/'retry-60';retry_dest.mkdir(exist_ok=True)
  for path in (STATE/'retry-60').glob('*.jsonl'):
   with path.open('rb') as source,gzip.open(retry_dest/(path.name+'.gz'),'wb') as out:shutil.copyfileobj(source,out)
  for path in (STATE/'retry-60').glob('*-provenance.json'):shutil.copy2(path,retry_dest/path.name)
if __name__=='__main__':main()
