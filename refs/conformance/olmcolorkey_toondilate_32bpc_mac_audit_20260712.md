# OLMColorKey / OLMToonDilate 32bpc Mac Audit - 2026-07-12

## Scope

Bounded audit of the production Mac float paths in
`mac/OLMColorKey/OLMColorKey.cpp` and
`mac/OLMToonDilate/OLMToonDilate.cpp`. No image tuning was performed.

## FACT

- The latest ledger/evidence keeps the Windows 32bpc ColorKey return
  `probe-only-png-return`; it is not float-preserving evidence.
- Mac AE 26.3 produced finite, uncompressed FLOAT EXR candidates for all three
  ToonDilate cases, but the evidence explicitly remains a host candidate, not
  `AE exact`, because the cross-platform no-effect RGB baseline is not closed.
- The SDK defines `PF_PixelFloat` as four `PF_FpShort` channels in A/R/G/B
  field order, with 1.0 as white. Both modules access the fields by name and
  use the float sample values without integer quantization.
- Both modules advertise smart render and float-color awareness through
  `out_flags2 = 0x00801400`, which includes
  `PF_OutFlag2_SUPPORTS_SMART_RENDER` and
  `PF_OutFlag2_FLOAT_COLOR_AWARE` in the local AE SDK.
- Both `SMART_RENDER` handlers dispatch 8/16/32bpc from
  `extra->input->bitdepth`, and their 32bpc branches instantiate
  `PF_PixelFloat`.
- The `PF_Cmd_RENDER` handlers use `PF_WORLD_IS_DEEP(output)` and therefore
  only select the legacy 8/16bpc branches. `PF_InData` has no legacy render
  bitdepth field; the SDK exposes the explicit bitdepth field on the smart
  render inputs instead.

## INFERENCE

- The current production float paths are structurally faithful to the
  binary-grounded 8/16bpc algorithms at the dispatch and pixel-contract
  boundary when AE invokes the advertised smart-render path.
- The legacy `PF_Cmd_RENDER` branch is not evidence of a usable 32bpc path and
  must not be described as one. There is no defensible source-only fix for
  that branch without an AE host contract that supplies its depth.
- ToonDilate's float opaque test (`alpha >= 1.0f`) and selective
  semi-transparent premultiplication are intentional float-domain analogues
  of the 8/16bpc max-channel/equality and integer-premultiply rules. No
  image-based change is justified by the current evidence.
- No `AE exact` claim is made. Mac and Windows host results remain
  cross-host evidence, not a typed plug-in-buffer equivalence proof.

## Decision

The production host-contract change corrects the two `out_flags2` masks to
`0x00801400`, expressed with the SDK names for smart render, float color
awareness, and flattened sequence data. The built `GlobalSetup` code and PiPL
resources both encode that value. No pixel
math, thresholds, distance behavior, alpha behavior, or image-tuned algorithm
logic was changed. The focused source-contract smoke below guards the
established boundary and the two Mac projects are built separately for
verification.
