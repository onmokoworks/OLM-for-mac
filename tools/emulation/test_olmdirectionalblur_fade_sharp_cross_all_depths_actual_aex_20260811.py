#!/usr/bin/env python3
"""Front/back Fade x Sharp Tail boundary crosses at PF8/PF16/PF32."""
from __future__ import annotations
import ctypes, hashlib, importlib.util, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py'
ALPHA=ROOT/'tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py'
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_fade_sharp_cross_all_depths_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_fade_sharp_cross_all_depths_actual_aex_20260811.md'
W=H=16; VALUES=(50,100)

def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise RuntimeError(name)
 module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def pf8_rows(temp:Path)->list[dict]:
 base=load(BASE,'dblur_fade_sharp_pf8_base'); source=load(ALPHA,'dblur_fade_sharp_pf8_alpha').build_input(); rows=[]
 for side in ('front','back'):
  for fade in VALUES:
   for sharp in VALUES:
    front,back=(8,0) if side=='front' else (0,8)
    ff,fs,bf,bs=(fade,float(sharp),0,0.0) if side=='front' else (0,0.0,fade,float(sharp))
    case=temp/f'pf8_{side}_{fade}_{sharp}'; case.mkdir()
    actual,am=base.capture_actual(45.0,source,front_strength=front,back_strength=back,front_alpha_fade=ff,front_sharp_tail=fs,back_alpha_fade=bf,back_sharp_tail=bs,size_variation=0.0,noise_variation=0.0,brightness_gain=1.0)
    mac,mm=base.capture_mac(source,case,45.0,front_strength=front,back_strength=back,front_alpha_fade=ff,front_sharp_tail=fs,back_alpha_fade=bf,back_sharp_tail=bs,size_variation=0.0,noise_variation=0.0,brightness_gain=1.0)
    mismatch=sum(a!=b for a,b in zip(actual,mac))
    if len(actual)!=W*H*4 or mismatch or mm['exact']!=1 or not am['natural_complete']: raise RuntimeError(f'PF8 {side} fade={fade} sharp={sharp} mismatch={mismatch}')
    rows.append({'depth':'PF8','side':side,'alpha_fade':fade,'sharp_tail':sharp,'raw_sha256':hashlib.sha256(actual).hexdigest()})
 return rows

def typed_rows(temp:Path,depth:int)->list[dict]:
 image=Image.open(SOURCE).convert('RGBA').crop((472,262,488,278)); srcpath=temp/'source.png'; image.save(srcpath)
 if depth==16:
  active=b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in image.get_flattened_data()); ctype=ctypes.c_uint16; symbol='olm_dblur_full_argb16'; pad=16; callbacks=['0x1800068e0','0x180006a90']
 else:
  active=b''.join(struct.pack('<4f',p[3]/255,p[0]/255,p[1]/255,p[2]/255) for p in image.get_flattened_data()); ctype=ctypes.c_float; symbol='olm_dblur_full_argb32'; pad=32; callbacks=['0x180006a20','0x180006bd0']
 lib=temp/f'lib{depth}.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
 if build.returncode: raise RuntimeError(build.stderr)
 fn=getattr(ctypes.CDLL(str(lib)),symbol); common=[ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float]
 fn.argtypes=[ctypes.POINTER(ctype),ctypes.POINTER(ctype)]+common+[ctypes.POINTER(ctype),ctypes.c_int]
 Words=ctype*(len(active)//ctypes.sizeof(ctype)); source=Words.from_buffer_copy(active); rows=[]
 for side in ('front','back'):
  for fade in VALUES:
   for sharp in VALUES:
    front,back=(8,0) if side=='front' else (0,8); ff,fs,bf,bs=(fade,float(sharp),0,0.0) if side=='front' else (0,0.0,fade,float(sharp))
    meta=temp/f'pf{depth}_{side}_{fade}_{sharp}.json'; out=temp/f'pf{depth}_{side}_{fade}_{sharp}.raw'
    cmd=[sys.executable,str(FIXTURE),'--source',str(srcpath),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth',str(depth),'--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength',str(front),'--size-variation','0','--front-alpha-fade',str(ff),'--front-sharp-tail',str(int(fs)),'--back-strength',str(back),'--back-alpha-fade',str(bf),'--back-sharp-tail',str(int(bs)),'--noise-variation','0','--noise-type','1','--seed','1','--noise-offset','0','--thickness','10','--world-area','0','0','16','16','--row-padding',str(pad),'--no-detour-rotate','--max-instructions','20000000']
    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    if run.returncode: raise RuntimeError(run.stderr)
    m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Words()
    if depth==16: rc=fn(source,dst,W,H,front,ff,ctypes.c_float(fs),back,bf,ctypes.c_float(bs),ctypes.c_float(0),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(0),1,1,0,ctypes.c_float(10),None,0)
    else: rc=fn(source,dst,W,H,front,ff,ctypes.c_float(fs),back,bf,ctypes.c_float(bs),ctypes.c_float(0),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(0),1,1,0,ctypes.c_float(10),None,0)
    production=bytes(dst); mismatch=sum(a!=b for a,b in zip(actual,production)); observed=[x['callback'] for x in m['execution']['iterate_calls']]
    if rc or len(actual)!=len(active) or mismatch or observed!=callbacks: raise RuntimeError(f'PF{depth} {side} fade={fade} sharp={sharp} rc={rc} mismatch={mismatch} callbacks={observed}')
    rows.append({'depth':f'PF{depth}','side':side,'alpha_fade':fade,'sharp_tail':sharp,'raw_sha256':hashlib.sha256(actual).hexdigest(),'callbacks':observed})
 return rows

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_fade_sharp_cross_') as raw:
  temp=Path(raw); rows=pf8_rows(temp)+typed_rows(temp,16)+typed_rows(temp,32)
 text=(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text()
 for token in ('fade_sharp_cross_exact','olm_dblur_full_argb16','olm_dblur_full_argb32'):
  if token not in text: raise RuntimeError(f'missing production token {token}')
 report={'schema_version':1,'status':'exact_bounded_crosses','plugin':'OLMDirectionalBlur','depths':['PF8','PF16','PF32'],'fixed_route':{'geometry':'16x16 padded','angle':45,'brightness_gain':1,'size_variation':0,'noise_variation':0,'render_scale':[1,1]},'matrix':{'side':['front','back'],'alpha_fade':[50,100],'sharp_tail':[50,100]},'representatives':rows,'admission':'Only these 24 fixed-route cells are newly admitted; neighboring values and higher-order intersections remain fail-closed.','not_proven':['other values or geometry','front and back simultaneously nonzero','size/noise intersections','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur Fade × Sharp Tail boundary matrix — 2026-08-11\n\nActual Windows AEX and production are exact for Front-only and Back-only Fade 50/100 × Sharp Tail 50/100 at PF8/PF16/PF32 on the pinned 16×16 route. PF8/PF16 are raw-byte exact; PF32 is raw-float-word exact. Admission is restricted to these 24 cells.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_fade_sharp_cross_all_depths_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_FADE_SHARP_CROSS PF8=8 PF16=8 PF32=8 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
