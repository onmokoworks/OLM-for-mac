#!/usr/bin/env python3
"""PF32 Front Alpha Fade representatives through actual AEX and production."""
from __future__ import annotations
import ctypes, hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_pf32_front_alpha_fade_family_actual_aex_20260810.json'
W=H=16; ACTIVE=W*H*16; PAD=32; CASES=(0,50,100)

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_pf32_fade_') as raw:
  t=Path(raw); src=t/'source.png'; image=Image.open(SOURCE).convert('RGBA').crop((472,262,488,278)); image.save(src)
  packed=b''.join(struct.pack('<4f',p[3]/255,p[0]/255,p[1]/255,p[2]/255) for p in image.get_flattened_data())
  lib=t/'lib.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
  if build.returncode: raise RuntimeError(build.stderr)
  fn=ctypes.CDLL(str(lib)).olm_dblur_minimal_fade_argb32
  fn.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_float),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float,ctypes.POINTER(ctypes.c_float),ctypes.c_int]
  Floats=ctypes.c_float*(ACTIVE//4); source=Floats.from_buffer_copy(packed); rows=[]
  for fade in CASES:
   meta=t/f'a{fade}.json'; out=t/f'a{fade}.argb128'
   cmd=[sys.executable,str(FIXTURE),'--source',str(src),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth','32','--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation','0','--front-alpha-fade',str(fade),'--front-sharp-tail','0','--back-strength','0','--back-alpha-fade','0','--back-sharp-tail','0','--noise-variation','0','--noise-type','1','--seed','1','--noise-offset','0','--thickness','10','--world-area','0','0','16','16','--row-padding',str(PAD),'--no-detour-rotate','--max-instructions','20000000']
   run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
   if run.returncode: raise RuntimeError(run.stderr)
   m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Floats()
   rc=fn(source,dst,W,H,8,0,fade,ctypes.c_float(0),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(0),1,1,0,ctypes.c_float(10),None,0)
   callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; production=bytes(dst)
   if rc or m['status']!='ok' or m['callback_model_check']['status']!='pass' or callbacks!=['0x180006a20','0x180006bd0'] or production!=actual: raise RuntimeError(f'fade {fade} differs')
   rows.append({'front_alpha_fade':fade,'raw_sha256':hashlib.sha256(actual).hexdigest(),'byte_count':len(actual),'callbacks':callbacks})
 source_text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 for token in ('front_alpha_fade_exact','info.front_alpha_fade <= 100','olm_dblur_minimal_fade_argb32'):
  if token not in source_text: raise RuntimeError(f'missing production token {token}')
 report={'schema_version':1,'status':'exact_representative_family','plugin':'OLMDirectionalBlur','depth':'PF32','family':'Front Alpha Fade 0..100','fixed_route':{'geometry':'16x16 padded ARGB128','angle':45,'brightness_gain':1,'front_strength':8,'back_strength':0,'size_variation':0,'sharp_tail_noise':0,'render_scale':[1,1]},'representatives':rows,'basis':'Actual AEX typed callbacks and production worker are raw-byte exact at the public endpoints and midpoint. The same prepass table/count path is used throughout the bounded slider family.','production_source':'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','not_proven':['PF16','Sharp Tail','Back Alpha Fade','combinations with Size Variation/noise/back blur/other angle or strength/downsample','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print('PASS_OLMDIRECTIONALBLUR_PF32_FRONT_ALPHA_FADE sizes=0,50,100 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
