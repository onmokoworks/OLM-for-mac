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
    `refs/conformance/olmradialblur_8bpc_decision.md`
    classifies RadialBlur as `blocked-needs-narrow-proof`: Zoom is a guarded
    alpha-normalization/sampler residual, tiny Rotation is an upstream polar
    RGB / substitute-path unresolved lane rather than a plain
    sampler/validity issue, and Inner has no exact/global candidate to
    promote.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Parameter reader stores Blur Type, center, strengths, offsets, edge fades, Repeat Border, Ratio, Angle, Quality, variation, noise, seed, and thickness into render struct offsets. | `notes/OLMRadialBlur_RE.md`, `FUN_180008690`. | binary-grounded |
| Rotation builds an angle-major polar grid, runs a prepass, then scatters outer and inner contributions before inverse sampling. | `notes/OLMRadialBlur_RE.md`, `notes/OLMRadialBlur_ASM_FACTS.md`, `FUN_180004640`. | binary-grounded |
| Repeat-border and non-repeat polar samplers alpha-normalize RGB and use loose `-2 < int(coord) < extent` validity windows. | `notes/OLMRadialBlur_ASM_FACTS.md`, sampler helper audit. | binary-grounded |
| The two RGBA polar samplers do not treat alpha identically: non-repeat `FUN_180001270` divides RGB by accumulated alpha and then rewrites `alpha = accumulated_alpha / in_bounds_weight_sum`, while repeat-border `FUN_180001520` divides RGB by accumulated alpha but keeps alpha as the raw accumulated edge-clamped sum and returns a separate loose-window validity flag. | 2026-06-30 Ghidra decompile pass on `0x180001270` and `0x180001520`. In `FUN_180001270`, `param_2[3] = fVar10 / fVar9` after RGB normalization; in `FUN_180001520`, RGB is normalized only when `param_2[3] != 0`, and the function returns `uVar7` for loose `-2 < int(coord) < extent` validity instead of rewriting alpha by a coverage denominator. | binary-grounded / 2026-06-30 ghidra |
| `FUN_180004640` preserves the RGBA sampler return as a caller-visible side channel independent of sampled RGBA alpha. | 2026-06-30 Ghidra recheck on `FUN_180004640`: sampler return `uVar4` is stored per polar cell into a separate validity buffer (`param_1 + 0xf252`) before prepass/scatter, and that buffer is then passed into `FUN_180002780` and `RadialBlur_scatter_valid_polar_cells`. | binary-grounded / 2026-06-30 ghidra |
| The final inverse sampler does not read the preserved validity side channel directly; `FUN_180004640` first collapses `+0xf252` into `+0xe.alpha` during polar normalization. | 2026-06-30 Ghidra recheck on `FUN_180004640`: if `*(float *)(... + 0xf252) == 0` it clears `+0xe.rgb`; otherwise it normalizes RGB from `+0xf250` and writes that same `0xf252` value into `+0xe.alpha` before the final `FUN_180009d80(param_1 + 0xe, ...)` call. | binary-grounded / 2026-06-30 ghidra |
| The current Mac C++ port does not model that preserved-validity side channel yet; both Zoom and Rotation inverse sampling currently consume a single blurred alpha plane instead of a caller-collapsed `+0xe.alpha` derived from `+0xf252`. | 2026-06-30 source audit of `mac/OLMRadialBlur/OLMRadialBlur.cpp`: `RenderZoom8` and `RenderRotation8` build one `blurred.rgba[...,3]` plane, then inverse-sample `alpha` directly from that plane. There is no separate buffer corresponding to AEX `+0xf252`, no RGB zero-on-zero-validity collapse before inverse sampling, and no distinct `+0xf250`/`+0xe` split. | source-audit / 2026-06-30 |
| A naive `0/1 preserved validity -> final alpha` substitution is rejected for the outer lanes. | `refs/conformance/olmradialblur_outer_caller_collapse_probe_20260630.md`: a bounded CLI probe with `--outer-caller-collapse-mode binary-validity` worsens both representative outer witnesses from the current narrow residuals to broad top-edge alpha staircases (`case_0009 mean=0.1146`, `case_0010 mean=0.1204`). This means the missing caller-collapse model is more specific than "sample valid flag becomes final alpha directly". | probe-rejected / 2026-06-30 |
| A weaker `validity only zeros RGB; alpha stays blurred` substitute is also rejected for the outer lanes. | `refs/conformance/olmradialblur_outer_caller_collapse_probe_20260630.md`: `--outer-caller-collapse-mode zero-rgb-on-invalid` lowers the damage versus `binary-validity`, but still broadens Zoom (`case_0009 mean=0.0260`, `max=91`) and slightly worsens tiny Rotation (`case_0010 mean=0.0144`) by erasing top-edge RGB that Windows keeps. This narrows the live hypothesis to a more specific typed caller-collapse rule, not a simple binary keep/drop gate. | probe-rejected / 2026-06-30 |
| Rotation caller plane ownership is `+0x38` polar RGBA, `+0x40` scatter span/gate, `+0x48` prepass alpha, and `+0x50` prepass factor. | `notes/OLMRadialBlur_ASM_FACTS.md`, `FUN_180004640` call sites. | binary-grounded |
| Sequence is `prepass(+0x38,+0x48,+0x50)`, then `scatter(+0x38,+0x48,+0x40)`, then polar normalization/writeback. | `notes/OLMRadialBlur_ASM_FACTS.md`, `FUN_180002780`, `FUN_1800024c0`, `FUN_180004640`. | binary-grounded |
| `FUN_180001c90` resolves outer/inner scatter spans from strength/offset mode, clamps to `3000`, multiplies by `param10`, and samples direction-specific 30000-entry tables. | Ghidra/ASM facts in `notes/OLMRadialBlur_ASM_FACTS.md`. | binary-grounded |
| Inner direction on angular underflow advances to the next radius row tail, not same-row modulo wrap. | `notes/OLMRadialBlur_ASM_FACTS.md`, Ghidra MCP re-read. | binary-grounded |
| Static scatter audit rejects promoting `loop-minus-one` or `circular-wrap` as global rules: `R14D = trunc(resolved_distance * span_gate)`, table step is `30000 / R14D`, the inner tail loops while `offset < R14D`, and underflow advances to the next radius row. | `refs/reports/olmradialblur_scatter_static_facts.md`, `scripts/analyze_radialblur_scatter_static_facts.py`. | binary-grounded |
| Runtime trace confirmed `rb_inner_only_strength_small` helper effective span resolves to `31`: callsite `OLMRadialBlur+0x26e5`, helper `+0x1c90`, `[RCX+0x3a9ec]=0x1f`, and `R14D=31` after `+0x1d18`. | `refs/reports/runtime_trace_summary_hardpaths_20260621_041022.md`. | runtime-trace |
| Size Variation feeds source-space span/factor maps, not a final alpha multiply. | `notes/OLMRadialBlur_ASM_FACTS.md`, source map audit. | binary-grounded / reference-confirmed |
| Inner `param10` alpha-plane substitutes are negative after the Quality/5 fix: `one` and `factor` are equivalent in the tested shape, while `polar-alpha` and `prepass-alpha` worsen old Inner and Edge Fade cases. | 2026-06-21 Mac probes: `smoke_olmradialblur_cpp_inner_param10_plane_probe_cli.py`. | probe-rejected |

