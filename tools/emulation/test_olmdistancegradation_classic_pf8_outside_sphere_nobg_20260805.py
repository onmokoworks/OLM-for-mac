#!/usr/bin/env python3
import hashlib,struct,subprocess,tempfile,sys,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';sys.path.insert(0,str(HERE))
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_fieldgen_p1b import make_mask
from test_dg_compose import make_loader,alloc_refcon,OFF_SRC_WORLD_PTR,OFF_FIELD_WORLD_PTR,OFF_DEGENERATE,OFF_USE_BG,OFF_INVERT,OFF_INOUT_MODE,OFF_RENDER_MODE,OFF_INTERP_MODE,OFF_POWER,OFF_GRAD_G,OFF_GRAD_R,OFF_GRAD_B,OFF_BG_G,OFF_BG_R,OFF_BG_B
FUN=0x181170870;W,H,IRB,ORB=17,11,75,79;HARNESS=HERE/'dg_classic_pf8_outside_sphere_nobg_harness_20260805.cpp'
def world(ld,pixels):
 data=ld.bump_alloc(W*H*4,align=64);ld.write_bytes(data,pixels);w=ld.host_alloc(0x80,align=16);ld.write_bytes(w,b'\0'*0x80)
 for o,v in ((0x18,struct.pack('<Q',data)),(0x20,struct.pack('<I',W*4)),(0x24,struct.pack('<I',W)),(0x28,struct.pack('<I',H))):ld.write_bytes(w+o,v)
 return w
def actual(invert,layer=False,power=False):
 mask=make_mask(W,H)
 if power:mask=np.ones((H,W),dtype=np.uint8);mask[2:9,4:13]=0
 field,trace=run_aex_fieldgen((mask==0).astype(np.uint8),4,0);staged=np.rint(np.clip(field,0,1)*255).astype(np.uint8);src=[]
 for y in range(H):
  for x in range(W):src.append((255,(x*13+y*3)%256,(x*7+y*19)%256,(x*23+y*5)%256) if mask[y,x] else (0,0,0,0))
 ld=make_loader();ld.register_libm_impls(max_threads=1);sw=world(ld,b''.join(bytes(p) for p in src));fw=world(ld,b''.join(bytes((0,int(staged[y,x]),0,0)) for y in range(H) for x in range(W)));ref=alloc_refcon(ld)
 def put(o,f,v):ld.write_bytes(ref+o,struct.pack(f,v))
 for o,f,v in ((OFF_SRC_WORLD_PTR,'<Q',sw),(OFF_FIELD_WORLD_PTR,'<Q',fw),(OFF_DEGENERATE,'<B',0),(OFF_USE_BG,'<B',0),(OFF_INVERT,'<B',invert),(OFF_INOUT_MODE,'<i',2),(OFF_RENDER_MODE,'<i',2 if layer else 1),(OFF_INTERP_MODE,'<i',4 if power else 3),(OFF_POWER,'<f',2.5 if power else 1.0),(OFF_GRAD_G,'<f',0.0),(OFF_GRAD_R,'<f',28/255),(OFF_GRAD_B,'<f',238/255),(OFF_BG_G,'<f',0.0),(OFF_BG_R,'<f',1.0),(OFF_BG_B,'<f',0.0)):put(o,f,v)
 out=[]
 for y in range(H):
  for x in range(W):
   p=ld.bump_alloc(4,align=8);ld.write_bytes(p,b'\xee'*4);ld.call_function(FUN,int_args=[ref,x,y,0,p],max_instructions=200000);out.append(tuple(ld.read_bytes(p,4)))
 return field,trace,src,out
def main():
 layer=os.environ.get('OLM_DG_CLASSIC_LAYER')=='1';power=os.environ.get('OLM_DG_CLASSIC_POWER')=='1';cases=[]
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);exe=t/'h';q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HARNESS),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr
  for invert in (0,1):
   field,trace,src,out=actual(invert,layer,power);source=b''.join(bytes((a,r,g,b)) for a,g,r,b in src);active=b''.join(bytes((a,r,g,b)) for a,g,r,b in out);srcpad=b''.join(source[y*68:(y+1)*68]+b'\xa5'*7 for y in range(H));expected=b''.join(active[y*68:(y+1)*68]+b'\xa5'*11 for y in range(H));a=t/f's{invert}';b=t/f'e{invert}';a.write_bytes(srcpad);b.write_bytes(expected);args=[str(exe),str(a),str(b)]+(['invert'] if invert else [])+(['layer'] if layer else [])+(['power'] if power else []);q=subprocess.run(args,capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='');cases.append((invert,hashlib.sha256(field.astype('<f4').tobytes()).hexdigest(),hashlib.sha256(active).hexdigest(),len(trace)))
 expected_power=[(0,'b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112','7e0dbb8fa472c312739a05818eb676142377219d969ae6028ad1ea664d4577ea',3),(1,'b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112','8eb17bd878f953edb4139df5144bcd64a58e3bf9d80df87c67fe13236fdeea38',3)];expected_layer=[(0,'f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229','13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf',3),(1,'f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229','e75997a208f073394cb11b7ce5a1f44f19f9af312f378fdcce2963c814d0d090',3)];expected_rgb=[(0,'f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229','2a5da60c5858360fe2bb6cd34e275eab368e73eebc6d0d0dc8afb34105392d19',3),(1,'f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229','5523ca4d6859e4c008a0c1479640f2530090fb60fd5d04b844c06bb3a7fa1c77',3)];assert cases==(expected_power if power else expected_layer if layer else expected_rgb);print('cases',cases);print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_OUTSIDE_POWER_NOBG_RGB_BOTH_INVERT_EXACT' if power else 'PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_OUTSIDE_SPHERE_NOBG_LAYER_BOTH_INVERT_EXACT' if layer else 'PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_OUTSIDE_SPHERE_NOBG_BOTH_INVERT_EXACT')
if __name__=='__main__':raise SystemExit(main())
