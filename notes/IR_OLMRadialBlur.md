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
  - 2026-06-24 decision matrix
    `refs/reports/olmradialblur_decision_matrix_20260624/decision_matrix.md`
    classifies RadialBlur as `blocked-needs-narrow-proof`: Zoom is a guarded
    alpha-normalization/sampler residual, tiny Rotation is sampler/validity
    unresolved, and Inner has no exact/global candidate to promote.

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
| Static scatter audit rejects promoting `loop-minus-one` or `circular-wrap` as global rules: `R14D = trunc(resolved_distance * span_gate)`, table step is `30000 / R14D`, the inner tail loops while `offset < R14D`, and underflow advances to the next radius row. | `refs/reports/olmradialblur_scatter_static_facts.md`, `scripts/analyze_radialblur_scatter_static_facts.py`. | binary-grounded |
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
- 2026-06-22 residual cluster audits
  (`refs/reports/olmradialblur_residual_clusters_20260622_011750/residual_clusters.md`,
  rerun `refs/reports/olmradialblur_residual_clusters_20260622_030500/residual_clusters.md`)
  now classifies the Zoom residual as `rgba-off-by-one`: `max=1`,
  `mean=0.004614559`, `31124` nonzero pixels (`1.5010%`), largest connected
  component only `9` pixels, RGB differences are limited to `-1..+1`, and
  alpha has `30962` positive / `0` negative signed differences. This strongly
  suggests a quantization/writeback or alpha-normalization one-step issue, not
  a broad sampler geometry error.
- The residual cluster audit now emits `recommended_next_evidence` in both JSON
  and Markdown. For the Zoom witness it asks for pre-round/pre-clamp
  normalization plus final u8 writeback values, so the next change can separate
  alpha-normalization from final quantization instead of tuning to PNG symptoms.
