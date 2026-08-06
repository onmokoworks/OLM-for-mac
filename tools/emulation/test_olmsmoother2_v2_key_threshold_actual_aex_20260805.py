#!/usr/bin/env python3
"""V2 non-invert key threshold branch through actual AEX and production."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as v1
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];W,H=3,2;FKEY=0x180002A70
HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_key_threshold_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_key_threshold_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_key_threshold_actual_aex_20260805.md'
def req(x,m):
    if not x:raise RuntimeError('FAIL CLOSED: '+m)
def desc(l,b,s):p=l.bump_alloc(24,align=16);l.write_bytes(p,struct.pack('<QiiQ',b,W,H,s));return p
def actual(depth,encoded,pad,invert=False,gamma_palette=None,gamma_value=2.4,key_rgb=None):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);ss=16*W+16;sb=l.bump_alloc(ss*H,align=16)
 for y in range(H):l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*encoded[y*W+x]) for x in range(W))+b'\x3c'*16)
 sd=desc(l,sb,ss);ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[W,0,H,0]):l.write_bytes(p,struct.pack('<i',n))
 key=l.bump_alloc(16,align=16);kv=typed.f32(1/255);krgb=tuple(typed.f32(v) for v in (key_rgb or (kv,kv,kv)));l.write_bytes(key,struct.pack('<4f',1.,*krgb));sv=v1.SmallStatic(l)
 if invert:
  palette=l.bump_alloc(16,align=16);l.write_bytes(palette,struct.pack('<4f',*krgb,1.));palette_cfg=l.bump_alloc(0x80,align=16);l.write_bytes(palette_cfg,b'\0'*0x80);l.write_bytes(palette_cfg+0x60,struct.pack('<Q',1));l.write_bytes(palette_cfg+0x68,struct.pack('<Q',palette));kr=l.call_function(0x180002930,int_args=[*ptr,sd,palette_cfg],max_instructions=5000000)
 else:
  kr=l.call_function(FKEY,int_args=[*ptr,sd,key],max_instructions=5000000)
 keyed=[]
 for y in range(H):
  for x in range(W):keyed.append(struct.unpack('<4f',l.read_bytes(sb+y*ss+x*16,16)))
 alphas=[p[3] for p in keyed];req(alphas.count(0.)>=2 and alphas.count(1.)>=2,'key did not cover sides')
 linear=[(v2.interp(v2.DECODE,r),v2.interp(v2.DECODE,g),v2.interp(v2.DECODE,b),a) for r,g,b,a in keyed]
 for y in range(H):
  for x in range(W):l.write_bytes(sb+y*ss+x*16,struct.pack('<4f',*linear[y*W+x]))
 cs=4*W+4;cb=l.bump_alloc(cs*H,align=16);l.write_bytes(cb,b'\xa5'*(cs*H));cd=desc(l,cb,cs);rect=l.bump_alloc(16,align=16);l.write_bytes(rect,struct.pack('<4i',0,0,W,H));cfg=l.bump_alloc(0x80,align=16);l.write_bytes(cfg,b'\0'*0x80);l.write_bytes(cfg+0x1c,struct.pack('<i',1));l.write_bytes(cfg+0x20,struct.pack('<ii',100,0))
 if gamma_palette:
  colors=l.bump_alloc(16*len(gamma_palette),align=16);l.write_bytes(colors,b''.join(struct.pack('<4f',*(typed.f32(v) for v in color)) for color in gamma_palette));l.write_bytes(cfg+0x28,struct.pack('<f',typed.f32(gamma_value)));l.write_bytes(cfg+0x30,struct.pack('<Q',len(gamma_palette)));l.write_bytes(cfg+0x38,struct.pack('<Q',colors));l.write_bytes(cfg+0x40,b'\x03')
 cv=v1.SmallStatic(l);cr=l.call_function(v1.FUN_ADA0,int_args=[sd,cd,rect,cfg],max_instructions=5000000);plane=b''.join(l.read_bytes(cb+y*cs,W*4) for y in range(H));req(any(plane),'zero class plane')
 psz=8 if depth=='PF16' else 16;os=W*psz+pad;ob=l.bump_alloc(os*H,align=16);l.write_bytes(ob,b'\xa5'*(os*H));od=desc(l,ob,os);tab=l.bump_alloc(len(v2.ENCODE),align=16);l.write_bytes(tab,v2.ENCODE);ctx=l.bump_alloc(0x20,align=16);l.write_bytes(ctx,b'\0'*0x20);l.write_bytes(ctx+0x10,struct.pack('<Q',10000));l.write_bytes(ctx+0x18,struct.pack('<Q',tab));dy=v1.Dynamic(l,typed.WORKERS[depth]);rr=l.call_function(typed.WORKERS[depth],int_args=[*ptr,sd,cd,od,cfg,ctx],max_instructions=20000000);raw=l.read_bytes(ob,os*H)
 for y in range(H):req(raw[y*os+W*psz:(y+1)*os]==b'\xa5'*pad,depth+' padding')
 return raw,plane,keyed,kr['instructions'],cr['instructions'],rr['instructions']
def production():
 with tempfile.TemporaryDirectory(prefix='sm2key_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],text=True,capture_output=True,check=True).stdout
 return dict(x.split() for x in o.splitlines())
def f(u):return struct.unpack('<f',struct.pack('<I',u))[0]
def main():
 k=typed.f32(1/255);pf16=[(128/32768,128/32768,128/32768,1),(65/32768,128/32768,128/32768,1),(64/32768,128/32768,128/32768,1),(0,1,0,1),(1,0,1,1),(.75,.75,.75,1)];pf32=[(k,k,k,1),(f(0x3b008082),k,k,1),(f(0x3b008081),k,k,1),(f(0x3b008080),k,k,1),(0,1,0,1),(.75,.75,.75,1)];prod=production();rows=[]
 for d,pix,pad in [('PF16',pf16,6),('PF32',pf32,12)]:
  pix=[tuple(typed.f32(v) for v in q) for q in pix];raw,plane,keyed,ki,ci,wi=actual(d,pix,pad);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'post_key_alpha':[x[3] for x in keyed],'threshold_relation':['exact-key','inside','outside' if d=='PF16' else 'tie','far','far','far'] if d=='PF16' else ['exact-key','inside','tie','outside','far','far'],'padding_preserved':True,'padding_per_row':pad,'key_instructions':ki,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 req(rows[1]['post_key_alpha'][2]==1.0,'PF32 tie must be excluded by JNC');req(rows[1]['post_key_alpha'][1]==0.0 and rows[1]['post_key_alpha'][3]==1.0,'PF32 sides');report={'verdict':'PASS_V2_KEY_THRESHOLD_NATURAL_AEX_TO_PRODUCTION_PADDED_3X2_EXACT','scope':'PF16/PF32 independent v2 non-invert key enabled, key RGB=1/255, threshold sides; PF32 exact tie; gamma UI none, captured LUTs, padded 3x2','aex_sha256':typed.AEX_SHA256,'key_threshold_f32_bits':'0x3b008081','pf16_exact_tie_representable':False,'pf16_tie_note':'No PF16 code/key-u8 pair subtracts to the exact threshold float32; adjacent codes 65 (inside) and 64 (outside) bracket it. PF32 exercises exact equality.','fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No invert-key claim','No Gamma UI mode claim','No other key color/geometry','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 key threshold boundary\n\nVerdict: `'+report['verdict']+'`\n\nActual AEX `FUN_180002a70` runs before natural classifier/c280 and typed writeback. Production is raw exact with padding preserved. PF32 covers inside/equality/outside; equality follows `COMISS/JNC` and is not keyed. PF16 has no exactly representable tie for an 8-bit key color, so adjacent codes 65/64 bracket the threshold.\n\nInvert key, Gamma UI modes, other key colors/geometry, and AE host are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
