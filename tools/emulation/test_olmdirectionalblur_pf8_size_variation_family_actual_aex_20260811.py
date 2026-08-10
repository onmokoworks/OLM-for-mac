#!/usr/bin/env python3
"""PF8 Size Variation family and one Front Fade cross through production."""
from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py'
ALPHA=ROOT/'tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.md'
CASES=((0.0,0),(25.0,0),(50.0,0),(100.0,0),(50.0,50))

def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise RuntimeError(name)
 module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def main()->int:
 if sys.platform!='darwin': raise SystemExit('Mac-only production seam')
 base=load(BASE,'dblur_pf8_base'); source=load(ALPHA,'dblur_pf8_alpha').build_input()
 rows=[]
 with tempfile.TemporaryDirectory(prefix='olm_dblur_pf8_size_family_') as raw:
  temp=Path(raw)
  for i,(size,fade) in enumerate(CASES):
   case_dir=temp/f'c{i}'; case_dir.mkdir()
   actual,am=base.capture_actual(45.0,source,front_strength=8,back_strength=0,front_alpha_fade=fade,front_sharp_tail=0.0,size_variation=size,noise_variation=0.0,brightness_gain=1.0)
   mac,mm=base.capture_mac(source,case_dir,45.0,front_strength=8,back_strength=0,front_alpha_fade=fade,front_sharp_tail=0.0,size_variation=size,noise_variation=0.0,brightness_gain=1.0)
   mismatch=[j for j,(a,b) in enumerate(zip(actual,mac)) if a!=b]
   if len(actual)!=1024 or len(mac)!=1024 or mismatch or mm['exact']!=1 or not am['natural_complete']:
    raise RuntimeError(f'size={size:g} fade={fade} mismatch={len(mismatch)} exact={mm["exact"]}')
   rows.append({'size_variation_percent':size,'front_alpha_fade':fade,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':[x['callback'] for x in am['iterate_calls']],'production_exact':mm['exact']})
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 if 'info.size_variation >= 0.0 && info.size_variation <= 100.0' not in text: raise RuntimeError('PF8 bounded Size predicate absent')
 report={'schema_version':1,'status':'exact_representative_family','plugin':'OLMDirectionalBlur','depth':'PF8','family':'Size Variation 0..100 plus bounded Front Fade cross','fixed_route':{'geometry':'16x16 padded ARGB32','angle':45,'brightness_gain':1,'front_strength':8,'back_strength':0,'sharp_noise':0,'render_scale':[1,1]},'representatives':rows,'component_rule':'Nonzero Size builds connected-component records; alpha weight is pow(clamp(sample alpha), Size/100), normalized by the component-area divisor in the shared float rowdriver.','writer_rule':'Production writes straight RGBA worker bytes into PF ARGB channels; RGB and alpha use float*255 followed by C++ integer truncation, not round-to-nearest.','basis':'0 and 100 are public endpoints, 25 is a non-half interior exponent, and 50 is the midpoint. All are actual-AEX/production raw exact through the same continuous exponent path.','cross_admission':{'size_variation':50,'front_alpha_fade':50},'fail_closed':['Size below 0 or above 100','unproved geometry/tuple and other parameter combinations'],'not_proven':['PF8 other geometry','other Fade combinations','Sharp/Noise/Back combinations','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur PF8 Size Variation — 2026-08-11\n\nActual Windows AEX and the production PF8 full worker are raw-byte exact for Size 0/25/50/100 and Size 50 × Front Fade 50 on the pinned 16×16 route. Nonzero Size uses the connected-component area/divisor and continuous `pow(alpha, Size/100)` path. The writer converts float channels with multiplication by 255 followed by integer truncation. Values outside the public 0..100 range fail closed.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_PF8_SIZE_VARIATION sizes=0,25,50,100 cross=50x50 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