## Ghidra Anchors

When only one CodeBrowser window is practical, keep these functions handy in the
current RadialBlur program:

- `RadialBlur_rotation_render` (`0x180004640`): top-level Rotation path,
  including sampler selection, preserved-validity storage at `+0xf252`,
  accumulation at `+0xf250`, collapse into final polar RGBA at `+0xe`, and the
  final inverse sampler call.
- `RadialBlur_scatter_tail_by_direction` (`0x180001c90`): outer/inner scatter
  span resolution, table stepping, and the inner "next radius row tail" wrap.
- `RadialBlur_sample_rgba_nonrepeat_loose` (`0x180001270`): non-repeat RGBA
  sampler with alpha rewrite as `alpha_sum / in_bounds_weight_sum`.
- `RadialBlur_sample_rgba_repeat_loose` (`0x180001520`): repeat-border RGBA
  sampler with clamped taps and a separate loose-window validity return.

If we only get one readable Ghidra target from this session, `RadialBlur` is
the right one to keep open because the highest-value pending Windows witness is
`olmradialblur_caller_collapse_witness_20260630`.

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
- A 2026-06-30 Ghidra pass sharpens that further at the helper boundary:
  non-repeat sampler `FUN_180001270` explicitly rewrites output alpha as
  `accumulated_alpha / in_bounds_weight_sum`, while repeat-border sampler
  `FUN_180001520` keeps raw accumulated alpha and returns a separate loose
  validity flag. So the remaining Zoom `(6,0)` alpha split can now be framed
  more narrowly as "which sampler helper path is active here, and what
  in-bounds coverage denominator or caller-side normalization survives to
  pre-writeback", rather than a generic writeback mystery.
- The same caller recheck shows that this is not just a helper-local quirk:
  `FUN_180004640` preserves the RGBA sampler return in an independent validity
  plane before prepass/scatter. So if Zoom `(6,0)` is on the repeat-border
  path, the later alpha/output split can legally depend on both the sampled
  RGBA alpha and the separate validity side channel.
- The caller recheck also pins the boundary of that dependence. The final
  inverse sampler does not consume `0xf252` directly; by then caller-side
  normalization has already copied preserved validity into `+0xe.alpha`. So
  the remaining Zoom question is specifically about the pre-inverse-sample
  normalization/collapse into `+0xe`, not about a hidden second validity read
  inside `FUN_180009d80`.
- A 2026-06-30 source audit shows the current Mac port still collapses this
  too early: it stores only one blurred alpha plane and reuses that plane as
  the inverse-sampled output alpha. So the local `255` vs Windows `254`
  witness should be treated as "caller-collapse not implemented yet", not as a
  generic final writeback or bilinear issue.
- Mac-side witness audit
  `refs/reports/olmradialblur_zoom_witness_20260624/audit.md` recomputes the
  same `(6,0)` path from the 20260604 manifest. Local RGB floats match the
  Windows pre-writeback floats within about `1.3e-7`, while local alpha clips
  to `1.0` and Windows alpha remains `0.9999999403953552`; local floor bytes
  are `[20,3,3,255]` versus Windows `[20,3,3,254]`. Do not change final byte
  conversion for this residual; the next proof belongs in Zoom polar
  alpha/sample accumulation.
