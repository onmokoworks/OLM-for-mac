# OLMColorKey actual exported owner seam

Verdict: `EXACT_EXPORTED_OWNER_ALL_DECLARED_TOGGLE_DEPTH_CELLS`

For both `off/off/off` and `on/on/on` Color Keep/Premultiplied/Replace representatives, the Windows AEX exported Smart owner materializes parameters and produces complete PF8, PF16, and PF32 buffers exactly equal to production `RenderWorld`. PF16 and PF32 exercise `PF iterate16 Suite` v1 and `PF iterateFloat Suite` v1 respectively through the AEXCompat typed-suite wiring at commit `0ee27894`.

This closes the former PF_Err 13 emulation boundary for these six declared cells. It does not claim arbitrary parameter products, native Windows execution, or After Effects host execution.
