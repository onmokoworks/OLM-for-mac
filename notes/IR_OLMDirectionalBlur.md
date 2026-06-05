# OLMDirectionalBlur Image Processing IR

Status: working intermediate representation for the Windows AEX algorithm.
This file is the implementation target; `OLMDirectionalBlur_ASM_FACTS.md`
keeps address-level evidence, and `PORTING_BOARD.md` keeps long-form history.

## Scope

Current verified reference slice:

- Windows refs: `refs/win_references/20260604_olm/OLMDirectionalBlur`
- Active front-only/no-noise cases: `case_0001..case_0005`
- Back/noise cases: `case_0006..case_0009`, measurement-only for now
- Current Mac plugin: 8bpc front-only/no-noise direct slice; copies unsupported
  back/noise/16-32bpc paths instead of pretending they are ported.

## Evidence Priority

1. `disasm/OLMDirectionalBlur.aex.asm.txt`
2. `decomp/OLMDirectionalBlur.aex.c.txt`
3. Windows PNG/manifest diffs
4. Empirical probes

Empirical probes may suggest direction, but production behavior should not be
promoted unless the IR has an asm/decomp-backed reason or the remaining gap is
explicitly accepted as reference-path uncertainty.

## Parameters

Manifest-visible parameters used by the current refs:

- `Angle`
- `Brightness Gain`
- `Size Variation`
- `Front Blur Strength`
- `Front Alpha Fade`
- `Front Sharp Tail`
- `Back Blur Strength`
- `Back Alpha Fade`
- `Back Sharp Tail`
- `Noise Variation`
- `Noise Type`
- `Noise Layer`
- `Seed`
- `Noise Offset`
- `Thickness`

Internal/runtime parameters:

- `render_scale = *(int *)(ctx+0x11c) / *(int *)(ctx+0x120)`
- AEX scales and truncates Front/Back Blur Strength and Alpha Fade by
  `render_scale`.
- Current CLI `--strength-scale auto = 1 / frame_rate` is a PNG-fit
  measurement hypothesis only. It is not the AEX field mapping.
- 2026-06-06 full-choreography scale sweep on cases `0001..0005` did not expose
  a scalar fix: average mean was `3.7928` at `auto` / `1/24`, `3.7731` at
  `0.03`, `3.8490` at `0.06`, and `3.9352` at `0.08`. `case_0005` improves
  at `0.08`, but cases `0001..0004` worsen. Keep scale as a diagnostic until
  the Windows reference records the actual render-context ratio.

## Buffer Model

Name the two main rotated RGBA float buffers:

- `A = params + 0x8078`
- `B = params + 0x8090`

Support buffers:

- `denom = params + 0x8080`
- `alpha_or_valid = params + 0x8088`
- `component_map = params + 0x8118`

Confirmed front-only/no-noise order:

1. Allocate/clear `A`, `B`, `denom`, `alpha_or_valid`, and `component_map`.
2. Host callback populates `A`.
3. `FUN_180001ec0(A, B, pad_w, pad_h, angle)` rotates `A` into `B`.
4. `memcpy(A, B)` copies the rotated image back into `A`.
5. Build a valid mask from `A.a > 0`.
6. Build `component_map` from the valid mask.
7. `FUN_1800038d0` row-driver reads from `A` and writes/accumulates into `B`
   plus `denom`.
8. Normalize `B.rgb` by `denom`.
9. Clear `A`.
10. `FUN_180001ec0(B, A, pad_w, pad_h, -angle)` rotates normalized `B` back
    into `A`.
11. Repoint `params + 0x8090 = A` for the host-output callback.

`FUN_180001ec0` argument convention:

- `param_1` / `RCX`: source image
- `param_2` / `RDX`: destination image

## Passes

### Gaussian Table

`FUN_180001830` builds tables for:

- front strength: `params + 0x58`
- back strength: `params + 0x4068`
- front alpha fade: `params + 0x3ed8`
- back alpha fade: `params + 0x7ee8`

The current broad Gaussian table is decomp-confirmed. Earlier narrow-table
probes sometimes gave lower diffs but are not faithful.

### Input Rotate

Use `FUN_180001ec0` semantics:

- strict inner-pixel sampling: source sample must satisfy
  `0 < ix < width - 1` and `0 < iy < height - 1`
