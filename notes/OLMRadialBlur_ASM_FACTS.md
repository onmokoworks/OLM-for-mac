# OLMRadialBlur ASM Facts

Scope: read-only sampler/writeback audit for Rotation polar buffers. Sources:
`notes/OLMRadialBlur_RE.md`, `decomp/OLMRadialBlur.aex.c.txt`,
`disasm/OLMRadialBlur.aex.asm.txt`, and current
`cli/OLMRadialBlur/main.cpp`. No implementation claims beyond the facts below.

## Sampler Helpers

- `FUN_180001270`: non-repeat RGBA polar sampler. It clears the four-float
  destination, accepts coordinates only when `-2 < int(x) < width` and
  `-2 < int(y) < height`, accumulates only in-bounds bilinear taps, weights RGB
  by tap alpha, then normalizes RGB by accumulated alpha. It returns `1` only
  when accumulated alpha is nonzero; otherwise returns `0`. It writes output
  alpha as `alpha_sum / geometric_weight_sum`.
- `FUN_180001520`: repeat-border RGBA polar sampler. It clears the destination,
  clamps the four tap coordinates to image edges, performs the same alpha
  weighted RGB normalization as `FUN_180001270`, and returns a validity byte
  based on the original un-clamped integer coordinate window
  `-2 < int(x) < width` and `-2 < int(y) < height`.
- `FUN_180001800`: non-repeat scalar sampler. It clears one float destination,
  accepts the same loose coordinate window as `FUN_180001270`, accumulates only
  in-bounds bilinear taps, and divides by the geometric weight sum when nonzero.
  It has no return value.
- `FUN_180001950`: repeat-border scalar sampler. It clears one float
  destination, clamps tap coordinates to image edges, and writes plain bilinear
  scalar output. It has no return value.

## Rotation Caller Plane Map

`FUN_180004640` selects the helper pair by Repeat Border: repeat off uses
`FUN_180001270` / `FUN_180001800`; repeat on uses `FUN_180001520` /
`FUN_180001950` (`decomp` around `2064..2072`, asm call through
`[RSI+0x58]`/`[RSI+0x60]`).

- `+0x38`: polar RGBA input. Filled by the RGBA sampler from source layer
  `param_2[0x13]` / asm `R14+0x98`; the sampler return byte is stored in a
  separate valid-byte plane at `180004b19`.
- `+0x40`: scalar span/gate plane for `FUN_1800024c0`. Filled by the scalar
  sampler from layer `param_2[0x12]` / asm `R14+0x90`.
- `+0x48`: prepass alpha plane. It is not filled during initial sampling.
  `FUN_180002780` writes it, and `FUN_1800024c0` later reads it.
- `+0x50`: prepass factor plane. If Size Variation enable flag `R14+0x44` is
  clear, the caller writes literal `1.0f`; otherwise it samples layer
  `param_2[0x11]` / asm `R14+0x88` through the scalar sampler.

Decompiler pointer-index aliases: `+0xe == +0x38`, `+0x10 == +0x40`,
`+0x12 == +0x48`, and `+0x14 == +0x50`.

- 2026-06-30 Ghidra caller recheck on `FUN_180004640` sharpens the role of
  that separate sampler return plane. The RGBA sampler return (`uVar4`) is
  written once per polar cell into the independent validity buffer
  (`local_res20`, later stored at `param_1 + 0xf252`) before any prepass or
  scatter work. The caller then passes this preserved side channel into
  `FUN_180002780` and `RadialBlur_scatter_valid_polar_cells` independently of
  the sampled RGBA alpha. Operationally, this means repeat-border
  `FUN_180001520` can feed both:
  - raw accumulated alpha inside sampled RGBA, and
  - a distinct loose-window validity return
  into later stages at the same time.
  So any remaining Zoom / tiny-Rotation border split must respect two separate
  caller-visible facts, not just one blended "sample alpha" concept.
- The same caller recheck also shows where that side channel stops being
  independent. Before the final inverse sample, `FUN_180004640` runs a polar
  normalization loop that reads `param_1 + 0xf252` per cell. If that value is
  zero it clears RGB in `+0xe`; otherwise it normalizes RGB from `+0xf250` and
  then writes the preserved `0xf252` value into `+0xe.alpha`. The final
  inverse sampler `FUN_180009d80` is then called on `param_1 + 0xe` only. So
  the last output stage does not consume `0xf252` directly: by that point the
  preserved validity/alpha side channel has already been collapsed into the
  normalized polar RGBA alpha stored in `+0xe`.
- 2026-07-10 Windows sampler-args return binds the final inverse sampler call
  for Zoom case_0009 at `OLMRadialBlur+0x5e68` and its return at `+0x5e6d`.
  The coordinate gate is `(EBX,R13D)=(x,y)`. For `(7,0)`, `(8,0)`, and
  `(24,0)`, `RCX` is the same pool, `RDX`/`RDI` identify a distinct
  four-float destination cell, and `R8/R9` are consistently `1104/1800`.
  The cell destinations advance by 16 bytes, matching the static
  `FUN_180009d80` output-cell stride. This proves the sampler ABI and cell
  binding, not the values of the upstream `+0xf250/+0xf252/+0xe` collapse
  planes; see
  `refs/conformance/olmradialblur_zoom_case0009_sampler_args_intake_20260710.md`.
