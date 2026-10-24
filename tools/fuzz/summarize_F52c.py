#!/usr/bin/env python3
"""Summarize actual comparisons; oracle failure takes precedence over candidate status."""
import json,collections
from measure_F52c import S,PLUGINS

def main():
 allrows={}
 for name in PLUGINS:
  rows=[json.loads(x) for x in (S/'campaigns'/name/'results.jsonl').read_text().splitlines()]
  counts=collections.defaultdict(collections.Counter);tags=collections.Counter();first={};unavailable=collections.Counter();failures=collections.Counter()
  for row in rows:
   i=row['case']['index']
   for route,r in row['result']['routes'].items():
    o=row['result'].get('oracles',{}).get(route,row['result']['oracle'])
    category='U' if o['status']!='ok' else 'E' if r['status'] in ('exact','no_write') else 'M' if r['status'] in ('mismatch','no_write_violation') else 'R' if r['status']=='refusal' else 'U'
    counts[route][category]+=1
    if category!='E':first.setdefault(route+':'+category,row)
    if o['status']!='ok':unavailable[route+':'+o['status']]+=1
    if r['status'] not in ('exact','no_write','mismatch','no_write_violation','refusal','uncompared'):failures[route+':'+r['status']]+=1
    for tag in row['refusals'].get(route,[]):
     classification='Mac-only' if o['status']=='ok' else 'unresolved-oracle-unavailable'
     tags[(route,tag,classification)]+=1
     first.setdefault(route+':'+tag+':'+classification,row)
  result=dict(n=len(rows),seed=1,counts={r:{k:c[k] for k in 'EMRU'} for r,c in counts.items()},tags=[dict(route=r,tag=t,classification=c,count=n) for (r,t,c),n in sorted(tags.items())],first=first,oracle_unavailable=dict(unavailable),candidate_host_failures=dict(failures))
  allrows[name]=result
  print(name,result['counts'],'host failures',dict(failures))
 (S/'summary.json').write_text(json.dumps(allrows,indent=2)+'\n')
if __name__=='__main__':main()
