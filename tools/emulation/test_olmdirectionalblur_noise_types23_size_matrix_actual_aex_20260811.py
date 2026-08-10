#!/usr/bin/env python3
"""PF16/PF32 Type-2/3 Noise Variation x Size matrix."""
from __future__ import annotations
import ctypes, hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_noise_types23_size_matrix_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_noise_types23_size_matrix_actual_aex_20260811.md'
W=H=16; MATRIX=((2,25.0,0.0),(2,25.0,50.0),(2,100.0,0.0),(2,100.0,50.0),(3,25.0,0.0),(3,25.0,50.0),(3,100.0,0.0),(3,100.0,50.0))

def padded(active:bytes,pixel_size:int,pad:int)->bytes:
 rb=W*pixel_size+pad; out=bytearray(rb*H)
 for y in range(H): out[y*rb:y*rb+W*pixel_size]=active[y*W*pixel_size:(y+1)*W*pixel_size]
 return bytes(out)

def main()->int:
 image=Image.open(SOURCE).convert('RGBA').crop((472,262,488,278)); pixels=list(image.get_flattened_data())
 packed16=b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in pixels)
 packed32=b''.join(struct.pack('<4f',p[3]/255,p[0]/255,p[1]/255,p[2]/255) for p in pixels)
 with tempfile.TemporaryDirectory(prefix='olm_dblur_noise23_size_') as raw:
  t=Path(raw); src=t/'source.png'; image.save(src)
  lib=t/'lib.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
  if build.returncode: raise RuntimeError(build.stderr)
  dylib=ctypes.CDLL(str(lib)); f16=dylib.olm_dblur_full_argb16; f32=dylib.olm_dblur_minimal_argb32
  f16.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint16),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float,ctypes.POINTER(ctypes.c_uint16),ctypes.c_int]
  f32.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_float),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float,ctypes.POINTER(ctypes.c_float),ctypes.c_int]
  W16=ctypes.c_uint16*(len(packed16)//2); W32=ctypes.c_float*(len(packed32)//4); source16=W16.from_buffer_copy(packed16); source32=W32.from_buffer_copy(packed32)
  layer16bytes=padded(packed16,8,16); layer32bytes=padded(packed32,16,32); L16=ctypes.c_ubyte*len(layer16bytes); L32=ctypes.c_ubyte*len(layer32bytes); layer16=L16.from_buffer_copy(layer16bytes); layer32=L32.from_buffer_copy(layer32bytes)
  rows=[]
  for depth in (16,32):
   active=packed16 if depth==16 else packed32; pad=16 if depth==16 else 32; expected_callbacks=['0x1800068e0','0x180006a90'] if depth==16 else ['0x180006a20','0x180006bd0']
   for i,(noise_type,nv,size) in enumerate(MATRIX):
    meta=t/f'd{depth}_{i}.json'; out=t/f'd{depth}_{i}.raw'
    cmd=[sys.executable,str(FIXTURE),'--source',str(src),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth',str(depth),'--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation',str(int(size)),'--front-alpha-fade','0','--front-sharp-tail','0','--back-strength','0','--back-alpha-fade','0','--back-sharp-tail','0','--noise-variation',str(int(nv)),'--noise-type',str(noise_type),'--seed','1','--noise-offset','0','--thickness','3','--world-area','0','0','16','16','--row-padding',str(pad),'--no-detour-rotate','--max-instructions','20000000']
    if noise_type==3: cmd += ['--noise-layer-row-padding',str(pad),'--noise-layer-origin','0','0']
    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    if run.returncode: raise RuntimeError(run.stderr)
    m=json.loads(meta.read_text()); actual=out.read_bytes()
    if depth==16:
     dst=W16(); lp=ctypes.cast(layer16,ctypes.POINTER(ctypes.c_uint16)) if noise_type==3 else None; lrb=W*8+16 if noise_type==3 else 0
     rc=f16(source16,dst,W,H,8,0,ctypes.c_float(0),0,0,ctypes.c_float(0),ctypes.c_float(size),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(nv),noise_type,1,0,ctypes.c_float(3),lp,lrb)
    else:
     dst=W32(); lp=ctypes.cast(layer32,ctypes.POINTER(ctypes.c_float)) if noise_type==3 else None; lrb=W*16+32 if noise_type==3 else 0
     rc=f32(source32,dst,W,H,8,0,ctypes.c_float(size),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(nv),noise_type,1,0,ctypes.c_float(3),lp,lrb)
    production=bytes(dst); callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; mismatch=sum(a!=b for a,b in zip(actual,production))
    if rc or len(actual)!=len(active) or mismatch or callbacks!=expected_callbacks or m['callback_model_check']['status']!='pass': raise RuntimeError(f'PF{depth} type={noise_type} nv={nv:g} size={size:g} mismatch={mismatch}')
    rows.append({'depth':f'PF{depth}','noise_type':noise_type,'noise_variation_percent':nv,'size_variation_percent':size,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':callbacks,'noise_layer_contract':{'dimensions':m['world_layout']['noise_layer_dimensions'],'rowbytes':m['world_layout']['noise_layer_rowbytes'],'origin':m['world_layout']['noise_layer_extent_hint'][:2]} if noise_type==3 else None})
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 for token in ('pf16_noise_size_exact','pf32_noise_size_exact'):
  if token not in text: raise RuntimeError(f'missing {token}')
 report={'schema_version':1,'status':'exact_bounded_matrix','plugin':'OLMDirectionalBlur','depths':['PF16','PF32'],'fixed_route':{'geometry':'16x16 padded','angle':45,'brightness_gain':1,'front_strength':8,'back_strength':0,'fade_sharp':0,'seed':1,'offset':0,'thickness':3,'render_scale':[1,1]},'matrix':{'noise_type':[2,3],'noise_variation':[25,100],'size_variation':[0,50]},'representatives':rows,'branches':{'Type2':'generated block-noise plane; Noise Layer checkout is not consumed','Type3':'checked-out same-size Layer world; active rowbytes may be padded and local origin is 0,0'},'admission':'Only the 2x2x2 matrix per depth and fixed route is admitted. Type3 requires non-null same-size world and sufficient rowbytes.','not_proven':['other NV/Size values','other world dimensions/origin semantics','fade/sharp/back combinations','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur PF16/PF32 Noise Type 2/3 × Size — 2026-08-11\n\nActual AEX and production are raw-byte exact for Noise Variation 25/100 × Size 0/50 in both Type 2 (generated Block noise) and Type 3 (Layer) at PF16/PF32. Type 3 requires a non-null 16×16 Layer world with sufficient padded rowbytes and local origin 0,0; Type 2 does not consume it. Only this matrix is admitted.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_types23_size_matrix_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_NOISE23_SIZE_MATRIX PF16=8 PF32=8 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
