#!/usr/bin/env python3
import hashlib,struct,subprocess,tempfile,sys,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';sys.path.insert(0,str(HERE))
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_fieldgen_p1b import make_mask
from test_dg_compose import make_loader,build_world,call_compose,alloc_refcon,OFF_SRC_WORLD_PTR,OFF_FIELD_WORLD_PTR,OFF_DEGENERATE,OFF_USE_BG,OFF_INVERT,OFF_INOUT_MODE,OFF_RENDER_MODE,OFF_INTERP_MODE,OFF_POWER,OFF_GRAD_G,OFF_GRAD_R,OFF_GRAD_B,OFF_BG_G,OFF_BG_R,OFF_BG_B
HARNESS=HERE/'dg_classic_pf16_outside_sphere_nobg_harness_20260805.cpp';W,H,IRB,ORB=17,11,146,150
def main():
 invert=os.environ.get('OLM_DG_CLASSIC_INVERT')=='1'
 mask=make_mask(W,H);field,trace=run_aex_fieldgen((mask==0).astype(np.uint8),4,0);words=np.rint(np.clip(field,0,1)*32768).astype('<u2');ld=make_loader();src={};fw={}
 for y in range(H):
  for x in range(W):
   if mask[y,x]:src[x,y]=(32768,(x*997+y*211)%32769,(x*613+y*1231)%32769,(x*1499+y*307)%32769)
   fw[x,y]=(0,int(words[y,x]),0,0)
 sw=build_world(ld,W,H,src);fieldw=build_world(ld,W,H,fw);ref=alloc_refcon(ld)
 def put(o,f,v):ld.write_bytes(ref+o,struct.pack(f,v))
 for o,f,v in ((OFF_SRC_WORLD_PTR,'<Q',sw),(OFF_FIELD_WORLD_PTR,'<Q',fieldw),(OFF_DEGENERATE,'<B',0),(OFF_USE_BG,'<B',0),(OFF_INVERT,'<B',int(invert)),(OFF_INOUT_MODE,'<i',2),(OFF_RENDER_MODE,'<i',1),(OFF_INTERP_MODE,'<i',3),(OFF_POWER,'<f',1.0),(OFF_GRAD_G,'<f',0.0),(OFF_GRAD_R,'<f',28/255),(OFF_GRAD_B,'<f',238/255),(OFF_BG_G,'<f',0.0),(OFF_BG_R,'<f',1.0),(OFF_BG_B,'<f',0.0)):put(o,f,v)
 actual_words=[call_compose(ld,ref,x,y) for y in range(H) for x in range(W)];active=b''.join(struct.pack('<4H',a,r,g,b) for a,g,r,b in actual_words);source=b''.join(struct.pack('<4H',a,r,g,b) for a,g,r,b in (src.get((x,y),(0,0,0,0)) for y in range(H) for x in range(W)));srcpad=b''.join(source[y*W*8:(y+1)*W*8]+b'\xa5'*(IRB-W*8) for y in range(H));expected=b''.join(active[y*W*8:(y+1)*W*8]+b'\xa5'*(ORB-W*8) for y in range(H))
 field_sha=hashlib.sha256(field.astype('<f4').tobytes()).hexdigest();output_sha=hashlib.sha256(active).hexdigest();assert field_sha=='f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229';expected_sha=('ef941acc83ffe9432b37d5307d0143a8a374711853a0d422c72e1235de7963df' if invert else '71b62987c22b93b09db49b238a767eac6797686f1cab365baed15aac0997f391');assert output_sha==expected_sha;print('field_sha256',field_sha);print('output_active_sha256',output_sha);assert len(trace)>0
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);a=t/'src';b=t/'exp';exe=t/'h';a.write_bytes(srcpad);b.write_bytes(expected);q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HARNESS),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr;args=[str(exe),str(a),str(b)]+(['invert'] if invert else []);q=subprocess.run(args,capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_OUTSIDE_SPHERE_NOBG_INVERT_EXACT' if invert else 'PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_OUTSIDE_SPHERE_NOBG_EXACT')
if __name__=='__main__':raise SystemExit(main())
