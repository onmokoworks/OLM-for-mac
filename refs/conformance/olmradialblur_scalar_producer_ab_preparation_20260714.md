# OLMRadialBlur scalar producer A/B preparation

Date: 2026-07-14

## Scope

The default Mac `RenderZoom8` path is unchanged. A diagnostic-only switch now
forces the existing non-FFT producer path for large radii and uses explicit
float32 multiply/add accumulation for its alpha and premultiplied RGB sums.

Enable it with:

`OLMRADIALBLUR_FORCE_SCALAR_PRODUCER=1`

The switch is read from the AE process environment. It is not enabled by
default and is not an algorithm correction or an `AE exact` claim.

## Evidence basis

The Windows decompilation of `FUN_18000b150` shows float32 accumulation,
truncating table indexing, and separate producer-side ranges. The current Mac
large-radius path uses a double/FFT convolution. This A/B only isolates the
FFT versus ordered-float accumulation question; it does not yet reproduce the
AEX scale-plane or left/right table selection.

## Verification

- `xcodebuild -project mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj -target OLMRadialBlur -configuration Debug CODE_SIGNING_ALLOWED=NO build`
  - `BUILD SUCCEEDED`
- Existing Windows evidence remains unchanged: current case_0009 is not
  `AE exact`, with `max=1` and `12,876` differing pixels in the latest Mac A/B
  baseline.

## Next measurement

Run the same Mac AE case_0009 with and without the environment switch and
compare the complete output plus the existing four-point debug dump. A lower
residual supports continuing in this producer lane; an unchanged result
closes this numerical hypothesis without changing production behavior.