- bilinear alpha sum is written as output alpha
- RGB corner weights are normalized by the sampled alpha sum

Current probe status:

- direct source-layer -> rotated buffer is the old scaffold.
- `rotated-aex-choreo` creates padded `A` first and rotates `A -> B`; this
  improves diagonal `case_0005` to `mean=1.1703`, but leaves angle-0
  `case_0001` at `mean=4.4483`.
- `rotated-aex-full-choreo` also rotates normalized padded `B` back into a
  padded `A` before cropping. It is numerically unchanged from
  `rotated-aex-choreo` for the tracked cases, so the remaining residual is not
  explained by direct-to-comp output sampling versus padded output ownership.
- `rotated-aex-pad-full-choreo` combines the confirmed host populate
  padding/offset formula with full A/B choreography. It is also numerically
  unchanged from `rotated-aex-full-choreo`, so the one-pixel pad/offset
  difference is not visible on the tracked refs.
- `rotated-aex-prepass-full-choreo` adds the `FUN_180001000`-shaped center
  prepass to the full A/B choreography. It is also numerically unchanged from
  `rotated-aex-full-choreo`, so the center prepass is not visible on the
  current opaque front-only refs when combined with the current scaffold.
- `rotated-aex-truncated-span` uses the exact `FUN_1800013e0` component/tail
  span gate (`effective_span = int(strength * coeff)`, offsets
  `1..effective_span-1`) instead of the previous float threshold. It gives only
  a tiny case1 improvement and worsens case5, so integer span truncation is an
  AEX fact but not the remaining dominant residual.
- `rotated-aex-trunc-output` matches the host-output callback's final
  conversion (`clamp * 255`, then `CVTTSS2SI` truncation). It improves case1
  slightly but worsens case5 slightly, so output quantization is another AEX
  fact rather than the main structural residual.
- `rotated-aex-float-math` uses `FUN_180001ec0`-shaped float angle trig and
  integer half-width/half-height centers. It is neutral on the tracked refs
  (`case_0001 mean=4.4483`, `case_0005 mean=1.1703`), so those rotate-math
  details are not the visible residual source.

### Host Populate / Output Callbacks

Direct `llvm-objdump` confirmed the 8bpc callback pair:

- populate at `0x180006980`
- output at `0x180006b30`

Both use the same padded index:

```text
((params+0x8098 + y) * *(int *)(params+0x80a0) + (params+0x809c + x)) * 4
```

8bpc populate maps AE PF pixel A/R/G/B bytes into work R/G/B/A floats, divided
by the channel max. 8bpc output reads work R/G/B/A, applies `BrightnessGain` to
RGB only, clamps RGB to `1.0`, leaves alpha ungained, multiplies by 255, and
truncates with `CVTTSS2SI`.

Current CLI's centered padded copy/crop and truncating-output diagnostic match
these facts. Host channel order, centered offsets, and output rounding are no
longer leading suspects for the current `case_0001` / `case_0005` residual.

### Component Map

`FUN_1800028e0` builds a per-pixel map from the rotated valid mask.

The row driver uses:

- component area
- max area
- center Y
- half-height / span

2026-06-06 asm/decomp check:

- The AEX scans each row into horizontal non-zero runs and merges runs between
  adjacent rows when their x ranges overlap inclusively.
- This matches 4-connected binary-component behavior, not 8-connected diagonal
  connectivity.
- Component area is the summed run length.
- `center_y` is the integer floor midpoint of min/max row, and `half_height`
  is `max_y - center_y`.
- `rotated-aex-halfheight` removes the CLI's previous `half_height >= 1`
  safety clamp and leaves the AEX value literal. It is neutral on the tracked
  refs (`case_0001 mean=4.4483`, `case_0005 mean=1.1703`).

Current CLI's 4-neighbor component-map approximation matches these facts closely
enough that component connectivity/center rounding is no longer the leading
suspect. Remaining work should focus on host populate/output edge semantics,
render-context scale mapping, exact rotate/validity semantics, or finer
scatter/source-alpha ownership.

### Alpha Fade Prepass

`FUN_180001000` receives the component coefficient before scatter.

Observed role:

- uses Front/Back Alpha Fade lengths, not Blur Strength lengths
- coefficient scales span and table index
- zero original source alpha clears `B[p]`, `denom[p]`, and
  `alpha_or_valid[p]`
