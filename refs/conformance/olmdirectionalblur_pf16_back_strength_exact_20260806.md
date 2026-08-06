# OLMDirectionalBlur PF16 back-strength exact boundary

- Status: `exact`
- Depth: PF16 / ARGB64
- Geometry: 16x16 with 16 bytes of host row padding
- Parameters: angle 45, brightness gain 1, front strength 0, back strength 1,
  2, or 8; fade, sharp tail, size variation, and noise all zero; render scale 1
- Actual-AEX callbacks: populate `0x1800068e0`, output `0x180006a90`

| Back | Active output SHA-256 |
|---:|---|
| 1 | `2545772bed5562452123c265cc52abd8a7c3ff5c8bf9f920f72270447bec7ec7` |
| 2 | `097f9257b33a92a078826f24026a8afc294ef2db0f40f3e1966af0e910f40609` |
| 8 | `0a2059d3b76dcb7908bfeda0a14bdec7630414ac33c31f2284f76b1c08be85e6` |

The PF16 focused test captures each output from the retained AEX and compares
all 1,024 words with production. The source-included production dispatcher test
also executes each bounded tuple and verifies active output and untouched row
padding.

Other strengths, angles, gains, render scales, simultaneous front/back beyond
the separately captured back-1 family, fade/tail/size/noise combinations, AE
host renders, and Windows AE exports remain unclaimed and fail-closed.
