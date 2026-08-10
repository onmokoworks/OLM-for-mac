#!/usr/bin/env python3
"""V2 natural classifier + typed worker versus production, including runtime LUTs."""
from __future__ import annotations
import hashlib,json,re,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as v1
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];W,H=3,2
HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_nonuniform_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_nonuniform_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_nonuniform_actual_aex_20260805.md'
def req(x,m):
    if not x:raise RuntimeError('FAIL CLOSED: '+m)
def table(name):
    t=(ROOT/f'mac/OLMSmoother2/Mac/OLMSmoother2_{name}_lut_10000.h').read_text();b=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',t));req(len(b)==40000,name+' LUT length');return b
DECODE,ENCODE=table('decode'),table('encode')
def interp(tab,v):
    v=typed.f32(v)
    if v<=0:return 0.
    if v>=1:return 1.
    s=float(v)*9999.;i=int(s);f=s-i;lo=struct.unpack_from('<f',tab,i*4)[0];hi=struct.unpack_from('<f',tab,(i+1)*4)[0]
    return typed.f32(float(hi)*f+float(lo)*(1.-f))
def desc(l,b,stride,width=W,height=H):
    p=l.bump_alloc(24,align=16);l.write_bytes(p,struct.pack('<QiiQ',b,width,height,stride));return p
def actual(depth,encoded,pad,gamma_all=False,gamma_value=2.4,gamma_colors=False,gamma_palette=None,smoothness=100,smooth_range=1,extra_smooth=0,require_class_nonzero=True,width=W,height=H):
    w,h=width,height
    req(len(encoded)==w*h,'encoded pixel count does not match geometry')
    l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);linear=[(interp(DECODE,r),interp(DECODE,g),interp(DECODE,b),a) for r,g,b,a in encoded]
    ss=16*w+16;sb=l.bump_alloc(ss*h,align=16)
    for y in range(h):l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*linear[y*w+x]) for x in range(w))+b'\x3c'*16)
    cs=4*w+4;cb=l.bump_alloc(cs*h,align=16);l.write_bytes(cb,b'\xa5'*(cs*h));sd,cd=desc(l,sb,ss,w,h),desc(l,cb,cs,w,h);rect=l.bump_alloc(16,align=16);l.write_bytes(rect,struct.pack('<4i',0,0,w,h));cfg=l.bump_alloc(0x80,align=16);l.write_bytes(cfg,b'\0'*0x80);l.write_bytes(cfg+0x1c,struct.pack('<i',smooth_range));l.write_bytes(cfg+0x20,struct.pack('<ii',smoothness,extra_smooth))
    if gamma_all:
        l.write_bytes(cfg+0x28,struct.pack('<f',typed.f32(gamma_value)));l.write_bytes(cfg+0x2c,struct.pack('<i',5));l.write_bytes(cfg+0x40,b'\x01')
    if gamma_colors:
        palette=gamma_palette or [(1.,1.,1.,1.)];colors=l.bump_alloc(16*len(palette),align=16);l.write_bytes(colors,b''.join(struct.pack('<4f',*(typed.f32(v) for v in color)) for color in palette));l.write_bytes(cfg+0x28,struct.pack('<f',typed.f32(gamma_value)));l.write_bytes(cfg+0x30,struct.pack('<Q',len(palette)));l.write_bytes(cfg+0x38,struct.pack('<Q',colors));l.write_bytes(cfg+0x40,b'\x03')
    sv=v1.SmallStatic(l,h);cr=l.call_function(v1.FUN_ADA0,int_args=[sd,cd,rect,cfg],max_instructions=5000000);plane=b''.join(l.read_bytes(cb+y*cs,w*4) for y in range(h));req(all(x in (0,255) for x in plane),f'class plane contains unwritten/invalid bytes: {plane.hex()}');req(any(plane) or not require_class_nonzero,'class plane stayed zero')
    psz={'PF8':4,'PF16':8,'PF32':16}[depth];os=w*psz+pad;ob=l.bump_alloc(os*h,align=16);l.write_bytes(ob,b'\xa5'*(os*h));od=desc(l,ob,os,w,h);tab=l.bump_alloc(len(ENCODE),align=16);l.write_bytes(tab,ENCODE);ctx=l.bump_alloc(0x20,align=16);l.write_bytes(ctx,b'\0'*0x20);l.write_bytes(ctx+0x10,struct.pack('<Q',10000));l.write_bytes(ctx+0x18,struct.pack('<Q',tab));dy=v1.Dynamic(l,typed.WORKERS[depth]);ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
    for p,n in zip(ptr,[w,0,h,0]):l.write_bytes(p,struct.pack('<i',n))
    rr=l.call_function(typed.WORKERS[depth],int_args=[*ptr,sd,cd,od,cfg,ctx],max_instructions=20000000);raw=l.read_bytes(ob,os*h)
    for y in range(h):req(raw[y*os+w*psz:(y+1)*os]==b'\xa5'*pad,depth+' padding')
    return raw,plane,linear,cr['instructions'],rr['instructions']
def production():
    with tempfile.TemporaryDirectory(prefix='sm2v2_') as td:
        b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],text=True,capture_output=True,check=True).stdout
    return dict(x.split() for x in o.splitlines())
def main():
    encoded=[(0.,0.,0.,1.),(0.,1.,1.,1.),(1.,0.,1.,1.),(1.,1.,0.,1.),(.25,.25,.25,1.),(.75,.75,.75,1.)];prod=production();rows=[]
    for d,p in [('PF16',6),('PF32',12)]:
        raw,plane,linear,ci,wi=actual(d,encoded,p);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'class_nonzero_bytes':sum(x!=0 for x in plane),'padding_per_row':p,'padding_preserved':True,'decode_input_rgba_f32':[list(x) for x in linear],'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
    req(rows[0]['class_plane_hex']==rows[1]['class_plane_hex'],'class divergence')
    report={'verdict':'PASS_V2_NATURAL_AEX_CLASSIFIER_TYPED_LUT_TO_PRODUCTION_PADDED_3X2_EXACT','scope':'PF16/PF32 independent v2 nonuniform padded 3x2, key disabled, gamma UI none, smoothness100, range1, captured 10000-entry decode/inverse LUTs, no host','aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(ENCODE).hexdigest(),'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixtures':rows,'claims_not_made':['No key or gamma UI mode claim','No other v2 geometry/parameters','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 nonuniform LUT boundary\n\nVerdict: `'+report['verdict']+'`\n\nThe actual AEX consumes a naturally generated class plane and the captured 10,000-entry input/output LUT contract. PF16/PF32 production output and row padding are exact for the independent 3x2 fixture.\n\nClass plane: `'+rows[0]['class_plane_hex']+'` ('+str(rows[0]['class_nonzero_bytes'])+'/24 nonzero).\n\nKey, gamma UI modes, other geometry, and AE host remain unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