- 2026-07-05 local Unicorn emulation confirms this final inverse-sample
  boundary for tiny Rotation `case_0010`. After running the CPU `.aex` through
  `FUN_180008690 -> FUN_180007520 -> FUN_180004640`, the normalized `+0xe`
  cells retained in earlier Windows CDB logs match to `<=1 ULP` RGB with exact
  alpha. A direct call sequence `FUN_180001b10(1614,6)` followed by
  `FUN_180001000(+0xe, sample_x=1603.839558785, sample_y=844.317504883)`
  returns near-black `[-0.004081939, -0.004081939, -0.004081939, 1.0]`.
  Therefore the legacy PNG white witness at `(1614,6)` is not explained by the
  observed CPU `.aex` normalized-polar final sampler path.

## Size-Variation / Scatter-Span Source (2026-06-15, RESOLVED)

The two scalar source-space layers feeding `+0x40` and `+0x50` are built before
`FUN_180004640` runs, in the layer-allocation/fill function (decomp
`~3160..3398`):

- `param_5[0x21]` is the per-pixel **size map**. When the Size Variation gate
  `+0x44 == 0`, it is filled with constant `1.0f` (`FUN_180006500`, decomp
  3270-3273). When enabled, `FUN_180008930` builds it from a connected-component
  /run-length distance transform over the alpha mask `mask[i] = (src.alpha > 0)`
  (decomp 3284-3286), and `+0x4c` stores the map maximum for normalization.
- `param_5[0x11]` (= `param_2[0x11]`, the `+0x50` **factor** plane in source
  space) is computed (decomp 3309-3324) as
  `size_factor[i] = (sizemap[i] / sizemap_max) * SV + (1.0 - SV)`,
  where `SV = +0x40_render_param = Size Variation * 0.01`. With `SV = 0` this is
  exactly `1.0` for every pixel.
- `param_5[0x12]` (= `param_2[0x12]`, the `+0x40` **scatter span/gate** plane in
  source space) is computed by `FUN_1800065c0` (decomp 2858-2887) as
  `span_gate[i] = (NV * noise[i] + (1.0 - NV)) * size_factor[i]`, where
  `NV = +0x3c_render_param = Noise Variation * 0.01`. With `NV = 0` this is
  exactly `size_factor[i]`; with both `NV = 0` and `SV = 0` it is exactly `1.0`.

`FUN_180001c90` reads `+0x40` as `param_10` and sets the effective scatter
length `effective_len = int(base_len * param_10)` (decomp 599). So the
size-variation map scales the per-cell inner/outer scatter length, and the
size factor / noise factor are NOT a final alpha multiply — they retune the
Gaussian span before the table is reindexed by `30000 / effective_len`.

Empirical confirmation from the 2026-06-15 sizevar references: for the fully
opaque `current_olm_cells` input, `sv000_edge000`, `sv050_edge000`, and
`sv100_edge000` outputs are **byte-identical**. This is consistent with the
formula: a fully opaque mask is a single region, so the normalized distance map
is (near-)uniform and `size_factor` is constant; a constant span scale that is
applied per cell and then re-normalized by the accumulated alpha-weight sum
cancels out, leaving the image unchanged. Size Variation therefore only has a
visible effect on inputs with non-trivial alpha structure (the `alpha_*`
references), where the distance transform is non-uniform.

## Prepass And Scatter Wiring

- `FUN_180002780` call site (`180004c31..180004c6a`) receives
  `param_2=+0x38`, `param_3=+0x48`, `param_4=+0x50`,
  `param_9=+0x3c940`, and `param_10=+0x3c948`.
- `FUN_1800024c0` call site (`180004cb1..180004cef`) receives
  `param_2=+0x38`, `param_3=+0x48`, `param_4=+0x40`, valid-byte plane,
  `param_10=+0x3c940`, and `param_11=+0x3c948`.
- Therefore the AEX sequence is:
  `prepass(+0x38, +0x48 out, +0x50 factor)`, then
  `scatter(+0x38, +0x48 prepass alpha, +0x40 span/gate)`.

## FUN_180002780 Edge Fade / Seed Facts

- Rotation setup scales Outer Edge Fade `+0x6c` into `param_1+0x3c930` and
  builds table `param_1+0x3a9f0`; it scales Inner Edge Fade `+0x70` into
  `param_1+0x3c934` and builds table `param_1+0x3b990`.
- For each cell, `FUN_180002780` reads polar RGBA from `+0x38`, factor from
  `+0x50`, and starts the gathered alpha from source alpha (`fVar32 =
  polar.a`) and weight sum `1.0`. That is the self seed.
- If source alpha is zero or factor is zero, it clears the prepass/scatter RGB
  accumulation output at `+0x3c940` for that cell to `0,0,0,0`.
- Otherwise it gathers neighboring alpha in the outer/backward angular
  direction using table `+0x3a9f0` for span `int(edge_fade_outer * factor)`,
  and in the inner/forward angular direction using table `+0x3b990` for span
  `int(edge_fade_inner * factor)`.
- After either branch, it writes the computed alpha to both the `+0x48`
  prepass alpha plane and the `+0x3c948` final/max-alpha plane. The nonzero
  branch also writes prepass output RGB as `computed_alpha * polar.rgb` and
  output alpha as `computed_alpha` into `+0x3c940`.

## FUN_1800024c0 Scatter Facts

- The scatter gate is `(valid byte != 0) && (+0x48 prepass alpha != 0) &&
  (+0x40 span/gate != 0)`.
