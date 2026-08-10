#!/usr/bin/env python3
"""Actual-AEX PF16 Inside/RGB blur x background x interpolation family."""
import hashlib, struct, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; HERE=ROOT/'tools/emulation'; sys.path.insert(0,str(HERE))
from aex_loader import AexLoader
import cv_bridge as cvb, opencv_impls as ocv
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_fieldgen_p1b import setup_tls
from test_dg_compose import (OFF_BG_B,OFF_BG_G,OFF_BG_R,OFF_DEGENERATE,OFF_FIELD_WORLD_PTR,
 OFF_GRAD_B,OFF_GRAD_G,OFF_GRAD_R,OFF_INOUT_MODE,OFF_INTERP_MODE,OFF_INVERT,OFF_POWER,
 OFF_RENDER_MODE,OFF_SRC_WORLD_PTR,OFF_USE_BG,alloc_refcon,build_world,call_compose,make_loader)
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RIP,UC_X86_REG_RSP
AEX=ROOT/'plugins_2025/DistanceGradation.aex'; BLUR=0x1812864d0; W,H=17,11; IRB,ORB=146,150
EXPECTED={
 'preblur':{'constant':'a7949b3cd602260af3a7ae9e81b99aafde9b0fe415c0c40d172af84c12ccbbe5','linear':'6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c'},
 'blurred':{'constant.mode2':'393cf156e1a1837880c7468167a4b6cb0d62a4d8ad7fdf85d2054855d1c78619','constant.mode3':'83cebbbd7ea2719c8aa6a2a612e9f08a7d4d1b7ae33d5e45251a107fc5613491','linear.mode2':'fb3a3e7ab8035af6785ed671a9c2456e2af885a667427ce67af8d086104a38d3','linear.mode3':'7026157d29a503e880e256b6716e81363bc87eded1ccc106c5c686d644b291c7'},
 'staged':{'constant.mode2':'6f11b23cdf841b21c1cccc87b8d341adc745fb31c868ed8065775f879046ce76','constant.mode3':'2c0ce37b90d010b5cdf09784911b3d584bd2b523a4fafac3cade1d74b3f1e421','linear.mode2':'b44a0eca6926cfd289378f3aa06829f0137ffcf98add40cd6d948cf3d6727374','linear.mode3':'d10e113be59f05128fc6a80f506163e6a29fd15a54ffd7b39c1cb4e25a6647ba'},
 'output':{'constant.mode2.bg0':'167fdc90816747a20784e28f4621cdff2c6c4c28d7ccf15707dd3b54ad0d400e','constant.mode2.bg1':'d71d1b1f0b4a63319c8f09f3c429df79bef008902782ae6f2d0b785703c8f74a','constant.mode3.bg0':'d323fd86053d4781ec7812f30b635c7174dacc690cf18143686cc8709f3a033e','constant.mode3.bg1':'76fea7c61cb720464911ac0bc9acedc990c87d375dfa5a44ff229a28567120fb','linear.mode2.bg0':'dbf9dab0521a040268082844b99f0f9c5ab5307d6a5cd7459b41acca144bdad5','linear.mode2.bg1':'748c54f2cd5c486407deee6e733773bcbbfa27a4b84eac677f330f7f3664d5d7','linear.mode3.bg0':'36162a7726e83f30a54213c6b279686ef6ed2f369c69929b220cdd0fec7722d0','linear.mode3.bg1':'a40951b0a307d9ea06e102bde9187ba3cfb7892a29f64b8a0891868f1a42389c'}}

def aex_blur(field, mode, kernel):
 ld=AexLoader(str(AEX),verbose=False,fast=True);ld.register_libm_impls(max_threads=1);setup_tls(ld)
 ocv.register_opencv_impls(ld,'DistanceGradation',ops=['threshold','dist_transform','resize_same_shape','normalize_minmax'])
 def release(_ld,_args):return 0
 obj_box={}
 def allocate(l,args):
  data=l.bump_alloc(0x20000,align=64);l.write_bytes(data,b'\0'*0x20000);u=l.host_alloc(0x80);l.write_bytes(u,b'\0'*0x80)
  l.write_bytes(u+8,struct.pack('<Q',obj_box['obj']));l.write_bytes(u+0x14,struct.pack('<I',1));l.write_bytes(u+0x18,struct.pack('<QQQ',data,data,0x20000));return u
 fa=ld.install_callback('DG.MatAllocator.allocate',allocate);fr=ld.install_callback('DG.MatAllocator.deallocate',release)
 vt=ld.host_alloc(0x40);ld.write_bytes(vt,b'\0'*0x40);ld.write_bytes(vt+0x10,struct.pack('<Q',fa));ld.write_bytes(vt+0x28,struct.pack('<Q',fr))
 obj=ld.host_alloc(0x10);obj_box['obj']=obj;ld.write_bytes(obj,struct.pack('<Q',vt)+b'\0'*8)
 def default_allocator(l,_a,_s):
  rsp=l.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',l.read_bytes(rsp,8))[0]
  l.uc.reg_write(UC_X86_REG_RAX,obj);l.uc.reg_write(UC_X86_REG_RSP,rsp+8);l.uc.reg_write(UC_X86_REG_RIP,ret)
 ld.add_code_hook(0x18118d2a0,default_allocator)
 src=cvb.build_ipl(ld,np.ascontiguousarray(field,dtype=np.float32),align_step=16)
 dst=cvb.build_ipl(ld,np.full((H,W),-777,np.float32),align_step=16)
 regs=ld.call_function(BLUR,int_args=[src,dst,mode-1,kernel,kernel,0,0],max_instructions=30_000_000)
 return np.ascontiguousarray(cvb.read_ipl(ld,dst),dtype='<f4'),int(regs['instructions'])

