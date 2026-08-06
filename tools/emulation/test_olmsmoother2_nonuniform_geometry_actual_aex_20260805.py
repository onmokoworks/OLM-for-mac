#!/usr/bin/env python3
"""Natural AEX classifier/c280 typed render versus production on padded 3x2 fixtures."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import SerialVcomp,FUN_ADA0

ROOT=Path(__file__).resolve().parents[2]; W,H=3,2
HARNESS=ROOT/'tools/emulation/olmsmoother2_nonuniform_geometry_production_harness_20260805.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_nonuniform_geometry_actual_aex_20260805.json'
DOC=ROOT/'refs/conformance/olmsmoother2_nonuniform_geometry_actual_aex_20260805.md'

def req(x,m):
    if not x: raise RuntimeError('FAIL CLOSED: '+m)
def desc(l,b,stride):
    p=l.bump_alloc(24,align=16);l.write_bytes(p,struct.pack('<QiiQ',b,W,H,stride));return p
class SmallStatic(SerialVcomp):
    def static_init(self,uc,args):
        req(args==[0,H-1,1,1],f'static args {args}')
        rsp=uc.reg_read(typed.UC_X86_REG_RSP); first=struct.unpack('<Q',self.loader.read_bytes(rsp+0x28,8))[0]; last=struct.unpack('<Q',self.loader.read_bytes(rsp+0x30,8))[0]
        self.loader.write_bytes(first,struct.pack('<i',0));self.loader.write_bytes(last,struct.pack('<i',H-1));self.static_events.append({'first':0,'last':H-1});return 0
class Dynamic(typed.SerialDynamic):
    def next(self,_uc,args):
        req(self.active is not None,'dynamic before init');self.next_calls+=1
        if self.next_calls==1:
            self.loader.write_bytes(args[0],struct.pack('<i',self.active[0]));self.loader.write_bytes(args[1],struct.pack('<i',self.active[1]));return 1
        return 0

def actual(depth, pixels, pad):
    l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1)
    ss=16*W+16; sb=l.bump_alloc(ss*H,align=16)
    for y in range(H): l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*pixels[y*W+x]) for x in range(W))+b'\x3c'*16)
    cs=4*W+4; cb=l.bump_alloc(cs*H,align=16);l.write_bytes(cb,b'\xa5'*(cs*H))
    sd,cd=desc(l,sb,ss),desc(l,cb,cs);rect=l.bump_alloc(16,align=16);l.write_bytes(rect,struct.pack('<4i',0,0,W,H))
    cfg=l.bump_alloc(0x80,align=16);l.write_bytes(cfg,b'\0'*0x80);l.write_bytes(cfg,struct.pack('<i',1));l.write_bytes(cfg+0x1c,struct.pack('<i',1));l.write_bytes(cfg+0x20,struct.pack('<ii',100,0))
    sv=SmallStatic(l); cr=l.call_function(FUN_ADA0,int_args=[sd,cd,rect,cfg],max_instructions=5_000_000)
    plane=b''.join(l.read_bytes(cb+y*cs,W*4) for y in range(H));req(0xa5 not in plane,'class canary');req(any(plane),'classifier plane stayed zero')
    psz=8 if depth=='PF16' else 16; os=W*psz+pad;ob=l.bump_alloc(os*H,align=16);l.write_bytes(ob,b'\xa5'*(os*H));od=desc(l,ob,os)
    ctx=l.bump_alloc(0x20,align=16);l.write_bytes(ctx,b'\0'*0x20);dy=Dynamic(l,typed.WORKERS[depth])
    ptrs=[l.bump_alloc(4,align=4) for _ in range(4)]
    for p,v in zip(ptrs,[W,0,H,0]):l.write_bytes(p,struct.pack('<i',v))
    rr=l.call_function(typed.WORKERS[depth],int_args=[*ptrs,sd,cd,od,cfg,ctx],max_instructions=20_000_000)
    raw=l.read_bytes(ob,os*H)
    for y in range(H):req(raw[y*os+W*psz:(y+1)*os]==b'\xa5'*pad,f'{depth} padding row {y}')
    return raw,plane,cr['instructions'],rr['instructions']
def production():
    with tempfile.TemporaryDirectory(prefix='sm2_nonuniform_') as td:
        b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True)
        o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
    return dict(x.split() for x in o.splitlines())
def main():
    px=[(0.,0.,0.,1.),(1.,0.,0.,1.),(0.,1.,0.,1.),(0.,0.,1.,1.),(1.,1.,1.,1.),(.5,.5,.5,1.)];prod=production();rows=[]
    for d,pad in [('PF16',6),('PF32',12)]:
        raw,plane,ci,ri=actual(d,px,pad);req(raw.hex()==prod[d],f'{d} mismatch')
        rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'class_nonzero_bytes':sum(v!=0 for v in plane),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'typed_worker_instructions':ri,'equal':True})
    req(rows[0]['class_plane_hex']==rows[1]['class_plane_hex'],'typed fixtures classifier plane differs')
    report={'verdict':'PASS_NATURAL_AEX_CLASSIFIER_C280_TO_PRODUCTION_PADDED_3X2_EXACT','scope':'PF16/PF32 independent padded nonuniform 3x2; v1, key disabled, gamma none, smoothness100, range1, no host','aex_sha256':typed.AEX_SHA256,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixtures':rows,'claims_not_made':['No v2/key/gamma claim','No other geometry or parameter claim','No AE host claim']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother2 nonuniform classifier/c280 3x2 boundary\n\nVerdict: `'+report['verdict']+'`\n\nActual AEX naturally generates the nonzero class plane and its typed worker consumes it. PF16/PF32 production `RenderBits` matches every output and preserves row padding.\n\n- Class plane: `'+rows[0]['class_plane_hex']+'`\n- Nonzero class bytes: `'+str(rows[0]['class_nonzero_bytes'])+' / 24`\n\nThis is limited to the declared nonuniform 3x2 fixture; v2, key, gamma, other geometry, and AE host are unclaimed.\n')
    print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