- 2026-06-24 decision matrix
  `refs/conformance/olmradialblur_8bpc_decision.md`
  keeps this slice at `guarded-alpha-normalization`: the only local floor-vs-
  Windows byte delta at the witness is alpha `+1`, and final byte packing is
  already ruled out.
- 2026-06-30 bounded Mac-side repeat-border sampler change switched polar RGBA
  sampling from per-channel bilinear to AEX-style alpha-aware sampling for the
  current C++ implementation. Result: Zoom `case_0009` stayed effectively
  unchanged at `max=1 mean=0.00461347`, while tiny Rotation improved only
  slightly (`mean 0.01040714 -> 0.01032034`, `max` still `255`). Treat this as
  positive evidence that sampling style matters but does not remove the main
  blocker; the missing caller-collapse / preserved-validity model remains the
  next high-value lane.
- 2026-06-30 local witness dumps now pin the remaining Zoom delta even tighter.
  The new CLI witness facility captures `case_0009 (6,0)` as
  `sample_rgba=[0.0822407,0.0141302,0.0141302,1.0]` with
  `sample_u8=[20,3,3,255]`, which matches the old local audit and keeps the
  only byte delta in alpha. Re-running the same witness with
  `--rgba-sampler-alpha-mode repeat-raw` produces the same dumped floats and
  bytes, so the narrow repeat-border raw-alpha hypothesis is no longer live by
  itself. The remaining `255 vs 254` proof stays upstream in caller-side polar
  alpha/sample collapse rather than in the final inverse-sampler byte packing.
- The same 2026-06-30 local dump now exposes the four contributing polar cells
  too. For Zoom `case_0009 (6,0)`, the current CLI sees `cell00/cell10` with
  `valid=1` and `cell01/cell11` with `valid=0`, yet all four cells still carry
  nonzero RGBA and the final sample remains the near-match
  `[20,3,3,255]`. This is strong local evidence that the surviving Zoom lane
  is not explained by a naive "invalid contributing cells must be zeroed before
  final inverse sampling" rule. The live issue remains caller-side collapse /
  alpha/sample formation, not a simple per-cell validity mask at the final
  bilinear stage. See
  `refs/conformance/olmradialblur_local_witness_dumps_20260630.md`.
- 2026-07-01 expanded same-row witness probing sharpens that split even more.
  Across `case_0009` top-row `x=2..10`, final inverse-sampled alpha stays
  near-opaque (`255`) while the current local preserved-validity proxy falls
  rapidly (`243 -> 47 -> 236`). The largest `alpha_u8 - validity_alpha_u8` gap
  reaches `208` at `x=8`, with RGB still matching the reference there. So the
  surviving Zoom lane is now narrower than "sample the current preserved
  validity plane" and should be treated as caller-collapse state between
  sampler return and final `+0xe` alpha. See
  `refs/conformance/olmradialblur_caller_collapse_plane_diag_20260701.md`.
- A same-day propagated-validity probe rejects the next obvious shortcut too.
  Replacing final outer alpha with a same-kernel propagated validity plane
  (`--outer-caller-collapse-mode propagated-validity-alpha`) leaves Zoom
  effectively unchanged at `max=1 mean=0.0046`, so the missing `254/255` split
  is not solved by "blur the validity bits with the same kernel" alone. See
  `refs/conformance/olmradialblur_outer_propagated_validity_probe_20260701.md`.
- A same-day source-candidates audit now freezes the implementation decision
  ladder for the surviving Zoom lane too. With RGB already matched at the
  witness, the current preserved-validity proxy collapsing far faster than the
  final alpha plane, and the same-kernel propagated-validity substitute
  explicitly inert, the allowed source order is now explicit and source-lined:
  first `RenderZoom8` polar population / preserved-validity capture, then
  alpha accumulation / denominator state, and only then final inverse-sample /
  writeback if a later Windows typed witness explicitly contradicts the current
  caller-collapse reading. See
  `refs/conformance/olmradialblur_zoom_source_candidates_audit_20260701.md`.
- A 2026-07-01 Mac AE debug hook now exists for the same narrow outer-lane
  witnesses. `mac/OLMRadialBlur/OLMRadialBlur.cpp` accepts
  `OLMRADIALBLUR_DEBUG_DUMP_PATH` and `OLMRADIALBLUR_DEBUG_POINTS=x,y;...`,
  then appends one `OLMRADIALBLUR_DEBUG_POINT` line per matched output pixel
  with `sample_rgba`, `sample_u8`, local bilinear `validity_alpha`,
  `brightness_gain`, pre-normalized `accum_rgba`, pre-gain
  `normalized_rgba`, and the four contributing `cell_valid` / `cell_alpha`
  values. That makes the Mac witness closer to the active tiny Rotation
  anchor-watch contract: `validity_alpha` is the local preserved-validity
  analogue, `accum_rgba` mirrors the weighted pre-normalized promotion state,
  and `normalized_rgba` is the last local state before brightness gain / byte
  quantization. Parse those logs with
  `scripts/analyze_radialblur_debug_points.py`. This does not prove Windows
  behavior, but it gives a Mac-AE-side witness surface parallel to the CLI
  caller-collapse probes before the next source change. See
  `refs/conformance/olmradialblur_mac_debug_hook_20260701.md`.
