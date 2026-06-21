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
  - Reference-set provenance is now explicitly audited: same-numbered
    `case_0001..0013` files differ between the 20260604 legacy set and the
    20260605 extra/img2 set, and one 20260619 bulk return stores RadialBlur
    PNGs under an `OLMDirectionalBlur` folder.

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
| Inner `param10` alpha-plane substitutes are negative after the Quality/5 fix: `one` and `factor` are equivalent in the tested shape, while `polar-alpha` and `prepass-alpha` worsen old Inner and Edge Fade cases. | 2026-06-21 Mac probes: `smoke_olmradialblur_cpp_inner_param10_plane_probe_cli.py`. | probe-rejected |

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
- 2026-06-21 Mac-side recheck while Smoother2 is paused:
  full Rotation remains expected-red in the current C++ CLI:
  `case_0001 max=255 mean=1.9034`,
  `case_0002 max=255 mean=1.3071`,
  while the tiny Rotation witness is unchanged at
  `case_0010 max=255 mean=0.0104`.
- Old Inner remains expected-red in the current C++ CLI:
  `case_0011 max=255 mean=23.0495`,
  `case_0012 max=255 mean=16.0039`,
  `case_0013 max=238 mean=18.0193`.
- Forcing source-scatter/prepass alone on old Inner leaves the same
  `23.0495/16.0039/18.0193` mean residuals, so that switch is not sufficient
  evidence for the old reference set.
- The 2026-06-21 `param10` plane probe narrows the residual:
  old Inner `one/factor` gives `26.1424/10.1548/13.2004`,
  `polar-alpha/prepass-alpha` gives `30.4408/12.3134/18.4576`;
  Edge Fade `one/factor` gives `5.7425/4.7327/2.2927`,
  `polar-alpha` gives `6.5374/5.4341/2.7749`, and `prepass-alpha` gives
  `7.2433/5.7656/2.7270`. This rejects a simple alpha-plane multiplier as the
  missing rule.
- Small-span scatter stats smoke confirms the current helper path is measurable
  and the span-31 runtime fact is integrated, but the image result is still not
  exact (`rb_inner_only_strength_small max=255 mean=0.2346` in the 2026-06-19
  rerun).
- Global promotion of decomp-looking source-scatter/prepass flags is rejected:
  it improves some strong/Quality cases but regresses already-close small-span
  and Edge Fade cases. Keep those switches diagnostic until a narrower binary
  fact explains the split.
- The dense RadialBlur runtime request is now routed through
  `scripts/compare_radialblur_trace.py`. The 2026-06-20 dense-all return
  contains a case/witness structure but placeholder values only, so it
  classifies as `trace-structure-present-values-missing`. The 2026-06-20
  live-followup captured the known `+0x26e5` / `+0x1d18` span registers
  (`ctx+0x3a9ec=0x1f`, `r14d=0x1f`) and classifies as
  `inner-span-31-registers-only`. This preserves the span-31 fact, but it does
  not answer sampler/scatter/writeback residuals and should not drive a broad
  implementation change.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| Zoom no-inner/no-noise `case_0009` | 8bpc | guarded near-exact | 2026-06-19 rerun: `max=1 mean=0.0046` | AE exact check and writeback/rounding proof |
| tiny Rotation `case_0010` | 8bpc | guarded mean-only | 2026-06-19 rerun: `max=255 mean=0.0104` | binary-ground high-max residual before broad compatibility claim |
| old Inner `case_0011..0013` | 8bpc | expected-red | 2026-06-19 rerun: `max=255/255/238`, `mean=23.0495/16.0039/18.0193` | narrow asm/runtime proof for remaining sampler/prepass/scatter/writeback split |
| Inner small-span witness | 8bpc | runtime-trace-informed guard | span fact resolved to 31, image still `max=255 mean=0.2346` in current smoke | compare more per-cell scatter/writeback witnesses before changing defaults |
| Inner `param10` plane probes | 8bpc | rejected hypotheses | `one/factor` equivalent; `polar-alpha/prepass-alpha` worse on old Inner and Edge Fade | focus next proof on `FUN_180001c90` effective length, loop bound, table divisor, or caller distance |

## Reference Provenance

`scripts/audit_radialblur_reference_sets.py` audits the RadialBlur reference
folders by SHA-256 rather than case number. Current result:

- Seven known reference locations exist:
  - `refs/win_references/20260604_olm/OLMRadialBlur`
  - `refs/win_references/20260605_extra/OLMRadialBlur_img2`
  - `refs/win_references/olm_reference_return_windows_recapture_20260615/OLMRadialBlur_inner`
  - `refs/win_references/olm_reference_return_windows_recapture_20260615/OLMRadialBlur_sizevar`
  - `refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_filtered_software/OLMRadialBlur`
  - `refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_full_software/OLMRadialBlur`
  - `refs/win_references/olm_windows_bulk_png_refs_20260619_014632_all_existing_requests_windows_result_20260619_0210/OLMDirectionalBlur`
- Same-numbered `case_0001..case_0013` files conflict between
  `20260604_olm/OLMRadialBlur` and `20260605_extra/OLMRadialBlur_img2`.
  Treat those as different request generations, not equivalent cases.
- The 20260619 bulk folder contains 18 RadialBlur files misplaced under
  `OLMDirectionalBlur`. They are still RadialBlur evidence, but scripts must
  key by filename/request ID rather than parent plug-in directory.
- The full 20260617 Inner return adds cases missing from the filtered return
  (`rb_inner_existing_0013_software_pair`, `rb_inner_quality_50`) and should
  be preferred for Inner request coverage.

## Open Questions

- Exact cause of tiny Rotation high-max residual despite low mean.
- Exact condition that separates strong Inner improvements from small-span /
  Edge Fade regressions.
- Whether remaining Inner residual is in radius/Quality geometry, table
  sampling, prepass alpha population, scatter normalization, or final inverse
  sampling.
- `FUN_180001c90` effective-length ownership: caller span, helper loop bound,
  table reindex divisor, and whether the span-31 runtime witness is a caller
  distance fact or a helper-local loop/population fact.
- Exact Zoom one-step writeback/rounding behavior.
- Noise and Size Variation exactness outside currently guarded slices.
- Mac AE exactness and 16/32bpc behavior.
