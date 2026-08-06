#!/usr/bin/env python3
"""Independent PF32 actual-owner/production Inner power-of-two family."""
import hashlib,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as base
REPORT=ROOT/'refs/conformance/olmradialblur_rotation_pf32_inner_strength_family_production_20260806.json'
STRENGTHS=tuple(int(x) for x in os.environ.get('OLM_RADIAL_INNER_STRENGTHS','1,2,4,8,16,32,64').split(','))
def sha(x):return hashlib.sha256(x).hexdigest()
def main():
 if os.environ.get('OLM_RADIAL_AGGREGATE')=='1':
  cases=[]
  for s in (1,2,4,8,16,32,64):cases.extend(json.loads(Path(f'/tmp/rb_pf32_inner_{s}.json').read_text())['cases'])
  report={'kind':'olmradialblur_rotation_pf32_inner_strength_family_production_20260806','status':'exact' if all(x['status']=='exact' for x in cases) else 'fail_closed','scope':'Independent native PF32 actual-AEX owner and production 9x7 rowbytes160 Rotation Inner power-of-two family; internal planes plus padded output','strengths':[1,2,4,8,16,32,64],'cases':cases};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0 if report['status']=='exact' else 2
 rows=[]
 for strength in STRENGTHS:
  base.OUTER_STRENGTH=0;base.INNER_STRENGTH=strength
  actual=base.actual_aex();production=base.mac_production(actual);names=('polar','source_scalar','accum','max_alpha','final_rgba','output');matches={n:production[n]==actual[n] for n in names};padding=all(production['output'][y*160+144:(y+1)*160]==bytes([0xc0+y])*16 for y in range(7));rows.append({'inner_strength':strength,'effective_span':max(0,strength-1),'status':'exact' if all(matches.values()) and padding else 'mismatch','matches':matches,'padding_exact':padding,'hashes':{n:sha(actual[n]) for n in names}})
 report={'kind':'olmradialblur_rotation_pf32_inner_strength_family_production_20260806','status':'exact' if all(x['status']=='exact' for x in rows) else 'fail_closed','scope':'Independent native PF32 actual-AEX owner and production 9x7 rowbytes160 Rotation Inner power-of-two family; internal planes plus padded output','strengths':list(STRENGTHS),'cases':rows};Path(os.environ.get('OLM_RADIAL_INNER_REPORT',str(REPORT))).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0 if report['status']=='exact' else 2
if __name__=='__main__':raise SystemExit(main())