- The first live Mac AE single-case rerun now confirms that this probe surface
  is genuinely usable on host once the request fixes the project bit depth.
  Without `project.bits_per_channel=8`, both `case_0009` and `case_0010`
  copied the input frame, which matches the plug-in's current unsupported
  16/32bpc fallback. After regenerating the single-case requests with
  `bits_per_channel=8`, host output returned to the expected guarded lanes:
  Zoom `case_0009 max=1 mean=0.00461347` and tiny Rotation
  `case_0010 max=255 mean=0.01032033`. The live host debug dump also captured
  both the Zoom row probe and the tiny Rotation witness, and those values agree
  with the current CLI interpretation (`Zoom (6,0)` still `sample_u8=(20,3,3,255)`,
  tiny Rotation `(1614,6)` still negative RGB with `validity_alpha=1`). See
  `refs/conformance/olmradialblur_mac_ae_single_case_probe_20260701.md`.
- A same-day automation fix removed one misleading host wrinkle from that
  probe flow. The original paired rerun launched two `run_ae_single_case.py`
  processes in parallel against one AE instance, which let `$.setenv(...)`
  collide and caused mixed/missing `radialblur_debug.log` outputs. The runner
  now serializes AE host executions with an exclusive lock at
  `/tmp/olm_ae_single_case.lock`, and isolated reruns produced separate clean
  logs for both `case_0009` and `case_0010`. Treat any earlier mixed dump as
  an automation race, not as RadialBlur behavior.
- A follow-up isolated host rerun with `cell_rgb` dumping narrows tiny
  Rotation further. Around `case_0010`, `(1612,6)` still carries a small
  bright family (`cell_rgb` contains `0.04418` / `0.00694`), `(1613,6)` mixes
  those positives with one negative cell, and the max witness `(1614,6)` has
  all four contributing cells already dark or negative
  (`[-0.01471,0,-0.04855,0]` per channel family) while
  `validity_alpha_u8` stays `255`. So the missing white lobe is not being
  removed only at the final inverse sample; by that point the contributing
  polar RGB neighborhood is already wrong on the Mac side. See
  `refs/conformance/olmradialblur_mac_ae_single_case_probe_20260701.md`.
- A same-day source-polar witness splits that upstream branch once more.
  Adding `src_cell_rgba` to the host debug dump shows that the four direct
  source polar cells feeding the witness neighborhood are all
  `RGBA=(0,0,0,1)` at `(1612,6)`, `(1613,6)`, `(1614,6)`, `(1614,5)`,
  `(1614,7)`, even though the blurred `cell_rgb` values there already contain
  small positive and negative contributions. So the missing white lobe is not
  "present in those exact source cells and later suppressed". It must depend on
  which nearby polar cells are allowed to contribute into the final lobe, or
  on a source-grid placement difference that changes where the bright family
  enters the polar buffer in the first place.
- A new same-row source audit tightens that one step more by marrying the live
  host dump to the current `RenderRotation8` source structure. For the active
  case (`outer_strength=4`, `outer_offset=0`, `quality=5`), the current small
  Rotation branch uses `row_length=3` and only same-radius-row angular taps for
  each blurred polar cell. Around the witness, those taps are
  `[1603,1602,1601]` / `[1604,1603,1602]` / `[1605,1604,1603]`, while all
  direct `src_cell_rgba` are still black. That means the current Mac branch
  cannot produce the missing bright lobe from those exact same-row direct
  source cells, and it also cannot express any AEX rule that depends on
  neighboring radius rows or a substitute path before the final inverse sample.
  See `refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.md`.
- A same-day consolidated lane audit now turns those local negatives into a
  reproducible decision boundary:
  `scripts/analyze_olmradialblur_tiny_rotation_lane.py`,
  `refs/scripts/smoke_analyze_olmradialblur_tiny_rotation_lane.py`, and
  `refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.md`.
  The lane now explicitly rejects four tempting promotions at once:
  propagated-validity remains inert, the direct same-row source cells at the
  witness are all black, the dominant local positive source-polar family sits
  one row above, and the tested row-coupled surrogates still keep the local
  bright-lobe count at `0` versus Windows `17`. This leaves only
  neighboring-row contribution ownership or an AEX substitute/fallback branch
  as the active upstream asks before final inverse sampling.
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
- 2026-07-01 same-row probing also removes one tempting dead-end here: across
  the bounded witness row `x=1610..1618`, validity alpha is fully live at every
  point (`alpha_u8 == validity_alpha_u8 == 255` throughout), yet the central
  witness `(1614,6)` still drops from Windows `[255,255,255,255]` to local
  `[0,0,0,255]`. So tiny Rotation is no longer well described as
  "validity-alpha collapse"; the remaining gap lives in upstream polar RGB /
  substitute-path population before the final inverse sample. See
  `refs/conformance/olmradialblur_caller_collapse_plane_diag_20260701.md`.
- The propagated-validity probe leaves tiny Rotation effectively unchanged too
  (`max=255 mean=0.0103`), which reinforces the same reading: this witness is
  not rescued by a better final alpha plane alone and still points upstream to
  polar RGB / substitute-path population. See
  `refs/conformance/olmradialblur_outer_propagated_validity_probe_20260701.md`.