- For each gated cell it calls `FUN_180001c90` outer first with direction
  `0`, then inner with direction `1`.
- Dynamic offset is radius-row dependent:
  `int((radius_count / 2 * offset_value) / current_row_index)` in decomp shape.
  Outer offset value comes from `param_1+0x28`; inner from `param_1+0x30`.
- 2026-06-17 field ownership recheck from `FUN_180004640` setup:
  `param_1+0x24` is outer offset mode, `+0x28` is outer offset value,
  `+0x3a9e8` is outer strength/base length; `param_1+0x2c` is inner offset
  mode, `+0x30` is inner offset value, and `+0x3a9ec` is inner strength/base
  length. All three span-relevant UI values are written after the same
  `DAT_180021608 / quality_step` scale and integer truncation. This supports
  the CLI's current Quality/5 span-scaling ownership and means the unresolved
  `span-minus-one` gain is not explained by applying Quality scaling to only
  Strength or only Offset.
- The values passed into `FUN_180001c90` are prepass alpha (`+0x48`) plus
  source RGB from `+0x38` and scalar span/gate from `+0x40`.
- 2026-06-17 Ghidra MCP recheck: `FUN_180001c90` computes
  `span = int(resolved_distance * param10)`, clamps the resolved distance to
  `3000`, then samples direction-specific weight tables at `param_1+0x68`
  (outer/forward) and `param_1+0x1d528` (inner/backward) using
  `int(sample_index * (30000 / span))`. It accumulates weighted RGBA into the
  scatter buffer and writes a per-cell max-alpha plane. This confirms the next
  RadialBlur work should audit normalization/writeback around the scatter
  buffers, not force fixed Quality or PNG-fit a span constant.
- 2026-06-17 Ghidra MCP re-read of `FUN_180001c90 @ 0x180001c90`
  confirms the inner/backward path is not same-row circular modulo. When the
  angular index underflows, it rewinds the angular coordinate to the row tail
  and advances the destination pointer to `(radius_row + 1) * angular_count`.
  The C++ CLI therefore defaults `inner_wrap_mode` to `aex-next-row`.
- 2026-06-17 Ghidra MCP pass on `FUN_180004640` confirms the post-scatter
  writeback order: allocate `+0x3c940` as RGBA accumulation and `+0x3c948` as
  a scalar max/denom plane; run `FUN_180002780`; run `FUN_1800024c0`; then
  normalize each polar cell by checking `+0x3c948`. If the scalar is zero, RGB
  is cleared. Otherwise RGB output in `+0x38` is `+0x3c940.rgb /
  +0x3c940.alpha`, while alpha output in `+0x38` is the scalar from
  `+0x3c948`. This supports the current max-alpha final-alpha model, but also
  means the remaining error is more likely in exact prepass/scatter population,
  table sampling, or Quality/radius geometry than in a simple final denominator
  toggle.

## CLI Mirror Status

- The current C++ CLI has diagnostic mirrors for the AEX sampler
  (`sample_rgba_aex_alpha`), polar valid mode, prepass factor modes, seed modes,
  scatter span/param10 planes, and final alpha/RGB denominator modes.
- 2026-06-17: the CLI now routes nonzero Rotation Inner Size Variation through
  the source-scatter/prepass path even when `--inner-source-scatter-prepass` is
  not explicitly passed. It builds a source alpha-mask size factor, samples it
  into the polar `+0x50` factor plane, and feeds the same factor into the
  `+0x40` span/gate plane for `effective_span = int(span * param10)`. This is
  a normal CLI coverage path for Size Variation, but still not a byte-match
  claim for all Inner behavior.
- Measurement against `radialblur_inner_size_variation_20260606`:
  `--ignore-size-variation` had `rb_inner_alpha_sv050_edge000 max=213
  mean=5.194305` and `rb_inner_alpha_sv050_edge025 max=230 mean=9.485505`.
  The new plane path gives `edge000 max=236 mean=5.2167` and improves
  `edge025` to `max=250 mean=6.0182`. Opaque SV 0/25/50/100 remain at the
  same `max=255 mean=0.3415` diagnostic residual, while byte-identical
  reference outputs confirm Size Variation cancels on the fully opaque input.
- The CLI still contains diagnostic alternatives; do not treat those switches
  as settled AEX behavior. The settled asm facts are the caller plane ownership,
  helper selection, prepass writeback to `+0x48/+0x3c948`, and scatter gating
  through valid byte, `+0x48`, and `+0x40`.
- Verification after promotion: `radialblur_inner_size_variation_20260606`
  runs without `--ignore-size-variation` or explicit prepass flags and reports
  `rb_inner_sv000_edge000 max=6 mean=0.0873`, the other opaque grid cases at
  `mean=0.3415/0.3396/0.3465`, and alpha-grid cases at
  `mean=5.2167/6.0182`. `radialblur_inner_20260605` default metrics are
  unchanged, so the change is scoped to nonzero Size Variation.