- Packaged focused Windows trace request:
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_residual_witness_20260622_012712.zip`.
  It asks for the `(6,0)` Zoom witness pre-writeback/normalization/final bytes
  separately from the tiny Rotation sampler witness below.
- 2026-06-24 focused runtime return classifies the Zoom witness as
  `pre-output alpha-normalization / sampler-side residual; not a later
  byte-writer mismatch`. Windows final bytes are `[20,3,3,254]`, and the
  traced pre-writeback floats truncate to those exact bytes. Therefore the
  remaining Zoom `alpha=255` local residual is upstream of final byte packing,
  likely alpha normalization or sampler-side state.
- Mac-side witness audit
  `refs/reports/olmradialblur_zoom_witness_20260624/audit.md` recomputes the
  same `(6,0)` path from the 20260604 manifest. Local RGB floats match the
  Windows pre-writeback floats within about `1.3e-7`, while local alpha clips
  to `1.0` and Windows alpha remains `0.9999999403953552`; local floor bytes
  are `[20,3,3,255]` versus Windows `[20,3,3,254]`. Do not change final byte
  conversion for this residual; the next proof belongs in Zoom polar
  alpha/sample accumulation.
- 2026-06-24 decision matrix
  `refs/reports/olmradialblur_decision_matrix_20260624/decision_matrix.md`
  keeps this slice at `guarded-alpha-normalization`: the only local floor-vs-
  Windows byte delta at the witness is alpha `+1`, and final byte packing is
  already ruled out.
- 2026-06-24 witness contract:
  `refs/reports/olmradialblur_witness_contract_20260624/witness_contract.md`
  freezes the useful proof boundary for Zoom, tiny Rotation, and Inner. For
  Zoom it explicitly keeps final byte packing unchanged because the Windows
  pre-writeback float `[0.08224078,0.01413010,0.01413010,0.99999994]`
  truncates to the Windows byte `[20,3,3,254]`; the remaining local alpha
  `1.0` vs Windows `0.99999994` must be explained in polar alpha/sample
  accumulation before sampler return.

## Rotation / Inner Status

- Tiny Rotation `case_0010` passes only a loose mean guard:
  `max=255 mean=0.0104`. This is a useful regression guard, not exactness.
- 2026-06-22 residual cluster audits show tiny Rotation is not a pure
  off-by-one/rounding problem. The latest audit classifies it as
  `high-rgb-border-sampler-or-validity`: `max=255`, `mean=0.010407142`,
  `33796` nonzero pixels (`1.6298%`), largest component `40` pixels touching
  the top border, and max witness `ref=[255,255,255,255]` /
  `cand=[0,0,0,255]` at `(1614,6)`. Alpha still has only positive +1
  differences, but RGB includes full negative drops (`R/G/B min=-255`). Treat
  this as a localized inverse-sampling or validity/border miss until
  binary/runtime evidence says otherwise.
- The same focused Windows trace package asks for the `(1614,6)` tiny Rotation
  inverse-sampler source/polar coordinates, validity/border decision,
  normalization denominator, pre-writeback RGBA, and final stored bytes.
- The residual cluster audit's `recommended_next_evidence` keeps this
  distinction machine-readable: high RGB drops near the top border should be
  answered by inverse-sampler coordinates, border validity branch, denominator,
  and final RGBA values, not by a broad scatter-loop toggle.
- 2026-06-24 focused runtime return captured final bytes for the tiny Rotation
  witness, but the closest traced inverse-sampler value does not explain the
  final white pixel. Treat this as `final-writeback-only` / unresolved
  sampler-validity evidence: final byte conversion is not enough, and the next
  proof needs the exact sampler/validity/pre-writeback path for the high-max
  top-border witness.
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
- 2026-06-22 Mac-side quick candidate matrix against the 20260617 full Inner
  Software set (`refs/reports/olmradialblur_inner_candidate_matrix_20260622_001824/`)
  narrows the next static target without changing implementation defaults:
  - `loop-minus-one` has the lowest representative mean sum
    (`33.853479` vs current `34.228107`) and improves Quality-heavy cases
    (`quality_1`, `quality_50`) plus Edge Fade by a small amount, but worsens
    small/large strength. This is localization evidence only.
  - `circular-wrap` improves small and large strength (`0.2346 -> 0.2275`,
    `0.1897 -> 0.1246`) but worsens Edge Fade and Quality cases. Do not
    replace the binary-grounded `aex-next-row` underflow rule globally.
  - `dynamic-offset-aex-row` is byte-identical to current default for the
    representative cases, so the next Mac-side search should not spend time on
    that dynamic-offset formula.
  - `grid-aex-float` changes only tiny mean-level amounts, so polar grid float
    precision is unlikely to explain the high-max residuals.
  - `no-span-minus-one` and `table-span-minus-one` strongly worsen small-span
    cases. The current default `span-minus-one` remains the least bad broad
    setting, but the loop/table split is still not binary-grounded.
- 2026-06-22 wide matrix (`refs/reports/olmradialblur_inner_candidate_matrix_20260622_002848/`)
  reruns the same eight high-value diagnostics against all ten 20260617 full
  Inner cases. It keeps `loop-minus-one` as the best total-mean candidate
  (`63.793179` vs current `64.313564`) and improves 7/10 cases, especially
  `existing_0011`, `existing_0012`, `quality_1`, and `quality_50`. It still
  worsens `small`, `large`, and `offset_mode_3`, while `circular-wrap` is best
  for exactly those low-span/offset families. `table-span-minus-one` is best
  for Edge Fade families. This split is stronger evidence that the missing rule
  is not a global span/loop/wrap toggle; the next proof needs a real
  `FUN_180001c90` per-cell witness for one low-span cell and one Quality cell.
- 2026-06-22 static scatter audit
  (`refs/reports/olmradialblur_scatter_static_facts.md`) makes that caution
  machine-checkable. The exported disassembly shows `CVTTSS2SI R14D,XMM0` for
  effective span, `IDIV R14D` for the 30000-entry table step, inner tail
  `CMP R10D,R14D` / `JL`, and underflow `LEA EDX,[R12 + 0x1]`. Therefore
  `loop-minus-one`, `table-span-minus-one`, and `circular-wrap` remain
  localization probes only; the next change needs a typed runtime witness for
  the wrong plane/value, not a broad helper toggle.
- 2026-06-24 decision matrix summarizes the split:
  `loop-minus-one` is still best by mean sum in the 20260617 full Inner matrix,
  but no candidate is exact and all top candidates keep `max=255`. Keep
  `loop-minus-one`, `circular-wrap`, `table-span-minus-one`, and
  `grid-aex-float` as localization probes, not implementation defaults.
- The 2026-06-24 witness contract also freezes tiny Rotation and Inner proof
  boundaries:
  - Tiny Rotation `case_0010 (1614,6)` has a closest traced inverse-sampler
    return `[-0.00408194,-0.00408194,-0.00408194,1.0]`, which floors to
    `[0,0,0,255]`, while Windows final is `[255,255,255,255]`. Do not treat
    that closest sampler return as the true final pre-writeback value; the
    next proof must identify the exact validity/border branch or substitute
    path.
  - Inner remains `blocked-no-global-toggle`. Static facts stay:
    `R14D = trunc(float(resolved_distance) * span_gate)`, table step
    `int(30000 / R14D)`, tail loop `offset < R14D`, and underflow to the next
    radius row tail. The next proof is typed `FUN_180001c90` per-cell values
    for a low-span cell and a Quality/strong cell.
- 2026-06-25 Inner witness-plan audit
  (`refs/reports/olmradialblur_inner_witness_plan_20260625/witness_plan.md`)
  turns that next proof into concrete representatives without changing the
  implementation:
  - Low-span representative: `rb_inner_only_strength_large`, where
    `circular-wrap` is the best localization probe (`mean 0.189705 -> 0.124590`)
    while `loop-minus-one` is nearly inert.
  - Quality/strong representative: `rb_inner_quality_1`, where
    `loop-minus-one` is the best localization probe (`mean 15.253006 -> 14.856614`)
    but still leaves `max=240`.
  - Edge/prepass fallback: `rb_inner_edgefade_only`, where
    `table-span-minus-one` is the best localization probe (`mean 3.957052 -> 3.920890`).
  The decision is `typed-inner-cell-witnesses-only`: do not promote
  `loop-minus-one`, `circular-wrap`, or `table-span-minus-one` globally from
  the matrix. The next useful evidence is typed per-cell `FUN_180001c90`
  state for the low-span and Quality/strong representatives, with Edge Fade
  prepass/denominator values only if those two do not explain the split.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| Zoom no-inner/no-noise `case_0009` | 8bpc | guarded near-exact | 2026-06-19 rerun: `max=1 mean=0.0046`; 2026-06-24 witness audit shows RGB float match and alpha-only local `[20,3,3,255]` vs Windows `[20,3,3,254]` | AE exact check and Zoom polar alpha/sample accumulation proof |
| tiny Rotation `case_0010` | 8bpc | guarded mean-only | 2026-06-19 rerun: `max=255 mean=0.0104` | binary-ground high-max residual before broad compatibility claim |
| old Inner `case_0011..0013` | 8bpc | expected-red | 2026-06-19 rerun: `max=255/255/238`, `mean=23.0495/16.0039/18.0193` | narrow asm/runtime proof for remaining sampler/prepass/scatter/writeback split |
| Inner small-span witness | 8bpc | runtime-trace-informed guard | span fact resolved to 31, image still `max=255 mean=0.2346` in current smoke | compare more per-cell scatter/writeback witnesses before changing defaults |
| Inner typed witness representatives | 8bpc | blocked witness plan | 2026-06-25 plan selects `rb_inner_only_strength_large` for low-span and `rb_inner_quality_1` for Quality/strong; `rb_inner_edgefade_only` is fallback if Edge Fade prepass remains unexplained | capture typed `FUN_180001c90` per-cell resolved span/table/loop/source-row/accumulation values for those representatives |
| Inner `param10` plane probes | 8bpc | rejected hypotheses | `one/factor` equivalent; `polar-alpha/prepass-alpha` worse on old Inner and Edge Fade | focus next proof on `FUN_180001c90` effective length, loop bound, table divisor, or caller distance |

## Focused Runtime Return Classification

`scripts/compare_radialblur_trace.py` now understands both the older dense
request `olmradialblur_dense_sampler_trace_20260620` and the focused residual
request `olmradialblur_zoom_tiny_rotation_residual_witness_20260622`.

After importing the focused Windows return, run:

```
python3 scripts/compare_radialblur_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary.json \
  --output-json refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness.json \
  --output-md refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness.md
