# OLM RadialBlur Edge Fade × Offset — 2026-08-11

Status: **exact** within the enumerated boundary.

## Zoom

- Centered 32×18, PF8/PF16/PF32, Outer Strength 4.
- Outer Edge Fade 0/50/100 with Offset Mode 1 / Offset 0: 9/9 exact.
- Outer Edge Fade 50 crossed with Mode 2 / UI Offset 2 and Mode 3 / UI Offset 4: 6/6 exact.
- Compared the actual AEX pre-blur and post-blur float32 planes and the typed output including row padding.
- The Zoom owner ignores Offset Mode and Offset. After Effects disables both controls for Zoom; the injected cross-cases prove that the actual AEX output remains identical to the same Fade 50, Mode 1 / Offset 0 result.

The port now follows the actual Zoom order: the dedicated Edge Fade prepass (`FUN_18000b150`) computes a seed alpha from the size-factor plane, then the strength scatter (`FUN_18000a9d0`) consumes that seed. At Size Variation 0 the fade factor is exactly 1.0 even where the separately sampled scatter span falls below one.

## Rotation

- Centered 32×18, PF8/PF16/PF32.
- Matching Outer or Inner Strength 4 and Edge Fade 50.
- Offset Mode 2 / UI Offset 4 and Mode 3 / UI Offset 4: 12/12 exact.
- Compared polar, source-scalar, prepass-alpha, accumulation, max-alpha, final-RGBA, coordinate, and typed output planes including row padding.

Rotation performs the Edge Fade prepass before the Offset-controlled scatter. The admitted tuples preserve that ordering and use the already recovered radius-dependent Mode 2/3 span conversion.

## Evidence boundary

Only the tuples above are admitted. Other Fade values, Offset values, geometries, strengths, simultaneous Outer and Inner Fade, Size/Noise intersections, special PF32 values, and After Effects host behavior are not generalized from this evidence and remain fail-closed unless independently admitted.

Reproduction:

```sh
python3 tools/emulation/probe_olmradialblur_zoom_edge_fade_offset_actual_aex_20260811.py
python3 tools/emulation/probe_olmradialblur_rotation_edge_offset_32x18_actual_aex_20260811.py
```
