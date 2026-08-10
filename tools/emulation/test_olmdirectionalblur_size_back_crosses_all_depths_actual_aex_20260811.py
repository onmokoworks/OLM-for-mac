#!/usr/bin/env python3
"""PF8/PF16 Size Variation x Back Fade/Sharp bounded crosses."""
from __future__ import annotations
import ctypes, hashlib, importlib.util, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py'
ALPHA=ROOT/'tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py'
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_size_back_crosses_all_depths_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_size_back_crosses_all_depths_actual_aex_20260811.md'
W=H=16
CASES=((25.0,50,0.0),(25.0,100,0.0),(50.0,50,0.0),(50.0,100,0.0),(100.0,50,0.0),(100.0,100,0.0),(50.0,0,50.0),(50.0,0,100.0))

def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise RuntimeError(name)
 module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def pf8_rows(temp:Path)->list[dict]:
 base=load(BASE,'dblur_back_pf8_base'); source=load(ALPHA,'dblur_back_pf8_alpha').build_input(); rows=[]
 for i,(size,fade,sharp) in enumerate(CASES):
  case=temp/f'pf8_{i}'; case.mkdir()
  actual,am=base.capture_actual(45.0,source,front_strength=0,back_strength=8,front_alpha_fade=0,front_sharp_tail=0.0,back_alpha_fade=fade,back_sharp_tail=sharp,size_variation=size,noise_variation=0.0,brightness_gain=1.0)
  mac,mm=base.capture_mac(source,case,45.0,front_strength=0,back_strength=8,front_alpha_fade=0,front_sharp_tail=0.0,back_alpha_fade=fade,back_sharp_tail=sharp,size_variation=size,noise_variation=0.0,brightness_gain=1.0)
  mismatch=sum(a!=b for a,b in zip(actual,mac))
  if len(actual)!=1024 or mismatch or mm['exact']!=1 or not am['natural_complete']: raise RuntimeError(f'PF8 size={size:g} fade={fade} sharp={sharp:g} mismatch={mismatch}')
  rows.append({'depth':'PF8','size_variation_percent':size,'back_alpha_fade':fade,'back_sharp_tail':sharp,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':[x['callback'] for x in am['iterate_calls']]})
 return rows

def pf16_rows(temp:Path)->list[dict]:
 image=Image.open(SOURCE).convert('RGBA').crop((472,262,488,278)); srcpath=temp/'source.png'; image.save(srcpath)
 packed=b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in image.get_flattened_data()); active=W*H*8
 lib=temp/'lib16.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
 if build.returncode: raise RuntimeError(build.stderr)
 fn=ctypes.CDLL(str(lib)).olm_dblur_full_argb16
 fn.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint16),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float,ctypes.POINTER(ctypes.c_uint16),ctypes.c_int]
 Words=ctypes.c_uint16*(active//2); source=Words.from_buffer_copy(packed); rows=[]
 for i,(size,fade,sharp) in enumerate(CASES):
  meta=temp/f'pf16_{i}.json'; out=temp/f'pf16_{i}.argb64'
  cmd=[sys.executable,str(FIXTURE),'--source',str(srcpath),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth','16','--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','0','--size-variation',str(int(size)),'--front-alpha-fade','0','--front-sharp-tail','0','--back-strength','8','--back-alpha-fade',str(fade),'--back-sharp-tail',str(int(sharp)),'--noise-variation','0','--noise-type','1','--seed','1','--noise-offset','0','--thickness','10','--world-area','0','0','16','16','--row-padding','16','--no-detour-rotate','--max-instructions','20000000']
  run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
  if run.returncode: raise RuntimeError(run.stderr)
  m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Words(); rc=fn(source,dst,W,H,0,0,ctypes.c_float(0),8,fade,ctypes.c_float(sharp),ctypes.c_float(size),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(0),1,1,0,ctypes.c_float(10),None,0); production=bytes(dst)
  callbacks=[x['callback'] for x in m['execution']['iterate_calls']]; mismatch=sum(a!=b for a,b in zip(actual,production))
  if rc or len(actual)!=active or mismatch or callbacks!=['0x1800068e0','0x180006a90']: raise RuntimeError(f'PF16 size={size:g} fade={fade} sharp={sharp:g} mismatch={mismatch}')
  rows.append({'depth':'PF16','size_variation_percent':size,'back_alpha_fade':fade,'back_sharp_tail':sharp,'byte_count':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':callbacks})
 return rows

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_size_back_') as raw:
  temp=Path(raw); rows=pf8_rows(temp)+pf16_rows(temp)
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 for token in ('size_back_combo_exact','pf16_size_back_cross_exact'):
  if token not in text: raise RuntimeError(f'missing {token}')
 report={'schema_version':1,'status':'exact_bounded_crosses','plugin':'OLMDirectionalBlur','depths':['PF8','PF16'],'fixed_route':{'geometry':'16x16 padded','angle':45,'brightness_gain':1,'front_strength':0,'back_strength':8,'front_coefficients':0,'noise':0,'render_scale':[1,1]},'representatives':rows,'admission':{'size_x_back_fade':{'size':[25,50,100],'fade':[50,100]},'size_x_back_sharp':{'size':[50],'sharp':[50,100]}},'coefficient_order':'Nonzero Size builds the shared component map/divisor; Back Fade prepass and Back Sharp coefficient then enter the float rowdriver with Size/100.','writers':{'PF8':'float*255 then integer truncation','PF16':'float*32768 then integer truncation'},'not_proven':['other values/geometry','front8+back8','noise or front coefficient combinations','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur Size × Back coefficients — 2026-08-11\n\nPF8 and PF16 actual Windows AEX outputs are raw-byte exact with production for Size 25/50/100 × Back Fade 50/100 and Size 50 × Back Sharp 50/100 on the fixed front0/back8 16×16 route. Component map/divisor is shared; Back prepass/Sharp coefficients enter afterward. PF8 truncates float×255 and PF16 truncates float×32768. Only these eight tuples per depth are admitted.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_size_back_crosses_all_depths_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_SIZE_BACK_CROSSES PF8=8 PF16=8 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
