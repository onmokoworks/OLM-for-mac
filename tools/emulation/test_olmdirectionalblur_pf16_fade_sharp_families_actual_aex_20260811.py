#!/usr/bin/env python3
"""PF16 fade/sharp families through actual AEX and the ARGB64 worker."""
from __future__ import annotations
import ctypes, hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_pf16_fade_sharp_families_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_pf16_fade_sharp_families_actual_aex_20260811.md'
W=H=16; ACTIVE=W*H*8; PAD=16
CASES=(
 ('front_baseline',8,0,0,0,0,0),('front_fade',8,50,0,0,0,0),('front_fade',8,100,0,0,0,0),
 ('front_sharp',8,0,50,0,0,0),('front_sharp',8,0,100,0,0,0),
 ('back_baseline',0,0,0,8,0,0),('back_fade',0,0,0,8,50,0),('back_fade',0,0,0,8,100,0),
 ('back_sharp',0,0,0,8,0,50),('back_sharp',0,0,0,8,0,100),
 ('back_fade_sharp_cross',0,0,0,8,50,50),
)

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_pf16_fade_sharp_') as raw:
  t=Path(raw); srcpath=t/'source.png'; image=Image.open(SOURCE).convert('RGBA').crop((472,262,488,278)); image.save(srcpath)
  packed=b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in image.get_flattened_data())
  lib=t/'lib.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
  if build.returncode: raise RuntimeError(build.stderr)
  fn=ctypes.CDLL(str(lib)).olm_dblur_full_argb16
  fn.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint16),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float,ctypes.POINTER(ctypes.c_uint16),ctypes.c_int]
  Words=ctypes.c_uint16*(ACTIVE//2); source=Words.from_buffer_copy(packed); rows=[]
  for i,(family,front,ffade,fsharp,back,bfade,bsharp) in enumerate(CASES):
   meta=t/f'c{i}.json'; out=t/f'c{i}.argb64'
   cmd=[sys.executable,str(FIXTURE),'--source',str(srcpath),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth','16','--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength',str(front),'--size-variation','0','--front-alpha-fade',str(ffade),'--front-sharp-tail',str(fsharp),'--back-strength',str(back),'--back-alpha-fade',str(bfade),'--back-sharp-tail',str(bsharp),'--noise-variation','0','--noise-type','1','--seed','1','--noise-offset','0','--thickness','10','--world-area','0','0','16','16','--row-padding',str(PAD),'--no-detour-rotate','--max-instructions','20000000']
   run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
   if run.returncode: raise RuntimeError(f'{family}: {run.stderr}')
   m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Words()
   rc=fn(source,dst,W,H,front,ffade,ctypes.c_float(fsharp),back,bfade,ctypes.c_float(bsharp),ctypes.c_float(0),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(0),1,1,0,ctypes.c_float(10),None,0)
   callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; production=bytes(dst)
   if rc or m['status']!='ok' or m['callback_model_check']['status']!='pass' or callbacks!=['0x1800068e0','0x180006a90'] or len(actual)!=ACTIVE or production!=actual:
    mismatch=sum(a!=b for a,b in zip(actual,production)); raise RuntimeError(f'{family} case {i} differs ({mismatch} bytes), rc={rc}, status={m["status"]}, model={m["callback_model_check"]["status"]}, callbacks={callbacks}, len={len(actual)}')
   rows.append({'family':family,'front_strength':front,'front_alpha_fade':ffade,'front_sharp_tail':fsharp,'back_strength':back,'back_alpha_fade':bfade,'back_sharp_tail':bsharp,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':callbacks})
 source_text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 for token in ('pf16_fade_sharp_family_exact','olm_dblur_full_argb16'):
  if token not in source_text: raise RuntimeError(f'missing production token {token}')
 report={'schema_version':1,'status':'exact_bounded_families','plugin':'OLMDirectionalBlur','depth':'PF16','fixed_route':{'geometry':'16x16 padded ARGB64','angle':45,'brightness_gain':1,'size_variation':0,'noise_variation':0,'render_scale':[1,1]},'representatives':rows,'families':{'Front Alpha Fade':[0,50,100],'Front Sharp Tail':[0,50,100],'Back Alpha Fade':[0,50,100],'Back Sharp Tail':[0,50,100],'natural_cross':{'back_alpha_fade':50,'back_sharp_tail':50}},'quantization':'Input words are normalized by 32768, the same float gaussian/prepass/component/accum/max rowdriver is used, and output truncates normalized channels after multiplication by 32768.','admission':'Only the listed fixed-route representatives are admitted.','not_proven':['other geometry','other values','other combinations','PF8/PF32 inference','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur PF16 Fade/Sharp families — 2026-08-11\n\nActual Windows AEX and the production ARGB64 worker are raw-byte exact for Front/Back Fade and Sharp Tail 0/50/100 plus Back Fade 50 × Back Sharp 50 on the pinned 16×16 route. The worker preserves PF16 normalization, float accumulation/max, and truncating 32768 quantization. Admission is enumeration-bounded.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_pf16_fade_sharp_families_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_PF16_FADE_SHARP_FAMILIES cases=11 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