- 2026-06-17 returned software-only full Inner set:
  `olm_reference_return_windows_20260617_radialblur_inner_full_software`
  contains 10 cases. Current CLI metrics are:
  `rb_inner_existing_0011 max=254 mean=37.2623`,
  `rb_inner_existing_0012 max=252 mean=4.0098`,
  `rb_inner_only_strength_small max=2 mean=0.1662`,
  `rb_inner_only_strength_large max=57 mean=2.0896`,
  `rb_inner_offset_mode_3 max=8 mean=0.1255`,
  `rb_inner_edgefade_only max=151 mean=5.6547`,
  `rb_outer_inner_edgefade max=100 mean=3.2042`,
  `rb_inner_quality_1 max=254 mean=25.5424`,
  `rb_inner_existing_0013 max=253 mean=4.5767`, and
  `rb_inner_quality_50 max=254 mean=23.7495`. The small-strength and
  offset-mode probes are close, while high-strength, Quality, and Edge Fade
  remain red.
- A read-only explorer suggested trying the already-supported AEX prepass route
  for full Inner with decomp-shaped flags. That existing candidate was measured
  with `--inner-source-scatter-prepass --inner-prepass-mode tail-gather
  --inner-prepass-factor-mode one --inner-prepass-weight-mode aex-alpha
  --inner-scatter-param10-plane factor --inner-final-alpha-mode max
  --inner-rgb-denominator-mode max` against the same full software set and was
  much worse: `rb_inner_existing_0011 mean=86.9519`,
  `0012 mean=29.0275`, `small mean=55.2078`, `large mean=53.8306`,
  `offset_mode_3 mean=55.1882`, `edgefade_only mean=129.8665`,
  `outer_inner_edgefade mean=131.1275`, `quality_1 mean=132.8091`,
  `0013 mean=23.2612`, `quality_50 mean=40.9856`. Do not promote that flag
  set as the full-Inner default. Keep the next search on exact radius/Quality
  geometry, `FUN_180002780` details, and `FUN_180001c90` table sampling.

2026-06-17 live-Ghidra continuation:

- Ghidra MCP re-read `FUN_180002780 @ 0x180002780`. It confirms the prepass
  starts with source alpha and weight sum `1.0`, uses the factor plane as the
  multiplier for both Edge Fade spans, samples the backward/outer table at
  `+0x3a9f0` and forward/inner table at `+0x3b990` with `CVTTSS2SI`, divides
  gathered alpha by gathered weight sum, writes `computed_alpha * polar.rgb`
  and `computed_alpha` to the RGBA accumulation buffer, and writes the same
  computed alpha to both scalar planes.
- A read-only Ghidra explorer rechecked setup around `FUN_180004640` and found
  that Quality affects more than the angular grid: `quality_step = 1/Quality`
  feeds a `0.2 / quality_step = Quality / 5` scale before the integer
  strength/offset/edge-fade spans are built. This is now exposed as the
  diagnostic CLI flag `--aex-quality-span-scale`.
- The same explorer confirmed the inner direction in `FUN_180001c90` is not a
  same-row modulo wrap: on angular underflow it advances to the next radius row
  and the row tail. The CLI already exposes that diagnostic as
  `--inner-wrap-mode aex-next-row`.
- Additional measurement on the 10-case software-only full Inner return:

| candidate | existing 0011 | existing 0012 | small | large | offset3 | edgefade | outer+inner edgefade | quality1 | existing 0013 | quality50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| default | 37.2623 | 4.0098 | 0.1662 | 2.0896 | 0.1255 | 5.6547 | 3.2042 | 25.5424 | 4.5767 | 23.7495 |
| `--aex-quality-span-scale` | 37.2623 | 4.0098 | 0.1662 | 2.0896 | 0.1255 | 5.6547 | 3.2042 | 15.2878 | 4.6547 | 23.2964 |
| `--inner-source-scatter-prepass` | 19.3670 | 4.3033 | 0.5182 | 0.1263 | 0.2884 | 4.3060 | 2.3311 | 70.2262 | 4.4715 | 19.9495 |
| `--inner-source-scatter-prepass --inner-prepass-mode tail-gather` | 27.3205 | 4.0825 | 0.5182 | 0.1263 | 0.2884 | 5.0243 | 2.5766 | 61.6733 | 4.5635 | 20.2265 |
| `--inner-source-scatter-prepass --aex-quality-span-scale --inner-wrap-mode aex-next-row` | 19.3659 | 4.3034 | 0.5244 | 0.1911 | 0.3159 | 4.3039 | 2.3296 | 15.4989 | 4.2821 | 14.6018 |
| `--inner-source-scatter-prepass --aex-quality-span-scale` | 19.3670 | 4.3033 | 0.5182 | 0.1263 | 0.2884 | 4.3060 | 2.3311 | 15.4996 | 4.2821 | 14.6028 |
| promoted default: source-scatter + Quality/5 + Edge-Fade prepass | 19.3670 | 4.3033 | 0.5182 | 0.1263 | 0.2884 | 3.9604 | 2.0848 | 15.4996 | 4.2821 | 14.6028 |
| `--inner-source-scatter-prepass --aex-quality-span-scale --inner-scatter-span-minus-one` | 19.3342 | 4.1421 | 0.2275 | 0.1246 | 0.1770 | 4.3049 | 2.3305 | 15.2553 | 4.3221 | 14.5948 |
| promoted default + `--inner-scatter-span-minus-one` | 19.3342 | 4.1421 | 0.2275 | 0.1246 | 0.1770 | 3.9594 | 2.0841 | 15.2553 | 4.3221 | 14.5948 |
| `--inner-source-scatter-prepass --aex-quality-span-scale --inner-scatter-loop-minus-one` | 19.3342 | 4.1913 | 0.5051 | 0.1246 | 0.2894 | 4.3049 | 2.3305 | 15.0997 | 4.2711 | 14.5948 |
| `--inner-source-scatter-prepass --aex-quality-span-scale --inner-scatter-table-span-minus-one` | 19.3670 | 4.2490 | 0.2542 | 0.1263 | 0.1810 | 4.3060 | 2.3311 | 15.6519 | 4.3329 | 14.6028 |

