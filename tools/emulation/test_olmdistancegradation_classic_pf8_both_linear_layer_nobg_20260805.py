#!/usr/bin/env python3
import hashlib,struct,subprocess,tempfile,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';sys.path.insert(0,str(HERE))
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_compose import make_loader,alloc_refcon,OFF_SRC_WORLD_PTR,OFF_FIELD_WORLD_PTR,OFF_DEGENERATE,OFF_USE_BG,OFF_INVERT,OFF_INOUT_MODE,OFF_RENDER_MODE,OFF_INTERP_MODE,OFF_POWER,OFF_GRAD_G,OFF_GRAD_R,OFF_GRAD_B,OFF_BG_G,OFF_BG_R,OFF_BG_B
FUN=0x181170870;W,H=17,11
def world(ld,pixels):
 data=ld.bump_alloc(W*H*4,align=64);ld.write_bytes(data,pixels);w=ld.host_alloc(0x80,align=16);ld.write_bytes(w,b'\0'*0x80)
 for o,v in ((0x18,struct.pack('<Q',data)),(0x20,struct.pack('<I',W*4)),(0x24,struct.pack('<I',W)),(0x28,struct.pack('<I',H))):ld.write_bytes(w+o,v)
 return w
def main():
 mask=np.ones((H,W),dtype=np.uint8);mask[2:9,4:13]=0;inside,ti=run_aex_fieldgen(mask,6,0);outside,to=run_aex_fieldgen((mask==0).astype(np.uint8),5,0);field=np.maximum(inside,outside);staged=np.rint(np.clip(field,0,1)*255).astype(np.uint8);src=[(255,(x*13+y*3)%256,(x*7+y*19)%256,(x*23+y*5)%256) if mask[y,x] else (0,0,0,0) for y in range(H) for x in range(W)];ld=make_loader();ld.register_libm_impls(max_threads=1);sw=world(ld,b''.join(bytes(p) for p in src));fw=world(ld,b''.join(bytes((0,int(staged[y,x]),0,0)) for y in range(H) for x in range(W)));ref=alloc_refcon(ld)
 def put(o,f,v):ld.write_bytes(ref+o,struct.pack(f,v))
 for o,f,v in ((OFF_SRC_WORLD_PTR,'<Q',sw),(OFF_FIELD_WORLD_PTR,'<Q',fw),(OFF_DEGENERATE,'<B',0),(OFF_USE_BG,'<B',0),(OFF_INVERT,'<B',1),(OFF_INOUT_MODE,'<i',3),(OFF_RENDER_MODE,'<i',2),(OFF_INTERP_MODE,'<i',2),(OFF_POWER,'<f',1.0),(OFF_GRAD_G,'<f',0.0),(OFF_GRAD_R,'<f',28/255),(OFF_GRAD_B,'<f',238/255),(OFF_BG_G,'<f',160/255),(OFF_BG_R,'<f',16/255),(OFF_BG_B,'<f',48/255)):put(o,f,v)
 out=[]
 for y in range(H):
  for x in range(W):
   p=ld.bump_alloc(4,align=8);ld.write_bytes(p,b'\xee'*4);ld.call_function(FUN,int_args=[ref,x,y,0,p],max_instructions=200000);out.append(tuple(ld.read_bytes(p,4)))
 source=b''.join(bytes((a,r,g,b)) for a,g,r,b in src);active=b''.join(bytes((a,r,g,b)) for a,g,r,b in out);srcpad=b''.join(source[y*68:(y+1)*68]+b'\xa5'*7 for y in range(H));expected=b''.join(active[y*68:(y+1)*68]+b'\xa5'*11 for y in range(H));inside_sha=hashlib.sha256(inside.astype('<f4').tobytes()).hexdigest();outside_sha=hashlib.sha256(outside.astype('<f4').tobytes()).hexdigest();field_sha=hashlib.sha256(field.astype('<f4').tobytes()).hexdigest();output_sha=hashlib.sha256(active).hexdigest();assert (inside_sha,outside_sha,field_sha,output_sha)==('061454ff2adc6e3fafc7a1558143b2da7d9eb1cb2641eda95c70ac97908d18dc','b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112','a84f59f33fe82263d86280a3bf48ff6fac47b5e98376b95b9418aec0c47c3f3d','b9947fdf92cdae2fe6bcc4c0c4f117f677c1778d723d9e4086fcdae66ae19bcd');print('inside_sha256',inside_sha);print('outside_sha256',outside_sha);print('field_sha256',field_sha);print('output_active_sha256',output_sha);assert len(ti)==len(to)==3
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);a=t/'s';b=t/'e';exe=t/'h';a.write_bytes(srcpad);b.write_bytes(expected);q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HERE/'dg_classic_pf8_both_linear_layer_nobg_harness_20260805.cpp'),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr;q=subprocess.run([str(exe),str(a),str(b)],capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_BOTH_LINEAR_LAYER_NOBG_EXACT')
if __name__=='__main__':raise SystemExit(main())
