#!/usr/bin/env python3
"""PF16 Size Variation family and one Fade cross through actual AEX."""
from __future__ import annotations
import ctypes, hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_pf16_size_variation_family_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_pf16_size_variation_family_actual_aex_20260811.md'
W=H=16; ACTIVE=W*H*8; PAD=16
CASES=((0.0,0),(25.0,0),(50.0,0),(100.0,0),(50.0,50))

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_pf16_size_') as raw:
  t=Path(raw); srcpath=t/'source.png'; image=Image.open(SOURCE).convert('RGBA').crop((472,262,488,278)); image.save(srcpath)
  packed=b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in image.get_flattened_data())
  lib=t/'lib.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
  if build.returncode: raise RuntimeError(build.stderr)
  fn=ctypes.CDLL(str(lib)).olm_dblur_full_argb16
  fn.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint16),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float]
  Words=ctypes.c_uint16*(ACTIVE//2); source=Words.from_buffer_copy(packed); rows=[]
  for i,(size,fade) in enumerate(CASES):
   meta=t/f'c{i}.json'; out=t/f'c{i}.argb64'
   cmd=[sys.executable,str(FIXTURE),'--source',str(srcpath),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth','16','--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation',str(int(size)),'--front-alpha-fade',str(fade),'--front-sharp-tail','0','--back-strength','0','--back-alpha-fade','0','--back-sharp-tail','0','--noise-variation','0','--noise-type','1','--seed','1','--noise-offset','0','--thickness','10','--world-area','0','0','16','16','--row-padding',str(PAD),'--no-detour-rotate','--max-instructions','20000000']
   run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
   if run.returncode: raise RuntimeError(run.stderr)
   m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Words()
   rc=fn(source,dst,W,H,8,fade,ctypes.c_float(0),0,0,ctypes.c_float(0),ctypes.c_float(size),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(0),1,1,0,ctypes.c_float(10))
   callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; production=bytes(dst)
   if rc or m['status']!='ok' or m['callback_model_check']['status']!='pass' or callbacks!=['0x1800068e0','0x180006a90'] or len(actual)!=ACTIVE or production!=actual:
    mismatch=sum(a!=b for a,b in zip(actual,production)); raise RuntimeError(f'size={size:g} fade={fade} differs ({mismatch} bytes)')
   rows.append({'size_variation_percent':size,'front_alpha_fade':fade,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':callbacks})
 source_text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 for token in ('pf16_size_variation_exact','pf16_size_fade_cross_exact','olm_dblur_full_argb16'):
  if token not in source_text: raise RuntimeError(f'missing production token {token}')
 report={'schema_version':1,'status':'exact_representative_family','plugin':'OLMDirectionalBlur','depth':'PF16','family':'Size Variation 0..100 plus bounded Front Fade cross','fixed_route':{'geometry':'16x16 padded ARGB64','angle':45,'brightness_gain':1,'front_strength':8,'back_strength':0,'sharp_noise':0,'render_scale':[1,1]},'representatives':rows,'basis':'Endpoints, a non-half interior value, and midpoint are exact through the same component-map/rowdriver coefficient path; the public 0..100 Size range is admitted only on this fixed route.','cross_admission':{'size_variation':50,'front_alpha_fade':50},'not_proven':['other PF16 geometry/tuple','Size outside 0..100','other Fade combinations','Sharp/Noise/Back combinations','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur PF16 Size Variation — 2026-08-11\n\nActual Windows AEX and the production ARGB64 worker are raw-byte exact for Size Variation 0/25/50/100 and Size 50 × Front Alpha Fade 50 on the pinned 16×16 route. The continuous public Size range uses one component-map exponent path; admission remains fixed-route bounded, and the Fade cross is tuple-enumerated.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_pf16_size_variation_family_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_PF16_SIZE_VARIATION sizes=0,25,50,100 cross=50x50 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
