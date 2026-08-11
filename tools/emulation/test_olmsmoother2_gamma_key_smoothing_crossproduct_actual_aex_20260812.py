#!/usr/bin/env python3
"""Bounded Gamma endpoint x key polarity x smoothing matrix, all depths."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_geometry_classifier_matrix_actual_aex_20260811 as base

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_geometry_classifier_matrix_production_harness_20260811.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_gamma_key_smoothing_crossproduct_actual_aex_20260812.json'
DOC=ROOT/'refs/conformance/olmsmoother2_gamma_key_smoothing_crossproduct_actual_aex_20260812.md'
W,H,PATTERN=9,7,'diagonal'
TUPLES={'lower':(1,0,0),'mixed':(50,50,50),'upper':(100,100,100)}
FEATURES=('gamma_all','colors_noninvert','colors_invert')
GAMMAS=(1.0,2.4)

def req(value,message):
 if not value: raise RuntimeError('FAIL CLOSED: '+message)

def main():
 with tempfile.TemporaryDirectory(prefix='sm2_gamma_cross_') as td:
  binary=Path(td)/'harness'
  subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True)
  rows=[]
  for feature in FEATURES:
   for gamma in GAMMAS:
    for tuple_name,(smooth,range_,extra) in TUPLES.items():
     for depth,(pixel_size,pad) in base.DEPTHS.items():
      pixels=base.encoded(depth,PATTERN,W,H,feature)
      actual,class_plane,ci,wi=base.actual(depth,2,pixels,pad,W,H,smooth,range_,extra,feature,gamma)
      proc=subprocess.run([str(binary),str(W),str(H),PATTERN,'2',str(smooth),str(range_),str(extra),depth,feature,str(gamma)],check=True,text=True,capture_output=True)
      lines=dict(line.split(' ',1) for line in proc.stdout.splitlines())
      production=bytes.fromhex(lines['RAW'])
      rowbytes=W*pixel_size+pad
      req(all(actual[y*rowbytes+W*pixel_size:(y+1)*rowbytes]==b'\xa5'*pad for y in range(H)),f'{feature}/gamma{gamma}/{tuple_name}/{depth} padding')
      exact=actual==production
      rows.append({'feature':feature,'gamma_value':gamma,'smoothing_tuple':tuple_name,'smoothness':smooth,'smooth_range':range_,'extra_smooth':extra,'depth':depth,'actual_raw_sha256':hashlib.sha256(actual).hexdigest(),'production_raw_sha256':hashlib.sha256(production).hexdigest(),'raw_mismatch_bytes':sum(a!=b for a,b in zip(actual,production)),'class_plane_sha256':hashlib.sha256(class_plane).hexdigest(),'classifier_instructions':ci,'worker_instructions':wi,'padding_per_row':pad,'exact':exact})
  req(len(rows)==54,'case count')
  exact=[row for row in rows if row['exact']]; failed=[row for row in rows if not row['exact']]
  req(len(exact)==53,'exact case count')
  req(len(failed)==1 and failed[0]['feature']=='gamma_all' and failed[0]['gamma_value']==2.4 and failed[0]['smoothing_tuple']=='mixed' and failed[0]['depth']=='PF8' and failed[0]['raw_mismatch_bytes']==5,'unexpected fail-closed seam')
  report={'schema':'olmsmoother2.gamma-key-smoothing-crossproduct/1','verdict':'PASS_53_EXACT_ONE_PF8_GAMMA_ALL_MIXED_FAIL_CLOSED','scope':'v2 padded 9x7 diagonal fixture; Gamma All plus Gamma Colors with non-invert/invert key; public Gamma endpoints and three smoothing boundary tuples; PF8/PF16/PF32','case_count':len(rows),'exact_case_count':len(exact),'fail_closed_case_count':len(failed),'fail_closed_boundary':{'feature':'gamma_all','gamma_value':2.4,'smoothing_tuple':'mixed','depth':'PF8','raw_mismatch_bytes':5,'decision':'unsupported until the five-byte typed writer seam is explained by a new actual-AEX witness'},'geometry':[W,H],'pattern':PATTERN,'gamma_values':list(GAMMAS),'features':list(FEATURES),'smoothing_tuples':TUPLES,'cases':rows,'aex_sha256':base.typed.AEX_SHA256,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No arbitrary parameter-product generalization','No other key colors or Gamma palettes','No AE-host execution claim','No exact claim for PF8 Gamma All 2.4 mixed smoothing']}
  REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
  DOC.write_text('# OLMSmoother2 Gamma/key/smoothing bounded cross-product\n\nVerdict: `'+report['verdict']+'`\n\nA padded 9x7 non-uniform fixture crosses public Gamma Value endpoints `1.0/2.4`, Gamma All and Gamma Colors with both key polarities, three smoothing boundary tuples, and PF8/PF16/PF32. 53 of 54 actual-AEX owner/classifier/typed-worker outputs match production raw bytes exactly, with row padding preserved.\n\nThe sole unsupported seam is PF8 Gamma All at 2.4 with the mixed `(Smoothness, Range, Extra Smooth) = (50, 50, 50)` tuple: five output bytes differ. It remains fail-closed pending a focused typed-writer witness; no rounding rule is inferred from it. Other key colors, palettes, arbitrary parameter products, and AE-host execution also remain unclaimed.\n')
  print(report['verdict'],len(exact),len(failed))
 return 0
if __name__=='__main__': raise SystemExit(main())
