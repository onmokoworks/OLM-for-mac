# OLMDistanceGradation PF32 SmartRender boundary

- Status: `not_an_aex_path`; a PF32 SmartRender byte-exact claim is impossible for the retained AEX entrypoint.

The actual AEX classic Render dispatch explicitly selects PF32 and calls `FUN_181172a10`. Its SmartRender dispatch has only two branches: request flag bit 0 selects PF16 (`FUN_181170280`), otherwise PF8 (`FUN_181170380`). There is no call or branch to the PF32 owner.

SmartPreRender result/max-result rectangle plumbing can be audited independently, but no actual-AEX PF32 SmartRender output world, parameter sequence, sequence/pre-render lifetime, or 2,992-byte result exists to capture. The already exact PF32 fixture belongs to classic `PF_Cmd_RENDER`.

The Mac source contains a direct PF32 SmartRender fallback, but it is not AEX-grounded and is not claimed exact. Reusing either integer SmartRender callback would violate the bit-depth boundary. The next legitimate host proof is a hash-bound AE run showing that 32bpc routes to classic Render while SmartPre/SmartRender remain the 8/16 path.

`tools/emulation/audit_olmdistancegradation_pf32_smartrender_boundary_20260805.py` locks these dispatch and rectangle facts. Resize and blur remain separate.