- nonzero original source alpha gathers a weighted alpha from the source row,
  then seeds `B[p].rgb = gathered_alpha * A[p].rgb`, `B[p].a =
  gathered_alpha`, `denom[p] = gathered_alpha`, and
  `alpha_or_valid[p] = gathered_alpha`
- scatter skip in `FUN_1800038d0` still checks original `A[p].a`, while
  `FUN_1800013e0` receives `alpha_or_valid` as its alpha/validity input

Probe status:

- `rotated-rowdriver-prepass`: negative for current refs
  (`case_0001 mean=4.7505`, `case_0005 mean=1.3802`)
- `rotated-rowdriver-prepass-init`: also negative
  (`case_0001 mean=4.7724`, `case_0005 mean=1.3862`)
- `rotated-aex-prepass-full-choreo`: neutral against full A/B choreography
  (`case_0001 mean=4.4483`, `case_0005 mean=1.1703`)

Interpretation: the prepass alone is not the missing behavior for opaque
front-only refs, and the current full-choreography prepass scaffold already
models the confirmed seed outputs closely enough to rule out another simple
prepass toggle. Keep it in the IR, but do not treat it as the next isolated
fix.

### Row Driver

`FUN_1800038d0` is the main scatter pass.

For each valid source pixel:

```text
component_coeff = pow(component_area / max_area, SizeVariation)
noise_coeff = optional noise factor
tail = max(0, 1 - abs(row - component_center_y) * SharpTail / half_height)
coeff = component_coeff * noise_coeff * tail
```

`FUN_1800013e0` then uses `coeff` structurally:

- effective span: `int(strength * coeff)`
- processed offsets: `1 <= offset < effective_span`; center offset 0 is never
  included by the scatter helper
- table index: `int(offset / coeff)`
- source RGB is loaded once from `param_4[source].rgb`
- source alpha/validity is loaded once from `param_7[source]`
- per-offset contribution is `param_7[source] * weight_table[int(offset / coeff)]`
- RGB accumulates as `param_4[source].rgb * contribution`
- denominator accumulates the same contribution separately
- output alpha is max-like, not simple alpha sum
- In the `FUN_1800038d0` call sites, `param_4` is `lVar2` / source A buffer.
  `FUN_180001000` writes premultiplied seed pixels into `lVar1` / B, but
  scatter still reads source RGB from A and alpha from `alpha_or_valid`.
- Although the front helper call steps toward lower x indices locally, the
  current rotated AEX probe family still matches references better with CLI
  `--sample-sign 1` after the surrounding rotate/callback coordinate convention
  is included. Rechecking `sample-sign -1` worsens `case_0005` from about
  `1.17` to `1.29..1.30` mean.
- The current CLI representation `source_rgb = raw_rgb * alpha` plus
  `rgb += source_rgb * weight` is algebraically equivalent to AEX
  `rgb += A.rgb * alpha_or_valid * weight` when CLI `alpha` matches the
  prepass `alpha_or_valid`. The remaining source-ownership risk is therefore
  not "scatter reads B as source"; it is whether the prepass alpha and rotate
  population match exactly.

Rejected interpretations:

- destination component coefficient: worsens `case_0005`
- direct alpha attenuation by coefficient: worsens `case_0005`
- alpha-sum final output: essentially no useful improvement
- direct helper-local sign flip as CLI `sample-sign -1`: worsens `case_0005`
- zero-denominator row-driver initialization is negative in the current CLI
  scaffold. `straight-zero` and `premul-zero` both report
  `case_0001 mean=4.4702`, `case_0005 mean=1.1762`; fully zeroed output is
  worse (`case_0001 mean=4.5240`, `case_0005 mean=1.4931`).

### Normalize And Rotate Back

After row-driver scatter:

1. Divide `B.rgb` by `denom` where `denom > 0`.
2. Clear `A`.
3. Rotate `B -> A` with negated angle.
4. Output from `A`.

Current probe status: `rotated-aex-full-choreo` tests the padded output
ownership and is neutral against `rotated-aex-choreo`. The current gap is more
likely in row-driver/denominator ownership or host populate/output edge
semantics than in the final direct-to-comp sampling shortcut alone.

## Current Probe Table