- The same 2026-06-30 Ghidra pass gives a tighter static fork for that
  witness. Repeat-border sampler `FUN_180001520` carries a separate loose
  `-2 < int(coord) < extent` validity return even while clamping taps to edge
  pixels, whereas non-repeat `FUN_180001270` encodes coverage through the
  normalized alpha itself. That makes the tiny Rotation `(1614,6)` blocker
  more specifically a "which validity-return / substitute-path did the caller
  honor after inverse sampling" question, not just a vague border mismatch.
- `FUN_180004640` now grounds the caller half of that question too: the RGBA
  sampler return is preserved as a distinct per-cell side channel before
  prepass/scatter. So the next useful tiny-Rotation witness should not only
  ask "what RGBA did the inverse sampler see?" but also "what preserved
  validity value from the sampler return was still live for that polar cell?"
- And we can narrow that one step further: by the time `FUN_180009d80` runs,
  the caller has already collapsed preserved validity into `+0xe.alpha` and
  zeroed RGB outright when that value is zero. So the next tiny-Rotation proof
  should focus on the normalization step that produces `+0xe` for the witness
  cell: what `0xf252` value survived, whether RGB was zeroed there, and what
  exact `+0xe RGBA` reached the final inverse sampler.
- A same-day source audit explains why the current Mac candidate can still
  miss this badly even when geometry looks close: `RenderRotation8` does not
  carry a preserved-validity plane at all. It inverse-samples one blurred alpha
  plane, so it currently cannot express the AEX rule "RGB zeroed when
  preserved validity is zero, while alpha comes from the caller-collapsed
  validity value".
- The current Rotation implementation is also structurally simpler than the
  binary-grounded AEX path in one more important way: the no-inner branch in
  both CLI and Mac code still does a direct row convolution over `polar.rgba`
  (`weighted_rgb / weighted_alpha`, `accum_alpha=max(contribution)`), rather
  than the AEX-owned sequence `prepass(+0x48) -> scatter(+0x40) -> normalize`.
  That source audit now lines up with the live host cell dump above. If the
  bright lobe never gets written into the polar RGB numerator, the final
  inverse sampler cannot recover it no matter how validity is collapsed later.
- A bounded local CLI experiment now rejects the most obvious shortcut. Routing
  outer-only tiny Rotation through the existing source-scatter/prepass branch
  (`--outer-source-scatter-prepass`) worsens `case_0010` from
  `mean=0.01032034` to roughly `0.3340..0.3588` across a small sweep of seed /
  final-alpha / denominator / param10 settings, with the witness still black.
  So "reuse the current Inner source-scatter machinery for outer Rotation" is
  not the missing AEX rule by itself.
- A second bounded CLI diagnostic rejects the simplest global grid-placement
  explanation too. Adding temporary `--rotation-grid-angle-offset-steps` and
  `--rotation-grid-radius-offset` probes and sweeping
  `angle_steps,radius_offset ∈ {-0.5,-0.25,0,0.25,0.5}` leaves the current
  baseline `(0,0)` best at `mean=0.01032034`. Every tested offset worsens the
  case (`best non-baseline ≈ 0.2547` for radius `+0.25`; quarter-step angular
  offsets worsen to `≈0.385..0.390`). So the remaining tiny-Rotation split is
  not well explained by a uniform half/quarter-step angular or radial grid
  bias. The live lane is narrower: contribution geometry / neighbor ownership
  rather than a simple global grid shift.
- The current local support math now points to that same conclusion more
  concretely. For the four blurred polar cells that feed the max witness
  `(1614,6)`, the no-inner path uses only same-row backward support
  `ai, ai-1, ai-2` because `Strength=4 -> effective length 3`. On the witness
  rows:
  - row `843`: backward support includes small positive source polar cells
    (`(1602,843)≈0.0894`, `(1601,843)≈0.1683`), yielding blurred cells
    `0.04419` / `0.00694`;
  - rows `844` and `845`: backward support instead picks negative source polar
    cells (`(1601,844)≈-0.1893`, `(1601,845)≈-0.6249`), yielding
  `-0.01471` / `-0.04855`.
  A pure forward same-row pass yields zeros for these witness cells, so the
  missing white lobe is not explained by a simple direction flip either. This
  makes the next live hypothesis "AEX outer Rotation contribution geometry is
  not a plain same-row 1D blur support" rather than "small coordinate bias" or
  "just reverse the direction".
- A local source-polar neighborhood audit around the witness sharpens that
  hypothesis further. In the searched block `rows 838..848`, `angles 1598..1608`,
  the strongest positive source polar cells are:
  - `(1601,843) ≈ 0.1683`
  - `(1602,843) ≈ 0.0894`
  - far weaker `(1608,839) ≈ 0.0356`
  - one far-out bright outlier `(1608,838) ≈ 0.4526`
  Meanwhile the direct source polar cells for the witness rows
  `(1603..1604, 844..845)` are all zero, and the current same-row backward
  support on rows `844/845` only reaches one negative source cell each
  (`(1601,844)≈-0.1893`, `(1601,845)≈-0.6249`). So the only plausible local
  bright family is the `row 843 / ai 1601..1602` cluster. The current model
  already lets that family brighten row `843`, but it does not transport that
  brightness into rows `844/845`, which dominate the final witness bilinear
  weights. This makes the next structural hypothesis explicit: AEX outer
  Rotation must couple neighboring radius rows or otherwise repopulate later
  rows before final inverse sampling; a pure same-row support model cannot
  generate the white lobe at `(1614,6)`.
