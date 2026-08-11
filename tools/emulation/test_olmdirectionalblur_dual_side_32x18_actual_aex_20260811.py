#!/usr/bin/env python3
"""Promote the proven simultaneous Front+Back tuples to padded 32x18."""
from __future__ import annotations
import ctypes, hashlib, json, os, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
PRODUCTION=ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_dual_side_32x18_actual_aex_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_dual_side_32x18_actual_aex_20260811.md'
TUPLES=((50,50,100,100,0,25,1),(50,100,50,50,50,100,2),(100,50,50,100,0,100,2),(100,100,100,50,50,25,1))
W,H=32,18

def actual(temp:Path,src:Path,depth:int,index:int,t:tuple[int,...])->tuple[bytes,dict]:
 ff,fs,bf,bs,size,nv,noise_type=t; pad={8:12,16:16,32:32}[depth]
 meta=temp/f'pf{depth}_{index}.json'; out=temp/f'pf{depth}_{index}.raw'
 cmd=[sys.executable,str(FIXTURE),'--source',str(src),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth',str(depth),'--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation',str(size),'--front-alpha-fade',str(ff),'--front-sharp-tail',str(fs),'--back-strength','8','--back-alpha-fade',str(bf),'--back-sharp-tail',str(bs),'--noise-variation',str(nv),'--noise-type',str(noise_type),'--seed','1','--noise-offset','0','--thickness','3','--world-area','0','0',str(W),str(H),'--row-padding',str(pad),'--no-detour-rotate','--max-instructions','40000000']
 run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 if run.returncode: raise RuntimeError(run.stderr)
 return out.read_bytes(),json.loads(meta.read_text())

def pf8_production(temp:Path,active:bytes,t:tuple[int,...])->bytes:
 ff,fs,bf,bs,size,nv,noise_type=t; array=','.join(str(x) for x in active); source=str(PRODUCTION).replace('"','\\"')
 cpp=temp/'pf8.cpp'; exe=temp/'pf8'
 cpp.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{source}"
#include <array>
#include <cstdio>
#include <cstdint>
int main(){{constexpr int W={W},H={H},RB=W*4+12;const std::uint8_t packed[]={{{array}}};std::array<std::uint8_t,RB*H> ib{{}},ob{{}};for(int y=0;y<H;y++)for(int x=0;x<W*4;x++)ib[y*RB+x]=packed[y*W*4+x];PF_EffectWorld in{{}},out{{}};in.data=(PF_PixelPtr)ib.data();in.rowbytes=RB;in.width=W;in.height=H;in.extent_hint={{0,0,W,H}};out.data=(PF_PixelPtr)ob.data();out.rowbytes=RB;out.width=W;out.height=H;out.extent_hint={{0,0,W,H}};OLMDirectionalBlurInfo i{{}};i.angle_deg=45;i.brightness_gain=1;i.front_strength=8;i.front_alpha_fade={ff};i.front_sharp_tail={fs};i.back_strength=8;i.back_alpha_fade={bf};i.back_sharp_tail={bs};i.size_variation={size};i.noise_variation={nv};i.noise_type={noise_type};i.seed=1;i.noise_offset=0;i.thickness=3;i.render_scale_x=1;i.render_scale_y=1;int exact=0;if(OLMDirectionalBlurTestRenderWorld(&in,&out,&i,8,&exact)!=PF_Err_NONE||!exact)return 2;for(int y=0;y<H;y++)for(int x=0;x<W*4;x++)std::printf("%02x",ob[y*RB+x]);}}''')
 sdk=subprocess.run(['xcrun','--show-sdk-path'],capture_output=True,text=True,check=True).stdout.strip()
 cmd=[os.environ.get('CXX','clang++'),'-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off','-Wno-unused-function','-Wno-unused-parameter','-ffunction-sections','-fdata-sections','-isysroot',sdk,'-I',str(ROOT/'Headers'),'-I',str(ROOT/'Headers/SP'),'-I',str(ROOT/'Util'),'-I',str(ROOT/'Resources'),str(cpp),str(ROOT/'core/dblur_frontonly.cpp'),str(ROOT/'core/dblur_rotate.cpp'),str(ROOT/'core/dblur_rowdriver.cpp'),str(ROOT/'core/dblur_field.cpp'),'-Wl,-dead_strip','-framework','Cocoa','-o',str(exe)]
 build=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 if build.returncode: raise RuntimeError(build.stderr)
 run=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
 if run.returncode: raise RuntimeError(run.stderr)
 return bytes.fromhex(run.stdout)

def main()->int:
 if sys.platform!='darwin': raise SystemExit('Mac-only actual-AEX/production differential')
 rows=[]
 with tempfile.TemporaryDirectory(prefix='olm_dblur_dual_32x18_') as raw:
  temp=Path(raw); image=Image.open(SOURCE).convert('RGBA').crop((472,262,472+W,262+H)); src=temp/'source.png'; image.save(src); pixels=list(image.get_flattened_data())
  active8=b''.join(bytes((p[3],p[0],p[1],p[2])) for p in pixels)
  for depth in (8,16,32):
   if depth==16: active=b''.join(struct.pack('<4H',p[3]*128,p[0]*128,p[1]*128,p[2]*128) for p in pixels); ctype=ctypes.c_uint16; symbol='olm_dblur_full_argb16'
   elif depth==32: active=b''.join(struct.pack('<4f',p[3]/255,p[0]/255,p[1]/255,p[2]/255) for p in pixels); ctype=ctypes.c_float; symbol='olm_dblur_full_argb32'
   else: active=active8
   lib=None; fn=None
   if depth!=8:
    lib=temp/f'lib{depth}.dylib'; build=subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC','core/dblur_frontonly.cpp','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','core/dblur_field.cpp','-o',str(lib)],cwd=ROOT,capture_output=True,text=True)
    if build.returncode: raise RuntimeError(build.stderr)
    fn=getattr(ctypes.CDLL(str(lib)),symbol); common=[ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_int,ctypes.c_int,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_int,ctypes.c_uint32,ctypes.c_int,ctypes.c_float]; fn.argtypes=[ctypes.POINTER(ctype),ctypes.POINTER(ctype)]+common+[ctypes.POINTER(ctype),ctypes.c_int]
   for index,t in enumerate(TUPLES):
    expected,m=actual(temp,src,depth,index,t); ff,fs,bf,bs,size,nv,noise_type=t
    if depth==8: production=pf8_production(temp,active,t)
    else:
     Words=ctype*(len(active)//ctypes.sizeof(ctype)); source=Words.from_buffer_copy(active); dst=Words()
     if depth==16: rc=fn(source,dst,W,H,8,ff,ctypes.c_float(fs),8,bf,ctypes.c_float(bs),ctypes.c_float(size),ctypes.c_float(1),ctypes.c_float(45),ctypes.c_float(nv),noise_type,1,0,ctypes.c_float(3),None,0)
     else: rc=fn(source,dst,W,H,8,ff,ctypes.c_float(fs),8,bf,ctypes.c_float(bs),ctypes.c_float(size),ctypes.c_float(45),ctypes.c_float(1),ctypes.c_float(nv),noise_type,1,0,ctypes.c_float(3),None,0)
     if rc: raise RuntimeError(f'PF{depth} tuple={index} rc={rc}')
     production=bytes(dst)
    mismatch=sum(a!=b for a,b in zip(expected,production)); callbacks=[x['callback'] for x in m['execution']['iterate_calls']]
    if len(expected)!=len(active) or mismatch or m['callback_model_check']['status']!='pass': raise RuntimeError(f'PF{depth} tuple={index} mismatch={mismatch}')
    calls=m['execution'].get('rowdriver_calls',[]); first=calls[0] if calls else {}
    rows.append({'depth':f'PF{depth}','tuple_index':index,'raw_sha256':hashlib.sha256(expected).hexdigest(),'byte_count':len(expected),'callbacks':callbacks,'rotate_entry_count':len(m['execution'].get('rotate_entry',[])),'rowdriver_call_count':len(calls),'rowdriver_ranges':[[c['row_start'],c['row_end']] for c in calls],'rowdriver_first_call':{k:first.get(k) for k in ('width','mode_plus_0x20','mode_branch','opacity_plus_0x2c','exponent_plus_0x30','divisor_plus_0x38','front_edge_plus_0x40','back_edge_plus_0x44','counts')}})
 report={'schema_version':1,'status':'exact_bounded_geometry_promotion','plugin':'OLMDirectionalBlur','geometry':[W,H],'depths':['PF8','PF16','PF32'],'fixed_route':{'angle':45,'front_strength':8,'back_strength':8,'brightness_gain':1,'seed':1,'offset':0,'thickness':3},'tuples':[{'front_fade':a,'front_sharp':b,'back_fade':c,'back_sharp':d,'size_variation':e,'noise_variation':f,'noise_type':g} for a,b,c,d,e,f,g in TUPLES],'representatives':rows,'rotated_work_partition':'32x18 expands to 40x40. The actual owner schedules 32 worker rows; rows 0..31 are processed and rows 32..39 retain the preseeded rotated-source destination before rotate-back. This matches the independently established PF32 32x18 geometry contract.','admission':'Only the same four dual-side tuples at 32x18 are newly admitted.','fail_closed':['other dual-side tuple','other geometry','Noise Type 3']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); NOTE.write_text('# OLMDirectionalBlur simultaneous Front + Back at 32×18 — 2026-08-11\n\nThe four dual-side higher-order tuples proven at 16×16 are raw exact at padded 32×18 for PF8/PF16/PF32 (12 cells). The rotated 40×40 work world follows the actual owner partition: 32 worker rows overwrite rows 0..31 while rows 32..39 retain the preseeded rotated destination before rotate-back. Admission remains tuple- and geometry-exact; Type 3 and other combinations remain fail-closed.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_dual_side_32x18_actual_aex_20260811.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_DUAL_SIDE_32X18 PF8=4 PF16=4 PF32=4 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