def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()=='a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
 mask=np.ones((H,W),np.uint8);mask[2:9,4:13]=0
 fields={};blurred={};traces={}
 for interp,param8 in [('constant',1),('linear',0)]:
  field,trace=run_aex_fieldgen(mask,4,param8);fields[interp]=field
  for mode in (2,3):
   b,n=aex_blur((field>=1).astype(np.float32) if interp=='constant' else field,mode,3)
   blurred[interp,mode]=b;traces[interp,mode]=n
 pixels={(x,y):(32768,(x*997+y*211)%32769,(x*613+y*1231)%32769,(x*1499+y*307)%32769) for y in range(H) for x in range(W) if mask[y,x]}
 ld=make_loader();ld.register_libm_impls(max_threads=1);sw=build_world(ld,W,H,pixels);ref=alloc_refcon(ld)
 def put(o,f,v):ld.write_bytes(ref+o,struct.pack(f,v))
 for z in ((OFF_SRC_WORLD_PTR,'<Q',sw),(OFF_DEGENERATE,'<B',0),(OFF_INVERT,'<B',1),(OFF_INOUT_MODE,'<i',1),(OFF_RENDER_MODE,'<i',1),(OFF_POWER,'<f',1.0),(OFF_GRAD_G,'<f',0.0),(OFF_GRAD_R,'<f',28/255),(OFF_GRAD_B,'<f',238/255),(OFF_BG_G,'<f',160/255),(OFF_BG_R,'<f',16/255),(OFF_BG_B,'<f',48/255)):put(*z)
 source_active=b''.join(struct.pack('<4H',a,r,g,b) for a,g,r,b in (pixels.get((x,y),(0,0,0,0)) for y in range(H) for x in range(W)))
 source=b''.join(source_active[y*W*8:(y+1)*W*8]+b'\xa5'*(IRB-W*8) for y in range(H))
 hashes={'preblur':{},'blurred':{},'staged':{},'output':{}}
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);sp=td/'src';ep=td/'exp';exe=td/'h';sp.write_bytes(source)
  q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HERE/'dg_classic_pf16_blur_background_family_harness_20260810.cpp'),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr
  for interp,imode in [('constant',1),('linear',2)]:
   hashes['preblur'][interp]=hashlib.sha256(fields[interp].astype('<f4').tobytes()).hexdigest()
   for mode in (2,3):
    b=blurred[interp,mode];key=f'{interp}.mode{mode}';hashes['blurred'][key]=hashlib.sha256(b.tobytes()).hexdigest()
    words=np.rint(np.clip(b,0,1)*32768).astype('<u2');hashes['staged'][key]=hashlib.sha256(words.tobytes()).hexdigest()
    fw=build_world(ld,W,H,{(x,y):(0,int(words[y,x]),0,0) for y in range(H) for x in range(W)})
    for bg in (0,1):
     put(OFF_FIELD_WORLD_PTR,'<Q',fw);put(OFF_USE_BG,'<B',bg);put(OFF_INTERP_MODE,'<i',imode)
     out=[call_compose(ld,ref,x,y) for y in range(H) for x in range(W)]
     active=b''.join(struct.pack('<4H',a,r,g,bv) for a,g,r,bv in out);case=f'{key}.bg{bg}';hashes['output'][case]=hashlib.sha256(active).hexdigest()
     expected=b''.join(active[y*W*8:(y+1)*W*8]+b'\xa5'*(ORB-W*8) for y in range(H));ep.write_bytes(expected)
     r=subprocess.run([str(exe),str(sp),str(ep),interp,str(bg),str(mode)],capture_output=True,text=True);assert r.returncode==0,r.stderr;print(r.stdout,end='')
 assert hashes==EXPECTED
 assert len(set(hashes['blurred'].values()))==4 and len(set(hashes['output'].values()))==8
 print('hashes',hashes);print('blur_instructions',traces);print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_BLUR_BACKGROUND_FAMILY_EXACT')
if __name__=='__main__':raise SystemExit(main())
