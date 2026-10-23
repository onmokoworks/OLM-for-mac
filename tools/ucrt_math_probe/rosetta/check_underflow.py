#!/usr/bin/env python3
"""Measure the retained UCRT zero / AMD min-subnormal powf boundary with MPFR."""
import argparse,csv,json,pathlib,struct
import gmpy2 as g
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
g.get_context().precision=200
rows=[r for r in csv.DictReader((a.state/'full/powf/first.csv').open()) if r['pair']=='ucrt0/amd-off' and r['left']=='00000000' and r['right']=='00000001']
vals=[]
for r in rows:
 x,y=[g.mpfr(struct.unpack('<f',struct.pack('<I',int(r[k],16)))[0]) for k in ['a','b']]
 z=x**y;assert g.mpfr(2)**-150<z<g.mpfr(2)**-149;vals.append(z/(g.mpfr(2)**-149))
a.out.write_text(json.dumps(dict(cases=len(rows),all_correctly_round_to='00000001',ucrt='00000000',minimum_exact_result_in_min_subnormal_units=str(min(vals)),maximum_exact_result_in_min_subnormal_units=str(max(vals)),mpfr=g.mpfr_version(),precision=200),indent=2)+'\n')
print('PASS:',len(rows),'underflow-boundary observations (UCRT differs from correctly rounded MPFR)')
