#!/usr/bin/env python3
"""PF16/PF32 public Noise-state pairwise crosses against the actual AEX owner."""
from __future__ import annotations
import ctypes, hashlib, itertools, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_noise_public_pairwise_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_noise_public_pairwise_actual_aex_20260811.md'
FACTORS=((1,2,3),(1,2),(0,1),(3,10),(25,100),('fade50','sharp50','size50'),((16,16),(32,18)))

def pairwise_rows():
 candidates=list(itertools.product(*FACTORS)); uncovered=set()
 for i in range(len(FACTORS)):
  for j in range(i+1,len(FACTORS)):
   uncovered.update((i,a,j,b) for a in FACTORS[i] for b in FACTORS[j])
 rows=[]
 while uncovered:
  best=max(candidates,key=lambda row:sum((i,row[i],j,row[j]) in uncovered for i in range(len(row)) for j in range(i+1,len(row))))
  rows.append(best); candidates.remove(best)
  uncovered.difference_update((i,best[i],j,best[j]) for i in range(len(best)) for j in range(i+1,len(best)))
 return rows

def padded(active:bytes,w:int,h:int,pixel_size:int,pad:int)->bytes:
 rb=w*pixel_size+pad; out=bytearray(rb*h)
 for y in range(h): out[y*rb:y*rb+w*pixel_size]=active[y*w*pixel_size:(y+1)*w*pixel_size]
 return bytes(out)

