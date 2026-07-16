# OLMRadialBlur natural full-size pre-collapse witness (2026-07-17)

- Status: `blocked`
- Classification: `blocked-fail-closed-no-resumable-full-size-checkpoint`
- No B150/A9D0 execution was attempted because the reusable checkpoint is not a resumable full-size state.
- Blocker: `setup checkpoint has no resumable full-size worker state; refusing to rerun the unchanged unprefilled 250M path`
- Required bounded run: actual B150 and A9D0, stop at `0x180005c9f`, then dump raw float32 RGBA/scalar at the four requested cells from `work+0x4210`/`work+0x4218`.
- Residual-driving classification: `undetermined`; no pre-collapse witness values were captured.
