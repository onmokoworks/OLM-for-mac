# Binary-Grounded IR: OLMRadialBlur

## Feature

- Plug-in: OLM RadialBlur
- Feature/path: 8bpc Zoom, Rotation, and Inner/Outer radial blur paths
- Bit depth: 8bpc documented here; 16/32bpc still need references
- Reference sets:
  - `refs/win_references/20260604_olm/OLMRadialBlur`
  - `refs/win_references/20260605_extra/OLMRadialBlur_img2`
  - `refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_full_software`
- Current status:
  - Zoom no-inner/no-noise: guarded near-exact, not `AE exact`
  - tiny Rotation: guarded mean-only near-match, high max residual remains
  - Inner: binary-grounded in plane ownership and selected helper spans, but
    still expected-red on old Inner and full Inner references

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Parameter reader stores Blur Type, center, strengths, offsets, edge fades, Repeat Border, Ratio, Angle, Quality, variation, noise, seed, and thickness into render struct offsets. | `notes/OLMRadialBlur_RE.md`, `FUN_180008690`. | binary-grounded |
| Rotation builds an angle-major polar grid, runs a prepass, then scatters outer and inner contributions before inverse sampling. | `notes/OLMRadialBlur_RE.md`, `notes/OLMRadialBlur_ASM_FACTS.md`, `FUN_180004640`. | binary-grounded |
| Repeat-border and non-repeat polar samplers alpha-normalize RGB and use loose `-2 < int(coord) < extent` validity windows. | `notes/OLMRadialBlur_ASM_FACTS.md`, sampler helper audit. | binary-grounded |
| Rotation caller plane ownership is `+0x38` polar RGBA, `+0x40` scatter span/gate, `+0x48` prepass alpha, and `+0x50` prepass factor. | `notes/OLMRadialBlur_ASM_FACTS.md`, `FUN_180004640` call sites. | binary-grounded |
| Sequence is `prepass(+0x38,+0x48,+0x50)`, then `scatter(+0x38,+0x48,+0x40)`, then polar normalization/writeback. | `notes/OLMRadialBlur_ASM_FACTS.md`, `FUN_180002780`, `FUN_1800024c0`, `FUN_180004640`. | binary-grounded |
| `FUN_180001c90` resolves outer/inner scatter spans from strength/offset mode, clamps to `3000`, multiplies by `param10`, and samples direction-specific 30000-entry tables. | Ghidra/ASM facts in `notes/OLMRadialBlur_ASM_FACTS.md`. | binary-grounded |
| Inner direction on angular underflow advances to the next radius row tail, not same-row modulo wrap. | `notes/OLMRadialBlur_ASM_FACTS.md`, Ghidra MCP re-read. | binary-grounded |
| Runtime trace confirmed `rb_inner_only_strength_small` helper effective span resolves to `31`: callsite `OLMRadialBlur+0x26e5`, helper `+0x1c90`, `[RCX+0x3a9ec]=0x1f`, and `R14D=31` after `+0x1d18`. | `refs/reports/runtime_trace_summary_hardpaths_20260621_041022.md`. | runtime-trace |
| Size Variation feeds source-space span/factor maps, not a final alpha multiply. | `notes/OLMRadialBlur_ASM_FACTS.md`, source map audit. | binary-grounded / reference-confirmed |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `Blur Type` | Zoom or Rotation. | `1=Zoom`, `2=Rotation`. | `FUN_180008690` |
| `Center` | Source-space blur center. | Stored as two doubles/floats in render state. | parameter reader |
| `Outer Strength` / `Inner Strength` | Base scatter length. | Span-relevant values are built with the same Quality/5-like scale in Rotation setup. | Ghidra follow-up |
| `Outer Offset Mode` / `Inner Offset Mode` | Mode for dynamic offset combination. | mode 1 add, mode 2 max, mode 3 dynamic-only in `FUN_180001c90` shape. | helper audit |
| `Outer Edge Fade` / `Inner Edge Fade` | Prepass alpha gather spans. | Separate tables at `+0x3a9f0` and `+0x3b990`. | prepass audit |
| `Repeat Border` | Selects repeat/clamp sampler pair. | Repeat on uses clamped taps but keeps original coordinate validity. | sampler audit |
| `Ratio` / `Angle` | Rotation polar basis. | Angle is degrees multiplied by pi/180. | parameter reader |
| `Quality` | Angular grid resolution and Rotation span scale. | Stored as `1 / Quality`, with setup using `0.2 / quality_step = Quality / 5` for span-relevant values. | Ghidra follow-up |
| `Size Variation` | Source-space size factor and span/gate modulation. | `Size Variation * 0.01`; cancels on fully opaque uniform masks. | source map audit |
| `Noise Variation` | Source-space noise factor into span/gate. | `Noise Variation * 0.01`; not implemented as exact final behavior yet. | source map audit |