def main()->int:
 rowspec=pairwise_rows()
 with tempfile.TemporaryDirectory(prefix='olm_dblur_noise_pairwise_') as raw:
  t=Path(raw); lib=t/'lib.dylib'
  build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
  if build.returncode: raise RuntimeError(build.stderr)
  dylib=ctypes.CDLL(str(lib)); f16=dylib.olm_dblur_full_argb16; f32=dylib.olm_dblur_full_argb32
  common=[ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float]
  f16.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint16)]+common+[ctypes.POINTER(ctypes.c_uint16),ctypes.c_int]
  f32.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_float)]+common+[ctypes.POINTER(ctypes.c_float),ctypes.c_int]
  results=[]
  for depth in (16,32):
   pixel_size=8 if depth==16 else 16; pad=16 if depth==16 else 32
   expected=['0x1800068e0','0x180006a90'] if depth==16 else ['0x180006a20','0x180006bd0']
   for index,(noise_type,seed,offset,thickness,nv,coeff,geometry) in enumerate(rowspec):
    w,h=geometry; image=Image.open(SOURCE).convert('RGBA').crop((472,262,472+w,262+h)); src=t/f'source_{w}x{h}.png'; image.save(src)
    pixels=list(image.get_flattened_data())
    active=(b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in pixels) if depth==16 else b''.join(struct.pack('<4f',p[3]/255,p[0]/255,p[1]/255,p[2]/255) for p in pixels))
    fade=50 if coeff=='fade50' else 0; sharp=50.0 if coeff=='sharp50' else 0.0; size=50.0 if coeff=='size50' else 0.0
    meta=t/f'd{depth}_{index}.json'; out=t/f'd{depth}_{index}.raw'
    cmd=[sys.executable,str(FIXTURE),'--source',str(src),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth',str(depth),'--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation',str(int(size)),'--front-alpha-fade',str(fade),'--front-sharp-tail',str(int(sharp)),'--back-strength','0','--back-alpha-fade','0','--back-sharp-tail','0','--noise-variation',str(nv),'--noise-type',str(noise_type),'--seed',str(seed),'--noise-offset',str(offset),'--thickness',str(thickness),'--world-area','0','0',str(w),str(h),'--row-padding',str(pad),'--no-detour-rotate','--max-instructions','30000000']
    if noise_type==3: cmd += ['--noise-layer-row-padding',str(pad),'--noise-layer-origin','0','0']
    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    if run.returncode: raise RuntimeError(run.stderr)
    actual=out.read_bytes(); m=json.loads(meta.read_text()); layerbytes=padded(active,w,h,pixel_size,pad)
    if depth==16:
     Words=ctypes.c_uint16*(len(active)//2); Layer=ctypes.c_ubyte*len(layerbytes); source=Words.from_buffer_copy(active); dst=Words(); layer=Layer.from_buffer_copy(layerbytes)
     lp=ctypes.cast(layer,ctypes.POINTER(ctypes.c_uint16)) if noise_type==3 else None
     rc=f16(source,dst,w,h,8,fade,ctypes.c_float(sharp),0,0,ctypes.c_float(0),ctypes.c_float(size),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(nv),noise_type,seed,offset,ctypes.c_float(thickness),lp,w*pixel_size+pad if noise_type==3 else 0)
    else:
     Words=ctypes.c_float*(len(active)//4); Layer=ctypes.c_ubyte*len(layerbytes); source=Words.from_buffer_copy(active); dst=Words(); layer=Layer.from_buffer_copy(layerbytes)
     lp=ctypes.cast(layer,ctypes.POINTER(ctypes.c_float)) if noise_type==3 else None
     rc=f32(source,dst,w,h,8,fade,ctypes.c_float(sharp),0,0,ctypes.c_float(0),ctypes.c_float(size),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(nv),noise_type,seed,offset,ctypes.c_float(thickness),lp,w*pixel_size+pad if noise_type==3 else 0)
    production=bytes(dst); callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; mismatch=sum(a!=b for a,b in zip(actual,production))
    if rc or len(actual)!=len(active) or mismatch or callbacks!=expected or m['callback_model_check']['status']!='pass': raise RuntimeError(f'PF{depth} row={index} {noise_type,seed,offset,thickness,nv,coeff,geometry} rc={rc} mismatch={mismatch}')
    results.append({'depth':f'PF{depth}','noise_type':noise_type,'seed':seed,'offset':offset,'thickness':thickness,'noise_variation_percent':nv,'front_cross':coeff,'geometry':list(geometry),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':callbacks})
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 if 'noise_public_pairwise_exact' not in text: raise RuntimeError('production bounded pairwise predicate is absent')
 report={'schema_version':1,'status':'exact_pairwise_matrix','plugin':'OLMDirectionalBlur','depths':['PF16','PF32'],'fixed_route':{'angle':45,'brightness_gain':1,'front_strength':8,'back_strength':0,'render_scale':[1,1]},'factors':{'noise_type':[1,2,3],'seed':[1,2],'offset':[0,1],'thickness':[3,10],'noise_variation':[25,100],'front_cross':['Fade50','Sharp50','Size50'],'geometry':[[16,16],[32,18]]},'pairwise_rows':len(rowspec),'representatives':results,'layer_contract':'Type 3 uses the same deterministic source pixels in a same-size, fixed Layer world with independent padded rowbytes and local origin 0,0.','admission':'Only the emitted pairwise tuples at PF16/PF32 are admitted in addition to earlier exact matrices.','not_proven':['unlisted higher-order combinations','other values or geometry','back blur intersections','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text(f'# OLMDirectionalBlur public Noise pairwise matrix — 2026-08-11\n\nActual AEX owner and production are raw-byte exact for a {len(rowspec)}-row pairwise covering array at each of PF16/PF32. Factors cover Noise Type 1/2/3, Seed 1/2, Offset 0/1, Thickness 3/10, Noise Variation 25/100, Front Fade 50 / Sharp 50 / Size 50, and 16×16 / 32×18 geometry. Type 3 uses a same-size fixed Layer. Admission is tuple-exact; unlisted higher-order combinations remain fail-closed.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_public_pairwise_actual_aex_20260811.py`\n')
 print(f'PASS_OLMDIRECTIONALBLUR_NOISE_PUBLIC_PAIRWISE rows={len(rowspec)} per_depth={len(rowspec)} raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