- 2026-07-01 turns that source-polar scan into a reproducible artifact.
  `refs/conformance/olmradialblur_tiny_rotation_source_polar_probe_20260701.md`
  re-runs the baseline C++ slice with a source-polar witness dump and keeps the
  same split explicit: there is one farther bright outlier at `(1608,838)`, but
  the dominant local positive cluster that can plausibly feed the witness still
  sits at `row 843 / ai 1601..1602`, while the direct source cells for
  `(1603..1604,844..845)` are all black.
- A first bounded row-coupling probe gives directional evidence for that read.
  A temporary CLI diagnostic
  `--outer-row-coupled-mode prev-row-add --outer-row-coupled-scale S` injects
  the previous radius row's same backward support into the current no-inner
  outer blur. This is intentionally crude, but it tests whether carrying the
  `row 843` bright family into `844/845` moves the patch the right way.
  Results on `case_0010`:
  - very small coupling (`S=0.01`) worsens mean only to `0.0191`, but already
    injects local brightness into the witness patch (`R` patch around
    `(1612..1614,4..6)` becomes `[[0,0,0],[4,0,0],[5,1,0]]`);
  - stronger coupling progressively worsens global residuals
    (`S=0.125 -> mean 0.1130`, `S=1.0 -> mean 0.4832`) while still leaving the
    central witness dark.
  So row coupling is not a dead end: even a crude previous-row add moves the
  local patch in the expected direction. But the exact AEX rule is more
  selective than "add the whole previous-row support with one constant scale".
  Treat this as positive evidence for cross-row outer population, not as a
  candidate implementation to promote.
- A follow-up selective coupling probe sharpens the same conclusion. Two
  narrower variants were tested:
  - `prev-row-tail-add`: borrow only `k>0` previous-row taps
  - `prev-row-tail-positive`: borrow only `k>0` previous-row taps whose source
    RGB luma is positive
  On `case_0010`, `prev-row-tail-positive` dominates the crude variants:
  - `scale=0.01` yields `mean=0.01424` with the same local patch lift
    `[[0,0,0],[4,0,0],[5,1,0]]`
  - the matching `prev-row-tail-add scale=0.01` is worse at `mean=0.01570`
  - larger scales still over-broaden the image (`0.0299` at `0.05`,
    `0.0869` at `0.2`, `0.3181` at `1.0`)
  This is the best local evidence so far for the structure of the missing
  family: a small positive-only cross-row tail can move the witness patch in
  the right direction without the broad damage caused by uniform previous-row
  coupling. It still does not recover the central white pixel, so it remains a
  diagnostic, not a promoted implementation.
- A second selective sweep improves that hypothesis again. Two new variants
  were tested:
  - `prev2-row-tail-positive`: borrow positive-only `k>0` tail taps from
    `ri-2`
  - `prev-ladder-tail-positive`: borrow from both `ri-1` and `ri-2`
  The current best result is now `prev2-row-tail-positive scale=0.005` with
  `mean=0.01256`, beating both:
  - `prev-row-tail-positive scale=0.01` at `0.01424`
  - `prev-ladder-tail-positive scale=0.005` at `0.01436`
  The local patch lift is the same family (`[[0,0,0],[4,0,0],[5,1,0]]`), but
  the lower global residual suggests the useful missing coupling is more
  compatible with transporting a small positive tail from `row 843` into later
  rows two steps away than with uniformly mixing the immediately previous row.
  This is still only a diagnostic, but it now points more specifically toward a
  sparse long-tail row coupling rather than broad neighboring-row blur.
- An ultra-narrow exact-tail probe is better still. Two more variants were
  tested:
  - `prev2-k2-positive`: borrow only the `k=2` positive tail from `ri-2`
  - `prev-hybrid-k12-positive`: borrow `ri-1/k=1` plus `ri-2/k=2`
  Current best local diagnostic is now:
  - `prev2-k2-positive scale=0.0025` -> `mean=0.010719`
  which is much closer to the current baseline `0.010320` than any broader
  row-coupling probe while preserving the same witness-patch lift.
  The hybrid version is consistently worse (`0.011432` at the same scale), so
  the evidence now points to a very specific missing family: not generic
  cross-row blur, but a sparse positive contribution that behaves like a weak
  `ri-2 / k=2` tail injection. This remains diagnostic, but it is the tightest
  structural clue we have for no-inner Rotation so far.
- A follow-up "only borrow into dark destination support" variant was also
  tested and rejected as a promotion candidate. Gating that same
  `ri-2 / k=2` positive tail by current destination-source luma reduces the
  collateral damage relative to the ungated version, but it still does not beat
  baseline: `prev2-k2-positive-darkdst scale=0.0005` lands at
  `mean=0.010326` versus baseline `0.010320`, and larger scales monotonically
  worsen both `mean` and `nonzero_px`. So the useful clue remains
  "there exists a sparse row-coupled positive family", not "gate the current
  ad hoc carry by darkness and keep it".
- This also clarifies what is no longer worth asking Windows for on this lane:
  a trace that only reports final `FUN_180009d80` output without the preceding
  `+0xf252` / `+0xf250` / `+0xe` state is now too late to distinguish
  substitute-path / validity-collapse behavior from ordinary bilinear sampling.
  The next actionable tiny-Rotation witness should explicitly include
  `0xf252`, `0xf250 RGBA`, normalized `+0xe RGBA`, and then final output.
