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
CASES=(
 (0.0,0,0.0),(25.0,0,0.0),(50.0,0,0.0),(100.0,0,0.0),
 (25.0,50,0.0),(25.0,100,0.0),(50.0,50,0.0),(50.0,100,0.0),
 (100.0,50,0.0),(100.0,100,0.0),(50.0,0,50.0),(50.0,0,100.0),
)

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
  for i,(size,fade,sharp) in enumerate(CASES):
   case_dir=temp/f'c{i}'; case_dir.mkdir()
   actual,am=base.capture_actual(45.0,source,front_strength=8,back_strength=0,front_alpha_fade=fade,front_sharp_tail=sharp,size_variation=size,noise_variation=0.0,brightness_gain=1.0)
   mac,mm=base.capture_mac(source,case_dir,45.0,front_strength=8,back_strength=0,front_alpha_fade=fade,front_sharp_tail=sharp,size_variation=size,noise_variation=0.0,brightness_gain=1.0)
   mismatch=[j for j,(a,b) in enumerate(zip(actual,mac)) if a!=b]
   if len(actual)!=1024 or len(mac)!=1024 or mismatch or mm['exact']!=1 or not am['natural_complete']:
    raise RuntimeError(f'size={size:g} fade={fade} sharp={sharp:g} mismatch={len(mismatch)} exact={mm["exact"]}')
   rows.append({'size_variation_percent':size,'front_alpha_fade':fade,'front_sharp_tail':sharp,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':[x['callback'] for x in am['iterate_calls']],'production_exact':mm['exact']})
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 if 'info.size_variation >= 0.0 && info.size_variation <= 100.0' not in text: raise RuntimeError('PF8 bounded Size predicate absent')
 report={'schema_version':1,'status':'exact_representative_family','plugin':'OLMDirectionalBlur','depth':'PF8','family':'Size Variation plus bounded Front Fade/Sharp crosses','fixed_route':{'geometry':'16x16 padded ARGB32','angle':45,'brightness_gain':1,'front_strength':8,'back_strength':0,'noise':0,'render_scale':[1,1]},'representatives':rows,'component_rule':'Nonzero Size builds connected-component records before Fade prepass and Sharp coefficients are passed together to the shared float rowdriver; alpha weight uses pow(clamp(sample alpha), Size/100) and the component-area divisor.','writer_rule':'Production writes straight RGBA worker bytes into PF ARGB channels; RGB and alpha use float*255 followed by C++ integer truncation, not round-to-nearest.','cross_admission':{'size_x_front_fade':{'size':[25,50,100],'fade':[50,100]},'size_x_front_sharp':{'size':[50],'sharp':[50,100]}},'legacy_preserved':'960x540 Size92 x FrontSharp45, angle0, scale0.5 remains independently hash-proven.','fail_closed':['Size below 0 or above 100','other Size x Front Fade/Sharp tuples','unproved geometry/tuple and other parameter combinations'],'not_proven':['PF8 other geometry','other Fade/Sharp combinations','Noise/Back combinations','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur PF8 Size × Fade/Sharp — 2026-08-11\n\nActual Windows AEX and production are raw-byte exact for Size 25/50/100 × Front Fade 50/100 and Size 50 × Front Sharp 50/100 on the pinned 16×16 route, in addition to Size 0/25/50/100 alone. Component records/divisor are built before Fade prepass and Sharp coefficients enter the shared rowdriver. The writer uses float×255 integer truncation. Only listed crosses are admitted; the older 960×540 Size92×Sharp45 witness remains an explicit exception.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_PF8_SIZE_FADE_SHARP cases=12 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