| Probe | case_0001 mean | case_0005 mean | Interpretation |
|---|---:|---:|---|
| direct/front-strength | 4.0897 | 1.1931 | best angle-0 scaffold, not structurally faithful |
| direct-map | 4.0883 | 1.1931 | tiny positive row-driver signal |
| rotated | 4.4483 | 1.2174 | structural base, worse than direct |
| rotated-preserve-alpha | 4.4483 | 1.1831 | useful RGB/alpha split |
| rotated-front-strength-preserve-alpha | 4.0897 | 1.1927 | best combined front-only diagnostic |
| rotated-aex-choreo | 4.4483 | 1.1703 | positive A/B input-rotate signal |
| rotated-aex-full-choreo | 4.4483 | 1.1703 | output-side padded A writeback is neutral |
| rotated-aex-pad-full-choreo | 4.4483 | 1.1703 | exact AEX pad + full A/B is neutral |
| rotated-aex-prepass-full-choreo | 4.4483 | 1.1703 | center prepass + full A/B is neutral |
| rotated-aex-halfheight | 4.4483 | 1.1703 | exact component half-height clamp removal is neutral |
| rotated-aex-float-center | 4.4483 | 1.1703 | float component center_y is neutral |
| rotated-aex-component-tail-only | 4.4484 | 1.1703 | removing global tail gate is neutral |
| rotated-aex-binary-alpha | 4.4483 | 1.1753 | binary validity side-channel is neutral/negative |
| rotated-aex-straight-source-rgb | 4.4483 | 1.1703 | neutral; opaque refs cannot distinguish source RGB premul |
| rotated-aex-float-math | 4.4483 | 1.1703 | float trig + integer centers are neutral |
| rotated-aex-trunc-output | 4.4438 | 1.1736 | exact output truncation is mixed/minor |
| rotated-aex-truncated-span | 4.4467 | 1.1749 | exact integer span gate is mixed/minor |
| rotated-aex-row-init-straight-zero | 4.4702 | 1.1762 | zero denominator / retained straight B is negative |
| rotated-aex-row-init-premul-zero | 4.4702 | 1.1762 | zero denominator / retained premul B is negative |
| rotated-aex-row-init-zero | 4.5240 | 1.4931 | cleared B+denom is strongly negative |
| rotated-rowdriver-prepass | 4.7505 | 1.3802 | negative alpha-fade prepass |
| rotated-rowdriver-prepass-init | 4.7724 | 1.3862 | negative copied-buffer/init hypothesis |

## Implementation Rules

- Keep `direct` as a measurement baseline, not production truth.
- Prefer evolving `rotated-aex-choreo` toward the confirmed A/B order.
- Size Variation is normalized as UI integer / 100.0. The divisor is confirmed
  by `DAT_18000b384 = 100.0` in `plugins_2025/OLMDirectionalBlur.aex`, so raw UI
  scaling is not a tuning knob.
- Do not tune `strength_scale` as the main fix unless Windows references record
  the render-context ratio or the diff becomes clearly scale-dominated. The
  latest full-choreography sweep shows it is not currently scale-dominated.
- Do not implement Noise Variation in production until `FUN_180003370` /
  `params+0x80b0/0x80c0` is represented in this IR.
- Do not promote Back Blur beyond diagnostics until front-only A/B row-driver
  behavior is better constrained.
- Unsupported Mac paths should continue to copy input rather than producing
  plausible but unverified output.

## Next Work

1. Refactor `render_rotated` behind an explicit buffer/state model matching
   `A`, `B`, `denom`, `alpha_or_valid`, and `component_map`.
2. Inspect `FUN_1800013e0` and `FUN_1800038d0` argument mapping for source RGB,
   alpha/validity, output RGB, denominator, and output alpha. Current
   zero-denominator probes are negative, so the next gap is more likely helper
   scatter semantics or host edge handling than simple B/denom initialization.
3. Re-measure `case_0001` and `case_0005`.
4. If angle-0 remains around `mean=4`, inspect render-context scale mapping
   (`ctx + 0x11c / ctx + 0x120`) and finer scatter/source-alpha ownership before
   more parameter sweeps. Host populate/output callbacks and the component-map
   run-merging pass now look consistent with the current CLI approximation.
5. Only after front-only improves, add Back Blur / Noise IR sections.
