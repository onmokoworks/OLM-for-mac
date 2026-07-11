# Windows AE 26.3 32bpc EXR Recapture

## Purpose

Reissue the existing 98-case 32bpc EXR-first reference batch under the same
After Effects major/minor version as the Mac validation host: **AE 26.3**.
The prior 48-case EXR return is valid evidence for Windows AE 25.2, but it
cannot be used to attribute a Mac AE 26.3 no-op gamma change to an OLM plug-in.

## Hard Gate

1. Launch Windows After Effects and record `app.version` before rendering.
2. Continue only when it starts with `26.3`.
3. If AE 26.3 is not installed or the original OLM AEX does not load there,
   return a short `blocked_host_version` manifest/log. Do **not** silently run
   AE 25.2 or another version as a substitute.

## Render Contract

- Project renderer: `SOFTWARE` only; record its name and raw value.
- Project depth: `32bpc` / `bits_per_channel=32`.
- Output: `OLM EXR 32 Float` or equivalent: OpenEXR, RGBA, uncompressed,
  FLOAT (not HALF) samples.
- Preserve a float EXR `before_effects_frame` for every case, plus the effect
  output EXR. This is the no-effect host-parity control.
- Record AE version, project color-management settings, output-module color
  settings, all effect properties, artifact hashes, EXR header metadata, and
  a manifest for every case.
- Keep the existing case IDs and parameters unchanged.

## Included Batch

Six request specs, 98 cases total:

- normalized 48-case batch: OLMBlur / OLMColorKey / OLMToonDilate /
  OLMDistanceGradation
- 10 random cases each: OLMDirectionalBlur / OLMKiraKira / OLMRadialBlur /
  OLMSmoother2 / OLMSmoother v1

## Acceptance

The Mac side will first compare `before_effects_frame` between Windows AE 26.3
and Mac AE 26.3. Only when that no-effect control is understood may an effect
output difference be assigned to the ported OLM implementation.
