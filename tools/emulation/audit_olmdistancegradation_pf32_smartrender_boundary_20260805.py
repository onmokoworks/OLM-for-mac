#!/usr/bin/env python3
"""Fail-closed proof that the AEX SmartRender path has no PF32 owner."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def block(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
def main():
 asm=(ROOT/'disasm/DistanceGradation.aex.asm.txt').read_text();src=(ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp').read_text()
 classic=block(asm,'; === FUN_181173d20 @ 181173d20 ===','; === FUN_181174060 @ 181174060 ===');smart=block(asm,'181174da9  MOV R8,qword ptr [R10]','181174e3d  MOV RDX,R14')
 facts={'classic_pf32_owner': '181173f6d  CALL 0x181172a10' in classic,'smart_pf16_branch':'181174df1  CALL 0x181170280' in smart,'smart_pf8_branch':'181174e31  CALL 0x181170380' in smart,'smart_pf32_owner_absent':'181172a10' not in smart,'production_has_direct_pf32_smart_branch':'else {\n\t\t\terr = RenderBits<PF_PixelFloat>' in src,'pre_render_unions_result_rect':'UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);' in src,'pre_render_unions_max_rect':'UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);' in src}
 assert all(facts.values()),facts
 r={'schema':'olmdistancegradation.pf32-smartrender-boundary/1','status':'not_an_aex_path','facts':facts,'decision':{'pf32_actual_aex_entry':'classic PF_Cmd_RENDER -> FUN_181172a10','pf32_actual_aex_smart_owner':None,'production_pf32_smart_exact_claim':False,'required_host_validation':'prove AE routes PF32 to classic Render; SmartRender direct PF32 must remain unclaimed'},'forbidden':['reuse PF8 smart callback','reuse PF16 smart callback','claim PF32 SmartRender exact from classic owner fixture']};print(json.dumps(r,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
