#!/usr/bin/env python3
"""Combined Range/Extra Smooth + invert key + Gamma Colors through actual AEX and production."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as v1
ROOT=Path(__file__).resolve().parents[2];W=H=5
HARNESS=ROOT/'tools/emulation/olmsmoother2_combined_parameters_production_harness_20260810.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_combined_parameters_actual_aex_20260810.json';DOC=ROOT/'refs/conformance/olmsmoother2_combined_parameters_actual_aex_20260810.md'
RGB=[(1,1,1),(255,0,0),(65,1,1),(0,255,0),(206,55,161),(86,55,26),(43,73,217),(231,16,235),(116,106,230),(1,9,43),(91,38,34),(99,183,84),(230,125,149),(208,155,60),(168,21,161),(233,157,226),(8,57,119),(159,56,196),(232,156,109),(50,140,246),(229,135,20),(36,6,46),(176,107,229),(168,83,193),(235,7,162)]
K=typed.f32(1/255);PALETTE=[(1.,0.,0.,1.),(K,K,K,1.)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2_combo_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return {k:bytes.fromhex(v) for k,v in (line.split() for line in o.splitlines())}
def encoded(depth):
 if depth=='PF8':return [tuple(typed.f32(v/255) for v in (*rgb,255)) for rgb in RGB]
 if depth=='PF16':return [tuple(typed.f32(v/32768) for v in (*(round(c*32768/255) for c in rgb),32768)) for rgb in RGB]
 return [tuple(typed.f32(v/255) for v in (*rgb,255)) for rgb in RGB]
def invert_key_actual(pixels):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);stride=16*W+16;base=l.bump_alloc(stride*H,align=16)
 for y in range(H):l.write_bytes(base+y*stride,b''.join(struct.pack('<4f',*pixels[y*W+x]) for x in range(W))+b'\x3c'*16)
 desc=l.bump_alloc(24,align=16);l.write_bytes(desc,struct.pack('<QiiQ',base,W,H,stride));ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[W,0,H,0]):l.write_bytes(p,struct.pack('<i',n))
 color=l.bump_alloc(16,align=16);l.write_bytes(color,struct.pack('<4f',K,K,K,1.));cfg=l.bump_alloc(0x80,align=16);l.write_bytes(cfg,b'\0'*0x80);l.write_bytes(cfg+0x60,struct.pack('<Q',1));l.write_bytes(cfg+0x68,struct.pack('<Q',color));v1.SmallStatic(l,H);r=l.call_function(0x180002930,int_args=[*ptr,desc,cfg],max_instructions=5000000)
 out=[]
 for y in range(H):
  for x in range(W):out.append(struct.unpack('<4f',l.read_bytes(base+y*stride+x*16,16)))
 return out,r['instructions']
def main():
 prod=production();rows=[]
 for depth,pad in [('PF8',5),('PF16',7),('PF32',13)]:
  keyed,ki=invert_key_actual(encoded(depth));req(keyed[0][3]==1. and keyed[1][3]==0.,depth+' invert-key roles')
  raw,plane,_linear,ci,wi=v2.actual(depth,keyed,pad,gamma_colors=True,gamma_palette=PALETTE,gamma_value=2.4,smoothness=100,smooth_range=100,extra_smooth=100,width=W,height=H)
  req(raw==prod[depth],depth+' combined production mismatch')
  rows.append({'depth':depth,'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex(),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'class_nonzero_bytes':sum(x!=0 for x in plane),'post_key_alpha_zero':sum(x[3]==0. for x in keyed),'post_key_alpha_one':sum(x[3]==1. for x in keyed),'padding_per_row':pad,'padding_preserved':True,'key_owner_instructions':ki,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 report={'verdict':'PASS_V2_COMBINED_RANGE_EXTRA_INVERT_KEY_GAMMA_COLORS_ALL_DEPTHS_EXACT','scope':'PF8/PF16/PF32 v2 padded5x5; Smoothness100 + Range100 + Extra100 + invert key RGB 1/255 + Gamma Colors ordered [red,key] gamma2.4','parameter_contract':{'smoothness':100,'smooth_range':100,'extra_smooth':100,'enable_key':True,'invert_key':True,'key_rgb':[K,K,K],'gamma_mode':'Gamma Colors','gamma_value':2.4,'ordered_gamma_palette':PALETTE},'fixture_rgb_u8':[list(x) for x in RGB],'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixtures':rows,'claims_not_made':['No claim for arbitrary parameter products','No other geometry/palette/key color','No AE-host execution claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 combined parameter boundary\n\nVerdict: `'+report['verdict']+'`\n\nA single padded 5x5 representative combines the public smoothing endpoints (`Smoothness=100`, `Range=100`, `Extra Smooth=100`) with invert Color Key and ordered two-entry Gamma Colors at Gamma Value 2.4. PF8/PF16/PF32 run the actual AEX key owner, natural classifier and typed worker, then match production byte-for-byte with row padding preserved.\n\nThis closes that representative cross-product only; it does not generalize to arbitrary parameter products, palettes, key colors, geometry, or AE-host execution.\n');print(report['verdict'])
if __name__=='__main__':raise SystemExit(main())