```

Expected useful classifications:

- `zoom:alpha-normalization-or-writeback`: compare denominator and final byte
  conversion before changing the Zoom path. The 2026-06-24 witness audit now
  rules out the final byte conversion for `case_0009 (6,0)`, so continue with
  polar alpha/sample accumulation rather than writeback tuning.
- `tiny_rotation:sampler-or-validity`: inspect inverse sampler coordinates and
  border/validity before changing normalization/writeback.
- `trace-structure-present-values-missing`: repeat the Windows trace with typed
  numeric witness values; do not tune from placeholders.
- The comparison JSON/Markdown also emits `recommended_next_evidence`. Use it
  as the stop/go note for the next Mac-side implementation step: Zoom needs
  denominator/pre-writeback/writeback proof, while tiny Rotation needs
  inverse-sampler/validity proof.
- Latest focused comparison:
  `refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness_20260624.md`.
  Use this over the older generic `olmradialblur_residual_witness.md` report
  when deciding the next RadialBlur change.

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
- Whether `FUN_180001c90` uses a case-dependent underflow/loop policy: the
  2026-06-22 quick matrix shows `loop-minus-one` and `circular-wrap` improve
  different case families, which is inconsistent with a single global toggle.
- Exact Zoom one-step writeback/rounding behavior.
- Noise and Size Variation exactness outside currently guarded slices.
- Mac AE exactness and 16/32bpc behavior.
