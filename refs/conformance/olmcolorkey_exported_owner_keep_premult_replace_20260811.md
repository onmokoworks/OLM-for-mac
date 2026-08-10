# OLMColorKey actual exported owner seam

Verdict: `PARTIAL_EXPORTED_OWNER_PF8_EXACT_PF16_PF32_DISPATCH_BLOCKED`

For both `off/off/off` and `on/on/on` Color Keep/Premultiplied/Replace representatives, the unchanged Windows AEX exported Smart owner materializes parameters and produces a complete PF8 buffer exactly equal to production `RenderWorld`. PF16 and PF32 both complete SmartPreRender, request their typed iterate suite without unsupported calls, then return PF_Err 13 from SmartRender before a complete worker/writer result exists.

Therefore the declared-record full-worker evidence is promoted to exported-owner evidence for PF8, but not PF16/PF32. AEXCompat issue851 is used read-only and is not modified. This is not native Windows or After Effects host evidence.