## Rotation Plane / Loop Shape

Current binary-grounded sequence:

1. Sample source into polar RGBA `+0x38`; store a separate valid-byte plane.
2. Sample scalar span/gate source into `+0x40`.
3. Sample or fill prepass factor plane `+0x50`.
4. Run `FUN_180002780`:
   - starts from source alpha and weight sum `1.0`;
   - gathers edge-fade alpha in outer/backward and inner/forward directions;
   - writes computed alpha to `+0x48` and the scalar max/denom plane;
   - writes `computed_alpha * polar.rgb` and `computed_alpha` to the RGBA
     accumulation buffer.
5. Run `FUN_1800024c0`:
   - gate is valid byte, `+0x48 != 0`, and `+0x40 != 0`;
   - calls outer scatter first, then inner scatter.
6. Normalize polar cells:
   - if scalar max/denom is zero, clear RGB;
   - otherwise RGB output is accumulation RGB divided by accumulation alpha,
     while alpha output is the scalar max/denom.
7. Inverse sample the polar buffer into the output image.

## Zoom Status

- The C++ CLI ports the no-inner/no-noise Zoom polar path.
- `case_0009` currently passes the guard at `max=1 mean=0.0046`.
- This is not completion: the remaining alpha/RGB one-step residual still
  needs AE exact validation and binary-grounded writeback/rounding proof.
- Size Variation and Noise remain outside the exact Zoom claim.

## Rotation / Inner Status

- Tiny Rotation `case_0010` passes only a loose mean guard:
  `max=255 mean=0.0104`. This is a useful regression guard, not exactness.
- Old Inner remains expected-red in the current C++ CLI:
  `case_0011 max=255 mean=23.0495`,
  `case_0012 max=255 mean=16.0039`,
  `case_0013 max=238 mean=18.0193`.
- Small-span scatter stats smoke confirms the current helper path is measurable
  and the span-31 runtime fact is integrated, but the image result is still not
  exact (`rb_inner_only_strength_small max=255 mean=0.2346` in the 2026-06-19
  rerun).
- Global promotion of decomp-looking source-scatter/prepass flags is rejected:
  it improves some strong/Quality cases but regresses already-close small-span
  and Edge Fade cases. Keep those switches diagnostic until a narrower binary
  fact explains the split.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| Zoom no-inner/no-noise `case_0009` | 8bpc | guarded near-exact | 2026-06-19 rerun: `max=1 mean=0.0046` | AE exact check and writeback/rounding proof |
| tiny Rotation `case_0010` | 8bpc | guarded mean-only | 2026-06-19 rerun: `max=255 mean=0.0104` | binary-ground high-max residual before broad compatibility claim |
| old Inner `case_0011..0013` | 8bpc | expected-red | 2026-06-19 rerun: `max=255/255/238`, `mean=23.0495/16.0039/18.0193` | narrow asm/runtime proof for remaining sampler/prepass/scatter/writeback split |
| Inner small-span witness | 8bpc | runtime-trace-informed guard | span fact resolved to 31, image still `max=255 mean=0.2346` in current smoke | compare more per-cell scatter/writeback witnesses before changing defaults |

## Open Questions

- Exact cause of tiny Rotation high-max residual despite low mean.
- Exact condition that separates strong Inner improvements from small-span /
  Edge Fade regressions.
- Whether remaining Inner residual is in radius/Quality geometry, table
  sampling, prepass alpha population, scatter normalization, or final inverse
  sampling.
- Exact Zoom one-step writeback/rounding behavior.
- Noise and Size Variation exactness outside currently guarded slices.
- Mac AE exactness and 16/32bpc behavior.
