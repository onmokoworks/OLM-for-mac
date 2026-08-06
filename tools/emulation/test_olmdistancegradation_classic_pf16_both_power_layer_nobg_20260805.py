#!/usr/bin/env python3
import hashlib,struct,subprocess,tempfile,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';sys.path.insert(0,str(HERE))
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_compose import make_loader,build_world,call_compose,alloc_refcon,OFF_SRC_WORLD_PTR,OFF_FIELD_WORLD_PTR,OFF_DEGENERATE,OFF_USE_BG,OFF_INVERT,OFF_INOUT_MODE,OFF_RENDER_MODE,OFF_INTERP_MODE,OFF_POWER,OFF_GRAD_G,OFF_GRAD_R,OFF_GRAD_B,OFF_BG_G,OFF_BG_R,OFF_BG_B
W,H=17,11
def main():
 mask=np.ones((H,W),dtype=np.uint8);mask[2:9,4:13]=0;inside,ti=run_aex_fieldgen(mask,6,0);outside,to=run_aex_fieldgen((mask==0).astype(np.uint8),5,0);field=np.maximum(inside,outside);words=np.rint(np.clip(field,0,1)*32768).astype('<u2');src={};fw={}
 for y in range(H):
  for x in range(W):
   if mask[y,x]:src[x,y]=(32768,(x*997+y*211)%32769,(x*613+y*1231)%32769,(x*1499+y*307)%32769)
   fw[x,y]=(0,int(words[y,x]),0,0)
 ld=make_loader();ld.register_libm_impls(max_threads=1);sw=build_world(ld,W,H,src);fieldw=build_world(ld,W,H,fw);ref=alloc_refcon(ld)
 def put(o,f,v):ld.write_bytes(ref+o,struct.pack(f,v))
 for o,f,v in ((OFF_SRC_WORLD_PTR,'<Q',sw),(OFF_FIELD_WORLD_PTR,'<Q',fieldw),(OFF_DEGENERATE,'<B',0),(OFF_USE_BG,'<B',0),(OFF_INVERT,'<B',1),(OFF_INOUT_MODE,'<i',3),(OFF_RENDER_MODE,'<i',2),(OFF_INTERP_MODE,'<i',4),(OFF_POWER,'<f',2.5),(OFF_GRAD_G,'<f',0.0),(OFF_GRAD_R,'<f',28/255),(OFF_GRAD_B,'<f',238/255),(OFF_BG_G,'<f',160/255),(OFF_BG_R,'<f',16/255),(OFF_BG_B,'<f',48/255)):put(o,f,v)
 actual=[call_compose(ld,ref,x,y) for y in range(H) for x in range(W)];source=b''.join(struct.pack('<4H',a,r,g,b) for a,g,r,b in (src.get((x,y),(0,0,0,0)) for y in range(H) for x in range(W)));active=b''.join(struct.pack('<4H',a,r,g,b) for a,g,r,b in actual);srcpad=b''.join(source[y*136:(y+1)*136]+b'\xa5'*10 for y in range(H));expected=b''.join(active[y*136:(y+1)*136]+b'\xa5'*14 for y in range(H));hs=[hashlib.sha256(z.astype('<f4').tobytes()).hexdigest() for z in (inside,outside,field)];out_sha=hashlib.sha256(active).hexdigest();assert hs==['061454ff2adc6e3fafc7a1558143b2da7d9eb1cb2641eda95c70ac97908d18dc','b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112','a84f59f33fe82263d86280a3bf48ff6fac47b5e98376b95b9418aec0c47c3f3d'];assert out_sha=='a8602dcead6cc882af398356a63a5d2806b426bb42bcc1e7c113f3e9e3a6295e';print('hashes',hs,out_sha);assert len(ti)==len(to)==3
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);a=t/'s';b=t/'e';exe=t/'h';a.write_bytes(srcpad);b.write_bytes(expected);q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HERE/'dg_classic_pf16_both_power_layer_nobg_harness_20260805.cpp'),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr;q=subprocess.run([str(exe),str(a),str(b)],capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_BOTH_POWER_LAYER_NOBG_EXACT')
if __name__=='__main__':raise SystemExit(main())
