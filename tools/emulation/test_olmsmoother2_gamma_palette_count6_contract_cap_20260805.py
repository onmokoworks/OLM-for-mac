#!/usr/bin/env python3
"""Fail-closed proof that direct a9c0 count6 is outside the public AE/production contract."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805 as dup
ROOT=Path(__file__).resolve().parents[2];HEADER=ROOT/'mac/OLMSmoother2/OLMSmoother2.h';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_gamma_palette_count6_contract_cap_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_gamma_palette_count6_contract_cap_20260805.md';PALETTE=[(1.,1.,1.,1.),(1.,0.,0.,1.),(0.,0.,1.,1.),(0.,1.,0.,1.),(1.,1.,0.,1.),(0.,1.,1.,1.)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def main():
 h=HEADER.read_text();s=SOURCE.read_text();req(re.search(r'#define\s+NUM_GAMMA_COLORS\s+5\b',h),'public maximum is not 5');req('SM_GAMMA_COLOR_4' in h and 'SM_GAMMA_COLOR_5' not in h,'public parameter slots changed');req('std::min(p.num_gamma_colors, NUM_GAMMA_COLORS)' in s,'production clamp missing');req('0, NUM_GAMMA_COLORS, 0, NUM_GAMMA_COLORS, 1' in s,'AE slider maximum missing')
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);owner,pb=dup.make_owner(l,PALETTE);rows=[]
 for role,color,want in [('first_white',PALETTE[0],True),('middle_green',PALETTE[3],True),('sixth_last_cyan',PALETTE[5],True),('no_match_gray',(.375,.75,.25,1),False)]:
  got=dup.call(l,owner,color);req(got['match']==want,role);rows.append({'role':role,'match':got['match'],'instructions':got['instructions']})
 report={'verdict':'PASS_FAIL_CLOSED_COUNT6_DIRECT_OWNER_ONLY_PUBLIC_CONTRACT_MAX5','aex_sha256':typed.AEX_SHA256,'direct_owner':{'count':6,'ordered_rgba':PALETTE,'ordered_memory_hex':pb.hex(),'rows':rows,'fact':'low-level actual AEX a9c0 accepts an independently constructed six-entry vector'},'public_ae_contract':{'maximum':5,'slots':'SM_GAMMA_COLOR_0..4','slider_max_symbol':'NUM_GAMMA_COLORS'},'production_contract':{'maximum':5,'clamp':'min(p.num_gamma_colors, NUM_GAMMA_COLORS)','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},'decision':'Do not implement count6. Count5 is the maximum natural owner/classifier/worker/RenderBits path. Direct-owner count6 is not an AE-host or production exact claim.','claims_not_made':['No natural count6 path','No PF16/PF32 count6 production exactness','No AE host count6 claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 Gamma Colors count6 contract cap\n\nVerdict: `'+report['verdict']+'`\n\nA directly constructed actual-AEX `a9c0` owner vector can scan six entries and match index 5. This is deliberately not the public render contract: the AE parameter surface exposes only Color 0..4, its count slider is capped at `NUM_GAMMA_COLORS = 5`, and production clamps with `min(p.num_gamma_colors, NUM_GAMMA_COLORS)`.\n\nCount 5 is therefore the maximum natural owner/classifier/worker/RenderBits path. Count 6 must not be implemented or claimed PF16/PF32/AE exact.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
