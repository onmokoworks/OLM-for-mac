#!/usr/bin/env python3
"""Public Range=100 and Extra Smooth 0/100 with independent output effects at every depth."""
from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_public_smoothing_endpoints_production_harness_20260810.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_public_smoothing_endpoints_actual_aex_20260810.json';DOC=ROOT/'refs/conformance/olmsmoother2_public_smoothing_endpoints_actual_aex_20260810.md'
RGB=[(206,55,161),(86,55,26),(43,73,217),(231,16,235),(116,106,230),(1,9,43),(91,38,34),(99,183,84),(230,125,149),(208,155,60),(168,21,161),(233,157,226),(8,57,119),(159,56,196),(232,156,109),(50,140,246),(229,135,20),(36,6,46),(176,107,229),(168,83,193),(235,7,162),(225,133,142),(159,155,17),(39,112,149),(138,142,192)]
def req(x,m):
    if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
    with tempfile.TemporaryDirectory(prefix='sm2_public_endpoints_') as td:
        b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
    return {k:bytes.fromhex(v) for k,v in (line.split() for line in o.splitlines())}
def pixels(depth):
    if depth=='PF8': return [tuple(typed.f32(v/255) for v in (*rgb,255)) for rgb in RGB]
    if depth=='PF16': return [tuple(typed.f32(v/32768) for v in (*(round(c*32768/255) for c in rgb),32768)) for rgb in RGB]
    return [tuple(typed.f32(v/255) for v in (*rgb,255)) for rgb in RGB]
def main():
    src=SOURCE.read_text();req(re.search(r'PF_ADD_SLIDER\(GetStringPtr\(StrID_SmoothRange_Param_Name\),\s*0, 100, 0, 100, 2,',src),'Range public endpoint drift');req(re.search(r'PF_ADD_SLIDER\(GetStringPtr\(StrID_ExtraSmooth_Param_Name\),\s*0, 100, 0, 100, 0,',src),'Extra public endpoint drift')
    prod=production();rows=[]
    variants=[('base',2,0),('range100',100,0),('extra100',2,100)]
    for depth,pad in [('PF8',5),('PF16',7),('PF32',13)]:
        outputs={};planes={}
        for name,rng,extra in variants:
            raw,plane,_linear,ci,wi=v2.actual(depth,pixels(depth),pad,smoothness=100,smooth_range=rng,extra_smooth=extra,require_class_nonzero=False,width=5,height=5)
            req(raw==prod[f'{depth}_{name}'],f'{depth} {name} production mismatch');outputs[name]=raw;planes[name]=plane
            rows.append({'depth':depth,'variant':name,'smooth_range':rng,'extra_smooth':extra,'raw_hex':raw.hex(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'class_nonzero_bytes':sum(x!=0 for x in plane),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'typed_worker_instructions':wi,'equal':True})
        req(len(set(outputs.values()))==3,depth+' endpoints do not independently affect output')
        req(planes['base']==planes['extra100'],depth+' Extra Smooth unexpectedly changed classifier plane')
        req(planes['base']!=planes['range100'],depth+' Range 100 did not change classifier plane')
    report={'verdict':'PASS_PUBLIC_RANGE100_AND_EXTRA0_100_INDEPENDENT_EFFECT_ALL_DEPTHS_EXACT','scope':'PF8/PF16/PF32 v2 key/gamma off, Smoothness100; baseline Range2/Extra0 versus public Range100 and public Extra100, padded5x5','public_ui_contract':{'smooth_range':{'minimum':0,'maximum':100,'default':2,'tested':100},'extra_smooth':{'minimum':0,'maximum':100,'default':0,'tested':[0,100]}},'independent_effect_contract':{'all_three_raw_outputs_distinct_per_depth':True,'range100_changes_classifier_plane':True,'extra100_preserves_classifier_plane_but_changes_worker_output':True},'fixture_rgb_u8':[list(x) for x in RGB],'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixtures':rows,'claims_not_made':['No other geometry or cross-parameter combination','No key/gamma interaction','No AE-host execution claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 public smoothing endpoints\n\nVerdict: `'+report['verdict']+'`\n\nOn one fixed padded 5x5 fixture, PF8/PF16/PF32 each produce three distinct raw outputs for baseline `Range=2, Extra=0`, public `Range=100, Extra=0`, and public `Range=2, Extra=100`. Range 100 changes the naturally generated class plane. Extra Smooth 100 preserves that plane but independently changes the worker output. Every variant is byte-exact between the checked-in AEX natural path and production.\n\nThe evidence is limited to this fixture and does not claim other parameter interactions or AE-host execution.\n');print(report['verdict']);return 0
if __name__=='__main__':raise SystemExit(main())
