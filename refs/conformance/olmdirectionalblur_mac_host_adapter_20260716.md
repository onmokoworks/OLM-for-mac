# OLMDirectionalBlur Mac Host-Adapter Proof

Status: **PASS**, 2026-07-16.

The focused test source-includes the current production adapter and calls its
test-only `OLMDirectionalBlurTestRenderWorld` seam. The seam reports the actual
`CanUseExactFrontOnly8` decision and then invokes the production `RenderWorld`
dispatcher. The macro is test-only and does not alter the plugin target.

## Boundary

- PF world: 16x16, `rowbytes=76`, `PF_Pixel8` A/R/G/B.
- The fixture runs full `[0,0,16,16]` and partial `[2,1,14,15]` extent hints
  through the production 8bpc dispatcher. Both hints produce identical
  full-world output, verifying that the current exact gate ignores
  `extent_hint`; cropped ROI semantics remain unverified.
- Input row padding is `0xA5`; output row padding is `0xEE`.
- Angle 0 and angle 45 were admitted to the exact path (`used_exact=1`) for
  both ROI hints.
- Every pixel matched an independent contiguous
  `olm_dblur_frontonly_rgba8` reference call.
- Input storage, input row padding, and output row padding were unchanged.

## Dispatch Gate

The matrix rejected exact dispatch for size variation, positive Front Alpha
Fade, Back Alpha Fade, Front Sharp Tail, Back Strength, noise, downsample, and
dimension mismatch. This fixture proves only that the current production gate
requires `front_alpha_fade == 0`; status of the positive-fade family comes from
separate conformance evidence.

This is a dispatch-gating correction only. It does not promote any AE exact
path or change the shared algorithm.

## Verification

```text
python3 tools/emulation/test_dblur_mac_host_adapter_20260716.py
status=ok
full ROI: angle 0 and 45 exact=1, pixels_match=true, padding_unchanged=true
partial ROI: angle 0 and 45 exact=1, pixels_match=true, padding_unchanged=true
gates=8/8 exact=0
```

A separate no-install `xcodebuild` of the same production source produced an
arm64 Mach-O plug-in bundle. `codesign --verify --deep --strict` passed. That
build/signature check is independent of the focused source-including probe.

Production references: `CanUseExactFrontOnly8` and `RenderWorld` in
`mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`.
