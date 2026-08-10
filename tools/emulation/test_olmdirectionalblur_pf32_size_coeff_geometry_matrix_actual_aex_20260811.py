#!/usr/bin/env python3
"""PF32 Size x front/back Fade/Sharp matrix at two practical geometries."""
from __future__ import annotations
import ctypes, hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_pf32_size_coeff_geometry_matrix_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_pf32_size_coeff_geometry_matrix_actual_aex_20260811.md'
GEOMETRIES=((16,16),(32,18))
FADE_CROSS=tuple((s,f,0.0) for s in (25.0,50.0,100.0) for f in (50,100))
SHARP_CROSS=((50.0,0,50.0),(50.0,0,100.0))

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_pf32_coeff_geometry_') as raw:
  t=Path(raw); lib=t/'lib.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
  if build.returncode: raise RuntimeError(build.stderr)
  fn=ctypes.CDLL(str(lib)).olm_dblur_full_argb32
  fn.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_float),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float,ctypes.POINTER(ctypes.c_float),ctypes.c_int]
  rows=[]
  for w,h in GEOMETRIES:
   image=Image.open(SOURCE).convert('RGBA').crop((472,262,472+w,262+h)); srcpath=t/f'source_{w}x{h}.png'; image.save(srcpath)
   packed=b''.join(struct.pack('<4f',p[3]/255,p[0]/255,p[1]/255,p[2]/255) for p in image.get_flattened_data()); Floats=ctypes.c_float*(len(packed)//4); source=Floats.from_buffer_copy(packed)
   cases=[]
   for size,fade,sharp in FADE_CROSS+SHARP_CROSS: cases.append(('front',size,fade,sharp,8,0,0,0.0))
   for size,fade,sharp in FADE_CROSS+SHARP_CROSS: cases.append(('back',size,0,0.0,0,8,fade,sharp))
   for i,(side,size,ffade,fsharp,front,back,bfade,bsharp) in enumerate(cases):
    meta=t/f'{w}x{h}_{i}.json'; out=t/f'{w}x{h}_{i}.argb128'
    cmd=[sys.executable,str(FIXTURE),'--source',str(srcpath),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth','32','--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength',str(front),'--size-variation',str(int(size)),'--front-alpha-fade',str(ffade),'--front-sharp-tail',str(int(fsharp)),'--back-strength',str(back),'--back-alpha-fade',str(bfade),'--back-sharp-tail',str(int(bsharp)),'--noise-variation','0','--noise-type','1','--seed','1','--noise-offset','0','--thickness','10','--world-area','0','0',str(w),str(h),'--row-padding','32','--no-detour-rotate','--max-instructions','30000000']
    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    if run.returncode: raise RuntimeError(run.stderr)
    m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Floats(); rc=fn(source,dst,w,h,front,ffade,ctypes.c_float(fsharp),back,bfade,ctypes.c_float(bsharp),ctypes.c_float(size),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(0),1,1,0,ctypes.c_float(10),None,0); production=bytes(dst); callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; mismatch=sum(a!=b for a,b in zip(actual,production))
    if rc or len(actual)!=w*h*16 or mismatch or callbacks!=['0x180006a20','0x180006bd0'] or m['callback_model_check']['status']!='pass':
     pairs=list(zip(struct.iter_unpack('<f',actual),struct.iter_unpack('<f',production))); changed=[(j,abs(a[0]-b[0])) for j,(a,b) in enumerate(pairs) if a[0]!=b[0]]; deltas=[d for _,d in changed]
     raise RuntimeError(f'{w}x{h} {side} size={size:g} fade={ffade or bfade} sharp={fsharp or bsharp:g} mismatch={mismatch} float_words={len(deltas)} max_delta={max(deltas) if deltas else 0} component={m["execution"].get("component_map_probe")}')
    rows.append({'geometry':[w,h],'side':side,'size_variation_percent':size,'alpha_fade':ffade or bfade,'sharp_tail':fsharp or bsharp,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':callbacks,'input_rowbytes':m['world_layout']['input_rowbytes']})
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 if 'pf32_size_coeff_cross_exact' not in text: raise RuntimeError('production predicate absent')
 report={'schema_version':1,'status':'exact_bounded_matrix','plugin':'OLMDirectionalBlur','depth':'PF32','geometries':[[16,16],[32,18]],'fixed_route':{'angle':45,'brightness_gain':1,'noise':0,'render_scale':[1,1]},'matrix':{'front_and_back_size_x_fade':{'size':[25,50,100],'fade':[50,100]},'front_and_back_size_x_sharp':{'size':[50],'sharp':[50,100]}},'representatives':rows,'coefficient_order':'Size builds component map/divisor; the selected front/back Fade prepass or Sharp coefficient then enters the shared float rowdriver. PF32 preserves raw float writer words.','rectangular_work_contract':'32x18 expands to a 40x40 work world. The AEX divides 40 rows across 32 workers, overwrites processed rows 0..31, and retains the rotated-source contents already present in destination rows 32..39 before rotate-back.','admission':'Only the listed tuples at 16x16 and 32x18 are admitted by the new cross predicate.','not_proven':['64x36 or other geometry','front and back simultaneously nonzero','noise combinations','other values','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur PF32 Size × Fade/Sharp geometry matrix — 2026-08-11\n\nActual AEX and production are raw-float exact at 16×16 and 32×18 for front-only and back-only Size 25/50/100 × Fade 50/100, plus Size 50 × Sharp 50/100. Size component mapping precedes the selected front/back prepass or Sharp coefficient. For 32×18, the 40×40 work world is divided among 32 workers: rows 0..31 are overwritten and rows 32..39 retain the rotated-source destination contents before rotate-back. The new admission is limited to these 32 cells.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_pf32_size_coeff_geometry_matrix_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_PF32_SIZE_COEFF_GEOMETRY cases=32 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
