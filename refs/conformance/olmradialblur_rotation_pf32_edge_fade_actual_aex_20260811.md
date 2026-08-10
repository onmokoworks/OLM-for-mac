# OLM RadialBlur PF32 Rotation Edge Fade — 2026-08-11

Status: **captured_fail_closed**

Actual AEX Outer and Inner Edge Fade 50/100 are captured from the polar stage through the separate pre-scatter alpha plane, accum/max/final, coordinates, and padded output. A same-radius circular Gaussian candidate was rejected after diverging at accum; the angular wrap/source-row rule remains unresolved. The regression requires all four production paths to remain fail-closed.