- 2026-06-30 local witness dumps tighten the tiny-Rotation diagnosis too. At
  the max witness `case_0010 (1614,6)`, all four contributing local polar cells
  are already `valid=1` with `alpha=1.0`, but their RGB values are
  `[negative, zero, negative, zero]`, yielding a slightly negative final sample
  and local output `[0,0,0,255]`. This means the high-max residual is not a
  last-stage validity gate at this witness. It is upstream in polar RGB
  population / normalization or in a source-coordinate choice that selects the
  wrong polar neighborhood before final inverse sampling. See
  `refs/conformance/olmradialblur_local_witness_dumps_20260630.md`.
- A 2026-06-30 negative-RGB clamp probe confirms that diagnosis. Clamping only
  the final inverse-sampled polar RGB contributors to `max(value, 0)` leaves
  Zoom unchanged and improves tiny Rotation only marginally
  (`mean 0.01032034 -> 0.01030189`, `max` still `255`). So the negative local
  cells are real, but a last-stage RGB clamp is not the missing AEX rule. The
  active lane stays upstream in polar RGB population / normalization or source
  coordinate choice, not in final post-sample cleanup. See
  `refs/conformance/olmradialblur_final_polar_rgb_clamp_probe_20260630.md`.
- A same-day output patch audit sharpens the "coordinate choice" half of that
  branch too. Around the tiny Rotation witness `(1614,6)`, the Windows
  reference contains a small bright cluster across `(1612..1614,4..6)` while
  the current candidate keeps the surrounding dark/low-gray support pixels but
  drops that bright lobe entirely. This looks less like a clean one-pixel
  output shift and more like a missing bright contribution family upstream of
  final inverse sampling. See
  `refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md`.
- A 2026-06-30 bright-lobe search then makes the "not just a shift" reading
  stronger. In a `25x25` window centered on the witness, the Windows reference
  still has `17` bright pixels (`R >= 200`) with a local center of mass around
  `(1611.74, 2.75)`, while the current candidate has `0` bright pixels in that
  same search region. So the tiny Rotation blocker is not merely a displaced
  nearby lobe; the bright contribution family is absent or numerically
  suppressed upstream of final inverse sampling. See
  `refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md`.
- 2026-07-01 reran the two best row-coupled diagnostics against that same
  bright-lobe metric and tightened the conclusion further. Neither
  `prev2-k2-positive scale=0.0025` nor `prev2-row-tail-positive scale=0.005`
  restores any nearby `R >= 200` pixels in the `25x25` witness window; both
  leave the local witness patch black at `(1614,6)`, and `prev2-k2-positive`
  keeps the exact same local `[[0,0,0],[4,0,0],[5,1,0]]` patch as baseline.
  So those probes remain useful only as a qualitative clue that some sparse
  cross-row positive family may exist upstream; they are not a close numeric
  stand-in for the AEX bright-lobe path. See
  `refs/conformance/olmradialblur_tiny_rotation_row_coupling_probe_20260701.md`.
- A follow-up support-envelope audit sharpens the geometry again without
  adding new rendering assumptions. The row-843 bright family is locally real,
  and a few nearby outputs can directly see it in the current same-row branch,
  but the active witness `(1614,6)` cannot because its bilinear support stays
  on rows `844/845`. That makes the current branch boundary more concrete: the
  witness cannot become white from that row-843 family without upstream
  neighboring-row ownership or a substitute/fallback path. See
  `refs/conformance/olmradialblur_tiny_rotation_support_envelope_20260701.md`.
- A same-day source-candidates audit now freezes the implementation decision
  ladder for that same lane. With the witness already black before final
  inverse sampling and the row-843 cluster invisible to the witness in the
  current branch, the allowed source order is now explicit and source-lined:
  first `RenderRotation8` polar population / preserved-validity capture,
  then scatter/substitute-path ownership, and only then final inverse-sample /
  writeback if a later Windows typed witness explicitly contradicts the current
  upstream reading. See
  `refs/conformance/olmradialblur_tiny_rotation_source_candidates_audit_20260701.md`.
- 2026-06-21 Mac-side recheck while Smoother2 is paused:
  full Rotation remains expected-red in the current C++ CLI:
  `case_0001 max=255 mean=1.9034`,
  `case_0002 max=255 mean=1.3071`,
  while the tiny Rotation witness is unchanged at
  `case_0010 max=255 mean=0.0104`.
- 2026-06-30 bounded sampler-alignment rerun nudges that witness only
  slightly: `case_0010 max=255 mean=0.01032034` after switching repeat-border
  polar sampling to alpha-aware RGBA. This is not enough to promote any
  broader rule; it mainly confirms that the residual is no longer well modeled
  as "plain sampling only".
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
- 2026-07-01 pending narrow-proof contract refresh:
  `refs/conformance/olmradialblur_pending_narrow_proof_20260629.md`.
  This keeps the remaining blocker split into three explicit witness lanes, but
  it also changes which one is actually live:
  - Zoom `case_0009 (6,0)` is now context, not the first Windows ask, because
    the sampled/pre-writeback floats already truncate to the exact stored
    Windows byte and the unresolved part is specifically caller-collapse /
    denominator-side state.
  - tiny Rotation `case_0010 (1614,6)` is now the only active Windows runtime
    package. It stays frozen as an upstream RGB / neighboring-contribution /
    substitute-path question because the closest traced sampler return still
    truncates to black, same-row direct sources are black, propagated validity
    is inert, and the current row-coupled surrogates still leave the reference
    bright-lobe count at `17 -> 0` locally.
  - Inner remains a separate helper-to-output continuity question past
    `effective_span`, with representative low-span / quality-strong /
    edge-prepass typed spans already recorded, but it is not the live send
    package right now.
  Operationally, this means broad loop/wrap/final-byte retuning should remain
  forbidden until one of those lanes is closed with a typed witness that
  survives to accumulation/denominator/writeback.
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