- Quality span scaling is binary-backed and improves Quality=1 immediately.
  Combining it with source-scatter and AEX next-row wrap improves strong Inner,
  Edge Fade, and Quality=50, but regresses the already-close small-strength and
  offset-mode probes by max/error shape. Keep it diagnostic for now; the next
  bounded patch should separate the source-scatter/next-row condition from the
  already-close low-span cases rather than promoting it globally.
- Follow-up probes narrow the low-span regression: `--inner-wrap-mode
  aex-next-row` is effectively neutral versus circular, so wrap is not the
  primary cause. Disabling the source seed with `--inner-scatter-seed-mode
  none` is strongly negative (`small mean=2.3227`, `offset3 mean=1.3818`),
  confirming the prepass/self seed is required. A diagnostic
  `--inner-scatter-span-minus-one` recovers much of the low-span regression
  while preserving the Quality gains (`small mean=0.2275`, `offset3 mean=0.1770`,
  `quality1 mean=15.2553`, `quality50 mean=14.5948`). Because live decomp of
  `FUN_180001c90` itself does not show this subtraction. The CLI diagnostic
  is now limited to the inner helper path, so treat it as evidence of a
  caller-resolved inner distance or loop-bound mismatch that still needs binary
  confirmation before default promotion.
- Follow-up split probes make that caution stronger. `--inner-scatter-loop-minus-one`
  is not the low-span fix (`small mean=0.5051`, `offset3 mean=0.2894`), though
  it helps Quality=1 slightly (`mean=15.0997`). `--inner-scatter-table-span-minus-one`
  recovers some low-span/table-endpoint error (`small mean=0.2542`,
  `offset3 mean=0.1810`) but worsens Quality=1 (`mean=15.6519`) and still does
  not match the combined `span-minus-one` diagnostic. Therefore the combined
  diagnostic is not a clean AEX loop-bound fact; it remains a marker that the
  inner span owner, weight reindex length, or caller distance is still not
  precisely modeled.
- Live re-read of `FUN_1800024c0 @ 0x1800024c0` shows no separate low-span
  caller path: for each gated polar cell it computes outer/inner resolved
  distances from `(radius_count / 2) * offset_value / (row + 1)` and calls
  `FUN_180001c90` outer then inner. The gate is still valid byte, prepass alpha,
  and span/gate plane. `--inner-scatter-span-minus-one` therefore should not be
  interpreted as a discovered branch; it is an inner-path diagnostic for a
  remaining loop bound / effective length mismatch.
- Live re-read of `FUN_18000b680 @ 0x18000b680` confirms the Gaussian table
  builder uses `exp(-(i*i) / (param_2*param_2*2*0.111111119389534 + 1e-5))`.
  For the main scatter tables, `FUN_180004640` builds 30000-entry tables and
  `FUN_180001c90` reindexes them by integer `30000 / effective_len`. This
  matches the CLI's broad `rotation_gaussian_weights()` shape, so the current
  best next audit is exact loop count / effective length ownership, not a new
  Gaussian constant.
- Rechecking `--dynamic-offset-mode aex-row` on top of the current best
  diagnostic is effectively neutral (`offset3 mean=0.1769` vs `0.1770`; all
  other listed means unchanged within rounding). This confirms the live
  `FUN_1800024c0` distance formula is already represented by the current CLI
  modes and should not be the next tuning target.
- 2026-06-22 Mac-side current-default matrix supersedes the older mixed
  diagnostic table for prioritization, without changing binary facts. Wide
  report:
  `refs/reports/olmradialblur_inner_candidate_matrix_20260622_002848/`.
  Against all ten 20260617 full-Inner Software cases, `loop-minus-one` is the
  best total-mean candidate (`63.793179` vs current `64.313564`) and improves
  7/10 cases, especially existing/Quality cases. It still worsens the low-span
  family (`small`, `large`, `offset_mode_3`). `circular-wrap` is best for the
  low-span family, and `table-span-minus-one` is best for Edge Fade families.
  Because each family wants a different diagnostic, none of these can be
  promoted as a global binary-grounded rule. The next useful proof is a direct
  `FUN_180001c90` witness for one low-span cell and one Quality cell recording
  caller span, `param10`, effective span, table step, loop limit, underflow
  handling, and first/last write coordinates.
- Static re-read of `disasm/OLMRadialBlur.aex.asm.txt` after the wide matrix
  keeps `loop-minus-one` as a rejected binary rule: the outer unrolled loop
  exits by comparing `R10D` with the saved effective span, and the inner
  unrolled/tail paths also compare `R10D < R14D` through `1800023e0..248a`.
  The inner underflow path at `180002138..2165` / `1800023e0..2409` advances
  to `(row + 1, angular_count - 1)`, matching the `aex-next-row` model.
  Therefore the fact that `loop-minus-one` and `circular-wrap` improve
  different case families is best interpreted as evidence that the upstream
  effective span, `param10`, or source/prepass plane value is still wrong for
  those families, not that the helper globally subtracts one or circular-wraps.
