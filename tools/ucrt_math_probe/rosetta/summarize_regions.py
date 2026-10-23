#!/usr/bin/env python3
"""Compact exponent-region and first-witness summaries, derived only from CSVs."""
import argparse,csv,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--full',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();result={}
for fn in ('expf','sinf','cosf','atan2f','powf'):
 d=a.full/fn;buckets=list(csv.DictReader((d/'buckets.csv').open()));first=list(csv.DictReader((d/'first.csv').open()));counts=list(csv.DictReader((d/'counts.csv').open()));pairs={}
 for row in counts:
  pair=row['pair'];regions=[]
  for arg in ['0','1']:
   rs=[r for r in buckets if r['pair']==pair and r['argument']==arg];es=[int(r['biased_exponent']) for r in rs]
   regions.append(dict(argument=int(arg),minimum=min(es) if es else None,maximum=max(es) if es else None,missing_inside_range=[e for e in range(min(es),max(es)+1) if e not in es] if es else [],below_half=sum(int(r['mismatches']) for r in rs if int(r['biased_exponent'])<=125),nonfinite_bucket=sum(int(r['mismatches']) for r in rs if int(r['biased_exponent'])==255)))
  pairs[pair]=dict(mismatches=int(row['mismatches']),regions=regions,first=next((r for r in first if r['pair']==pair),None))
 result[fn]=pairs
a.out.write_text(json.dumps(result,indent=2)+'\n')
