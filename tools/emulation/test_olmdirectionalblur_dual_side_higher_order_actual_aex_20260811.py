#!/usr/bin/env python3
"""Simultaneous Front+Back coefficient/noise/size matrix at all depths."""
from __future__ import annotations
import ctypes, hashlib, importlib.util, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py'
ALPHA=ROOT/'tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py'
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_dual_side_higher_order_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_dual_side_higher_order_actual_aex_20260811.md'
TUPLES=((50,50,100,100,0,25,1),(50,100,50,50,50,100,2),(100,50,50,100,0,100,2),(100,100,100,50,50,25,1))
W=H=16

def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise RuntimeError(name)
 module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def row(depth:str,t:tuple[int,...],raw:bytes,callbacks:list[str])->dict:
 ff,fs,bf,bs,size,nv,noise_type=t
 return {'depth':depth,'front_alpha_fade':ff,'front_sharp_tail':fs,'back_alpha_fade':bf,
         'back_sharp_tail':bs,'size_variation_percent':size,'noise_variation_percent':nv,
         'noise_type':noise_type,'raw_sha256':hashlib.sha256(raw).hexdigest(),'callbacks':callbacks}

def pf8_rows(temp:Path)->list[dict]:
 base=load(BASE,'dblur_dual_pf8_base'); source=load(ALPHA,'dblur_dual_pf8_alpha').build_input(); rows=[]
 for i,t in enumerate(TUPLES):
  ff,fs,bf,bs,size,nv,noise_type=t; case=temp/f'pf8_{i}'; case.mkdir()
  kw=dict(front_strength=8,back_strength=8,front_alpha_fade=ff,front_sharp_tail=float(fs),
          back_alpha_fade=bf,back_sharp_tail=float(bs),size_variation=float(size),
          noise_variation=float(nv),noise_type=noise_type,seed=1,noise_offset=0,
          thickness=3.0,brightness_gain=1.0)
  actual,am=base.capture_actual(45.0,source,**kw); mac,mm=base.capture_mac(source,case,45.0,**kw)
  mismatch=sum(a!=b for a,b in zip(actual,mac))
  if len(actual)!=W*H*4 or mismatch or mm['exact']!=1 or not am['natural_complete']:
   raise RuntimeError(f'PF8 tuple={i} mismatch={mismatch} exact={mm["exact"]}')
  rows.append(row('PF8',t,actual,[x['callback'] for x in am['iterate_calls']]))
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
 for i,t in enumerate(TUPLES):
  ff,fs,bf,bs,size,nv,noise_type=t; meta=temp/f'pf{depth}_{i}.json'; out=temp/f'pf{depth}_{i}.raw'
  cmd=[sys.executable,str(FIXTURE),'--source',str(srcpath),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth',str(depth),'--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation',str(size),'--front-alpha-fade',str(ff),'--front-sharp-tail',str(fs),'--back-strength','8','--back-alpha-fade',str(bf),'--back-sharp-tail',str(bs),'--noise-variation',str(nv),'--noise-type',str(noise_type),'--seed','1','--noise-offset','0','--thickness','3','--world-area','0','0','16','16','--row-padding',str(pad),'--no-detour-rotate','--max-instructions','30000000']
  run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
  if run.returncode: raise RuntimeError(run.stderr)
  m=json.loads(meta.read_text()); actual=out.read_bytes(); dst=Words()
  if depth==16: rc=fn(source,dst,W,H,8,ff,ctypes.c_float(fs),8,bf,ctypes.c_float(bs),ctypes.c_float(size),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(nv),noise_type,1,0,ctypes.c_float(3),None,0)
  else: rc=fn(source,dst,W,H,8,ff,ctypes.c_float(fs),8,bf,ctypes.c_float(bs),ctypes.c_float(size),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(nv),noise_type,1,0,ctypes.c_float(3),None,0)
  production=bytes(dst); mismatch=sum(a!=b for a,b in zip(actual,production)); observed=[x['callback'] for x in m['execution']['iterate_calls']]
  if rc or len(actual)!=len(active) or mismatch or observed!=callbacks or m['callback_model_check']['status']!='pass':
   raise RuntimeError(f'PF{depth} tuple={i} rc={rc} mismatch={mismatch} callbacks={observed}')
  rows.append(row(f'PF{depth}',t,actual,observed))
 return rows

def main()->int:
 if sys.platform!='darwin': raise SystemExit('Mac-only actual-AEX/production differential')
 with tempfile.TemporaryDirectory(prefix='olm_dblur_dual_side_higher_') as raw:
  temp=Path(raw); rows=pf8_rows(temp)+typed_rows(temp,16)+typed_rows(temp,32)
 if 'DualSideHigherOrderTuple' not in (ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp').read_text(): raise RuntimeError('bounded predicate absent')
 report={'schema_version':1,'status':'exact_bounded_dual_side_higher_order','plugin':'OLMDirectionalBlur','depths':['PF8','PF16','PF32'],'fixed_route':{'geometry':'16x16 padded','angle':45,'brightness_gain':1,'front_strength':8,'back_strength':8,'seed':1,'offset':0,'thickness':3,'render_scale':[1,1]},'matrix':{'tuples':[{'front_fade':a,'front_sharp':b,'back_fade':c,'back_sharp':d,'size_variation':e,'noise_variation':f,'noise_type':g} for a,b,c,d,e,f,g in TUPLES]},'representatives':rows,'admission':'Only these 12 simultaneous Front+Back fixed-route cells are newly admitted.','fail_closed':['unlisted simultaneous-side tuple','other geometry','Noise Type 3'],'not_proven':['other values or combinations','native AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text('# OLMDirectionalBlur simultaneous Front + Back higher-order matrix — 2026-08-11\n\nActual Windows AEX and production are exact for four simultaneous Front+Back tuples at PF8/PF16/PF32 (12 cells). The fixed 16×16 route covers both-side Fade/Sharp 50/100 with Size 0/50, Noise Variation 25/100, and Noise Type 1/2. PF8/PF16 are raw-byte exact; PF32 is raw-float-word exact. Unlisted tuples, other geometry, and Type 3 remain fail-closed.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_dual_side_higher_order_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_DUAL_SIDE_HIGHER_ORDER PF8=4 PF16=4 PF32=4 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