- `FUN_180002780` and `FUN_180001c90` ownership is now promoted into the C++
  CLI defaults for Inner: source-scatter/prepass is used whenever Inner is
  active, Quality/5 span scaling is on by default, inner underflow uses
  `aex-next-row`, and the prepass uses Edge Fade spans, AEX-style factor
  reindexing, and literal factor `1.0` when Size Variation is disabled. The
  full Inner software set now measures `existing_0011 mean=19.3659`,
  `existing_0012 mean=4.3034`, `small mean=0.5244`,
  `large mean=0.1911`, `offset3 mean=0.3159`, `edgefade mean=3.9581`,
  `outer+inner edgefade mean=2.0832`, `quality1 mean=15.4989`,
  `existing_0013 mean=4.2821`, and `quality50 mean=14.6018`.
- Size Variation default recheck after this promotion is mostly unchanged for
  opaque cases (`sv000..sv100 edge000 mean=0.3654`, `sv050_edge025 mean=0.3634`,
  `sv100_edge050 mean=0.3703`) and preserves `alpha_sv050_edge000 mean=5.2167`;
  `alpha_sv050_edge025` is `mean=6.5061`, so the remaining alpha +
  Edge Fade path should be treated as a factor-plane/writeback residual rather
  than a reason to revert the Ghidra-backed prepass ownership.
- A follow-up `param10` plane probe with Quality/5 scaling did not explain the
  `span-minus-one` gain: `--inner-scatter-param10-plane polar-alpha` and
  `prepass-alpha` both measured `small mean=0.5182`, `offset3 mean=0.2884`,
  `quality1 mean=15.7157`, `quality50 mean=14.8290`. That is worse than
  `--inner-scatter-span-minus-one` and does not recover low-span cases. Keep
  `+0x10` plane ownership as a live fact, but do not use simple polar/prepass
  alpha substitution as the default scatter-span model.
- With `aex-next-row` now default, the best remaining diagnostic on the full
  Inner set is still `--inner-scatter-span-minus-one`: `existing_0011
  mean=19.3331`, `existing_0012 mean=4.1421`, `small mean=0.2346`,
  `large mean=0.1897`, `offset3 mean=0.2057`, `edgefade mean=3.9571`,
  `outer+inner edgefade mean=2.0825`, `quality1 mean=15.2530`,
  `existing_0013 mean=4.3221`, and `quality50 mean=14.5937`. It remains a
  diagnostic only because `FUN_180001c90` does not visibly subtract one; treat
  this as evidence for an unresolved caller distance / effective length /
  loop-bound mismatch, not a settled binary fact.

## Inner Scatter Population Diagnostic

2026-06-17 follow-up: the C++ CLI now has a non-render-affecting
`--inner-scatter-stats path.json` diagnostic for the source-scatter/prepass
path. It records inner call counts, source skips, effective-span and loop-limit
histograms, write population, next-row underflow wraps, radius OOB skips, and
zero-contribution skips. A same-input smoke confirmed the flag does not change
the output PNG byte stream.

On `radialblur_inner_20260605__software__fr24__rb_inner_only_strength_small`,
default stats were:

- active inner sources: `1,418,861` (`inner_calls=1,987,200`,
  `inner_source_skips=568,339`)
- `inner_effective_span_hist={"32": 1418861}`
- `inner_loop_limit_hist={"32": 1418861}`
- `inner_writes=43,984,691`
- `inner_underflow_wraps=476,438`

With `--inner-scatter-span-minus-one`, the same case becomes:

- `inner_effective_span_hist={"31": 1418861}`
- `inner_loop_limit_hist={"31": 1418861}`
- `inner_writes=42,565,830`
- `inner_underflow_wraps=446,636`

The write-count delta is exactly one neighbor write per active inner source
(`1,418,861`). This explains why the diagnostic meaningfully changes low-span
cases, but it does **not** prove an AEX `span - 1` rule: the objdump/decomp
loop still uses `iVar7 = 1` and writes while `iVar7 < iVar10`, where
`iVar10 = int(resolved_distance * param10)`. Keep `--inner-scatter-span-minus-one`
as a population diagnostic until the caller-resolved distance, table divisor,
or loop-bound ownership is proven.

2026-06-18 read-only explorer audit tightened the next action:

- Do not request more Windows renders for Inner right now. Full Inner,
  Size Variation, and Edge Fade cases are already covered; the next blocker is
  binary evidence, not another PNG set.
- Use `rb_inner_only_strength_small` from `radialblur_inner_20260605` as the
  narrow witness case: Inner Strength is `32`, Quality is `5`, and Offset /
  Edge Fade are zero, so the suspected `32` vs `31` effective-span ambiguity is
  not hidden behind other parameters.
- The helper itself still does not show a subtract-one rule:
  `180001d0f..180001d18` computes `R14D = int(span * param10)`,
  `180001d33..180001d43` computes `30000 / R14D`, and the later loops compare
  against `R14D`. `FUN_1800024c0` calls the helper outer then inner at decomp
  lines around `882..886`, passing the caller-resolved distance in `R8D`.
- Next binary-grounded action: with the Windows AEX under a debugger or an
  equivalent register trace, break on the inner call site near `0x1800026e5`
  for `rb_inner_only_strength_small` and dump the incoming `R8D`/distance,
  the value from the span/gate plane (`param10`), table base
  `param_1+0x3a9ec`, and the resulting `R14D` inside `FUN_180001c90`. If
  `R14D` is `31`, fix caller span setup; if it is `32`, keep
  `--inner-scatter-span-minus-one` diagnostic-only and look for an unmodeled
  write/pointer edge rather than promoting a span decrement.

