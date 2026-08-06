#!/usr/bin/env python3
"""Fail-closed inventory for the missing DG PF32 full-small-frame oracle."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def main():
 asm=(ROOT/'disasm/DistanceGradation.aex.asm.txt').read_text()
 src=(ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp').read_text()
 checks={
  'classic_pf32_dispatch_owner': '181173f6d  CALL 0x181172a10' in asm,
  'pf32_owner_copies_16_byte_rows': '18117364f  SHL R15D,0x4' in asm and '181173682  MOV R8,R13' in asm,
  'pf32_owner_calls_shared_fieldgen': '181173532  CALL 0x181174760' in asm and '181173572  CALL 0x181174760' in asm,
  'production_pf32_has_no_pf8_pf16_roundtrip': 'else if (p.pixel_size == sizeof(PF_Pixel8))' in src and 'if (p.pixel_size == sizeof(PF_Pixel16))' in src and 'sizeof(PF_PixelFloat)' not in src[src.index('// The Windows typed paths merge'):src.index('// ============================================================================\n// Per-pixel color combination')],
 }
 assert all(checks.values()),checks
 report={'schema':'olmdistancegradation.pf32-small-pipeline-boundary/1','status':'capture_required','checks':checks,'facts':{'pf32_owner':'FUN_181172a10','shared_fieldgen':'FUN_181174760','typed_pf32_compose_callback':None,'retained_pf32_typed_fixture_count':0},'required_capture':{'entry':'FUN_181172a10','geometry':[17,11],'depth':'PF32','must_retain':['source_argb_f32','field_f32 after FUN_181174760','final_argb_f32','all host checkout/handle callbacks','OpenCV detour sequence'],'must_not_reuse':['PF8 staging','PF16 staging','FUN_181170870','FUN_181170480']},'claims':{'production_changed':False,'pf32_exact':False}}
 print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