`scripts/compare_radialblur_trace.py` now understands the older dense request
`olmradialblur_dense_sampler_trace_20260620`, the mixed outer residual lane
`olmradialblur_caller_collapse_witness_20260630`
(`olmradialblur_zoom_tiny_rotation_residual_witness_20260622` legacy), and the
tiny-Rotation-only narrow follow-ups
`olmradialblur_tiny_rotation_substitute_path_followup_20260701` and its
inverse-sampler-anchored successor
`olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701`, plus
the current fourth-round live ask
`olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702`. For
those tiny-only follow-ups, the comparator now also injects the local lane audit from
`refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.json` so the
Windows typed witness is read against the already-frozen Mac-side support,
source-polar, and row-coupling envelope instead of as a standalone log.

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
- `tiny_rotation:substitute-or-upstream-rgb`: treat the return as proof about
  substitute/fallback ownership, source-population, preserved-validity
  `+0xf252`, accumulated `+0xf250`, and normalized `+0xe` RGBA before touching
  any final inverse-sample/writeback code. This is the intended classification
  for `olmradialblur_tiny_rotation_substitute_path_followup_20260701` and the
  tighter `olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701`,
  and it remains the correct lane classification for the current
  `olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702` once
  that return is imported.
- `tiny_rotation:anchor-watch-upstream-rgb`: keep the stable inverse-sampler
  anchor, but request pointer/watchpoint context and typed upstream
  substitute/source-population values before changing code.
- `trace-structure-present-values-missing`: repeat the Windows trace with typed
  numeric witness values; do not tune from placeholders.
- The 2026-07-01 tiny-only partial return is now also archived as a stable
  project-local evidence object:
  `refs/returns/windows/20260701_214150_radialblur_tiny_rotation_substitute_followup/...return_windows.zip`
  plus the focused comparison
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_substitute_followup_20260701.md`.
  That report freezes the current read as
  `tiny_rotation:substitute-or-upstream-rgb`, not a final-byte or
  validity-only lane.
- A dedicated backstep-anchor audit now freezes the exact last stable local
  sample point for the active Windows follow-up:
  `scripts/analyze_olmradialblur_tiny_rotation_backstep_anchor.py`,
  `refs/scripts/smoke_analyze_olmradialblur_tiny_rotation_backstep_anchor.py`,
  and
  `refs/conformance/olmradialblur_tiny_rotation_backstep_anchor_audit_20260701.md`.
  It records that the reliable inverse-sampler anchor for `case_0010 (1614,6)`
  is `(angle=1603.83948, radius=844.317505)` with direct support only on rows
  `844/845`, all direct source cells black, and the nearest positive family one
  row above at `row 843 / angles 1601..1602`. That keeps the live Windows ask
  on the first upstream inclusion/substitute branch, not on final sample
  placement.
- A same-day Windows return now freezes what that backstep ask still does not
  capture:
  `refs/returns/windows/20260701_225800_radialblur_tiny_rotation_backstep_followup/...return_windows.zip`,
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.summary.md`,
  and
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.md`.
  The result is still `failed_partial`: it preserves the stable
  `+0x4eb9/+0x4ec8` inverse-sampler anchor, final white byte, and the same
  near-black sampled RGBA, but it does not retain the first upstream branch
  that promotes the witness to white. That means the next Windows ask is no
  longer "backstep from the anchor" in general; it must attach stack/pointer
  context or sampled-cell watchpoints to that same anchor so the first
  substitute/source-population branch is retained.
- The current live Windows ask is therefore the anchor-watch contract:
  `refs/conformance/olmradialblur_tiny_rotation_anchor_watch_followup_contract_20260701.md`
  and
  `refs/conformance/olmradialblur_tiny_rotation_anchor_watch_return_acceptance_20260701.md`.
  Treat the backstep package and its comparison as archived evidence that
  justifies this narrower request, not as the active queue item.
- The comparison JSON/Markdown also emits `recommended_next_evidence`. Use it
  as the stop/go note for the next Mac-side implementation step: Zoom needs
  caller-collapse / denominator / pre-writeback proof, while tiny Rotation
  needs the anchor-watch upstream RGB / substitute-path witness.
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
- Exact Zoom one-step caller-collapse behavior from sampler return /
  preserved-validity / accumulated RGBA into `+0xe`.
- Whether the current Mac port should introduce explicit `polar_rgba`,
  `polar_validity`, and caller-collapsed `polar_out` planes before any broader
  RadialBlur exactness work.
- Noise and Size Variation exactness outside currently guarded slices.
- Mac AE exactness and 16/32bpc behavior.