2026-06-18 CLI traceable mirror update, superseded later the same day by the
Windows runtime trace below:

- `cli/OLMRadialBlur/main.cpp` now writes `outer_caller_span_hist` and
  `inner_caller_span_hist` in `--inner-scatter-stats`, alongside the existing
  effective-span and loop-limit histograms. These are non-render-affecting
  diagnostics for the values passed from the `FUN_1800024c0`-equivalent caller
  into the scatter helper.
- The original same-day mirror asserted the static interpretation:
  `inner_caller_span_hist={"32": 1987200}`,
  `inner_effective_span_hist={"32": 1418861}`,
  `inner_loop_limit_hist={"32": 1418861}`, and `inner_writes=43984691`.
  The later Windows runtime trace recorded `R14D=31`, so
  `refs/scripts/smoke_olmradialblur_cpp_inner_small_scatter_stats_cli.py`
  now asserts the runtime-grounded default:
  `inner_caller_span_hist={"32": 1987200}`,
  `inner_effective_span_hist={"31": 1418861}`,
  `inner_loop_limit_hist={"31": 1418861}`, and `inner_writes=42565830`.
- Before the runtime trace, running the same case with
  `--inner-scatter-span-minus-one` left the caller span histogram at
  `{"32": 1987200}` but changed the post-diagnostic effective span and loop
  limit to `{"31": 1418861}`. That diagnostic is now the default because the
  Windows trace proved the witness helper invocation reaches `R14D=31`.
- Static disasm also supports the caller-span ownership: the inner call at
  `1800026e5` receives `R8D` from `[rsp+0x138]`; that slot is computed at
  `1800025d6..1800025e1` as
  `trunc(((param_7/2) * inner_base) * (1.0f / (row + 1)))`. For the small
  witness case, Offset and Edge Fade are zero and `param10` is `1`, so the
  mirror's `32` caller span is still the static caller interpretation. The
  runtime trace resolves the helper-effective span to `31`, so keep the caller
  histogram as `32` while rendering with the runtime-grounded span-31 helper
  population.

2026-06-18 Ghidra DB annotation pass:

- `FUN_180001c90` was renamed in the Ghidra project to
  `RadialBlur_scatter_tail_by_direction` and given an explanatory prototype:
  `ctx`, `direction_is_inner`, `caller_distance`, `angle_index`,
  `radius_index`, `source_alpha`, RGB, `span_gate`, `angular_count`,
  `accum_rgba`, and `max_alpha`.
- `FUN_1800024c0` was renamed to `RadialBlur_scatter_valid_polar_cells`.
- Comments were added at `1800026e5` (inner helper call), `180001d18`
  (`R14D = trunc(float(resolved_span) * span_gate)`), `180001d33`
  (`30000 / effective_len` table step), and `1800023e0` (inner scalar tail
  loop compares `offset < effective_len`).
- The renamed decompile makes the static ownership explicit: caller distance is
  passed in `R8D`, the helper applies Offset Mode / span base / `span_gate`,
  and the loop bound remains the computed effective length. Treat this as the
  reason to keep both caller-span and effective-span histograms in diagnostics:
  caller-span stays `32`, while the traced helper-effective span for the small
  witness is `31`.

2026-06-18 Gaussian table audit:

- `FUN_180004640` builds both rotation scatter Gaussian tables with fixed
  length `0x7530` (`30000`): outer at `param_1+0x68` and inner at
  `param_1+0x1d528`. `FUN_18000b680` writes `table[i]` for `i=0..length-1`
  without normalization.
- Raw constants from `plugins_2025/OLMRadialBlur.aex`:
  `0x180021738 = 0.111111119389534f`, `0x180021740 = 1.0e-5` as double,
  and `0x1800212d4 = 1.0f`.
- The AEX table formula is:
  `table[i] = expf(-(float)(i*i) / denom)`, where
  `denom = float(float(length) * float(length) * 0.111111119389534f * 2.0f
  + 1.0e-5)`. For scatter tables with `length=30000`, this rounds to
  `200000016.0f`. The vector body uses `RCPPS` plus one Newton refinement
  before a vector exp helper; scalar tail uses `DIVSS` and a scalar expf-like
  helper.
- `cli/OLMRadialBlur/main.cpp` now has diagnostic
  `--rotation-gaussian-mode aex-float`, which uses the AEX-style float
  denominator and float exponent argument while leaving the default `double`
  path unchanged.
- Measuring the 10-case `radialblur_inner_20260605` software return showed
  only tiny mixed movement, e.g. default vs `aex-float`:
  `existing_0011 mean=19.3659 -> 19.3658`,
  `existing_0012 4.3034 -> 4.3022`,
  `small 0.5244 -> 0.5245`,
  `large 0.1911 -> 0.1917`,
  `offset_mode_3 0.3159 -> 0.3201`,
  `quality_1 15.4989 -> 15.5006`.
  So Gaussian table float/double drift is not the main RadialBlur Inner
  residual. Keep the flag diagnostic-only unless a later byte-level fact
  requires exact MSVC SIMD exp parity.

2026-06-18 rotation grid float diagnostic:

- `FUN_180004640` creates the polar grid with `angular_count = int(360.0f /
  quality_step)` and a precomputed sin/cos table. It uses `FUN_180001bb0` to
  derive the radius bounds, then subtracts 2 from the min radius after ratio
  scaling and adds 2 to the max radius. `FUN_180001b10` maps output pixels back
  to polar space with float `sqrt`/`atan2f`.
- `cli/OLMRadialBlur/main.cpp` now has diagnostic
  `--rotation-grid-mode aex-float`, which keeps default behavior unchanged but
  uses float-oriented polar-grid generation and float-oriented inverse
  cartesian-to-polar indexing for Rotation.
- Measuring the 10-case `radialblur_inner_20260605` software return again
  showed only tiny mixed movement, e.g. default vs `aex-float` grid:
  `small 0.5244 -> 0.5242`,
  `large 0.1911 -> 0.1910`,
  `offset_mode_3 0.3159 -> 0.3158`,
  `quality_1 15.4989 -> 15.4990`,
  while the larger residual cases were unchanged within printed precision.
  Therefore broad float/double grid drift is not the main Inner residual.
  Keep this as a diagnostic switch and continue with exact sampler validity,
  helper loop/state ownership, or a Windows register trace for the
  `32` vs `31` effective-span question.

2026-06-18 sampler/validity remeasure on current CLI defaults:

- Re-ran `refs/scripts/smoke_olmradialblur_cpp_inner_polar_sample_probe_cli.py`
  after the current source-scatter/prepass defaults, Quality/5 scaling,
  `aex-next-row`, Gaussian diagnostics, and grid diagnostics were in place.
  The old notes were directionally useful but numerically stale.
- Old Inner cases with `--polar-sample-mode plain` now measure
  `case_0011 mean=26.1534`, `case_0012 mean=10.6248`,
  `case_0013 mean=13.2212`. `aex-alpha` gives
  `23.7898`, `12.3460`, `14.1928`; `conditional-inner` gives
  `23.7898`, `10.6248`, `14.1928`. So the AEX alpha-weighted RGBA sampler
  still helps `0011`, but it now regresses `0012` and `0013` under the current
  model.
- Edge Fade cases still prefer the plain sampler:
  plain/conditional `case_0024/0025/0027 mean=5.8034/4.8054/2.3524`, while
  `aex-alpha` gives `6.3103/5.5407/3.1133`.
- Re-ran `refs/scripts/smoke_olmradialblur_cpp_inner_polar_valid_probe_cli.py`.
  `strict` gives `case_0011/0012/0013 mean=26.1534/10.6248/13.2212`;
  `aex-repeat` gives `26.0576/10.6270/13.2160`. This is a tiny mixed change,
  not a main residual. Keep sampler/validity switches diagnostic-only.
- Updated conclusion: the remaining Inner residual is not solved by a global
  sampler promotion. The best next binary-grounded target remains
  `FUN_180001c90` runtime span/loop state or a more exact explanation for why
  `case_0011` prefers the AEX alpha-weighted sampler while Edge Fade and
  other Inner cases do not.

2026-06-18 Windows runtime trace return:

- Imported return package:
  `~/Downloads/olm_runtime_trace_return_windows_20260618.zip`.
  Normalized summary lives at `refs/reports/runtime_trace_summary.md`.
- Witness case: `radialblur_inner_20260605` /
  `rb_inner_only_strength_small` under Windows AE Software render.
- At call site `OLMRadialBlur+0x26e5`, the trace recorded
  `dword ptr [RCX+0x3a9ec] = 0x1f` (`31`), with stack/argument state
  `R8D=0`, `EDX=1`, `R9D=0`, `[rsp+0x138]=0`, and span/factor slots at
  `1.0f`.
- Inside the exact helper invocation, after stepping over
  `cvttss2si r14d, xmm0` at `OLMRadialBlur+0x1d18`, the trace recorded
  `R14D=31`. This answers the previous `32` vs `31` blocker: for this
  witness, the AEX effective inner scatter span is `31`.
- The C++ CLI default now mirrors this population by enabling
  `inner_scatter_span_minus_one` by default. `--no-inner-scatter-span-minus-one`
  remains available as a diagnostic for the previous static interpretation.
- Full `radialblur_inner_20260605` software remeasure after applying the
  span-31 default: `rb_inner_only_strength_small mean=0.2346`
  (from `0.5244`), `rb_inner_existing_0012 mean=4.1421` (from `4.3034`),
  `rb_inner_quality_1 mean=15.2530` (from `15.4989`), and
  `rb_inner_existing_0013 mean=4.3221` (a small regression from `4.2821`).
  This is a binary-grounded improvement, not AE exact.
- 2026-06-19 smoke confirmation: the span-stat guard passes for
  `rb_inner_only_strength_small` with
  `inner_caller_span_hist={"32": 1987200}`,
  `inner_effective_span_hist={"31": 1418861}`,
  `inner_loop_limit_hist={"31": 1418861}`, and
  `inner_writes=42565830`. The broader old Inner measurement remains expected
  red: `case_0011 max=255 mean=23.0495`, `case_0012 max=255 mean=16.0039`,
  `case_0013 max=238 mean=18.0193`.
- Zoom and tiny Rotation guards still pass under the same build:
  `case_0009 max=1 mean=0.0046` and `case_0010 max=255 mean=0.0104`.
  These are regression guards only, not AE exact evidence.
- Remaining Inner work should not ask the same span question again. Continue
  with exact sampler/prepass/writeback details or another narrow runtime
  witness tied to the still-nonzero residual.
