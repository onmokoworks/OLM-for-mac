# OLMDirectionalBlur Image Processing IR

Status: working intermediate representation for the Windows AEX algorithm.
This file is the implementation target; `OLMDirectionalBlur_ASM_FACTS.md`
keeps address-level evidence, and `PORTING_BOARD.md` keeps long-form history.

## Scope

Current verified reference slice:

- Windows refs: `refs/win_references/20260604_olm/OLMDirectionalBlur`
- Additional context-scale refs:
  `refs/win_references/olm_reference_return_windows_20260611/OLMDirectionalBlur`
- Active front-only/no-noise cases: `case_0001..case_0005`
- Back/noise cases: `case_0006..case_0009`, measurement-only for now
- Current Mac plugin: 8bpc front-only/no-noise direct slice; copies unsupported
  back/noise/16-32bpc paths instead of pretending they are ported.
- 2026-06-24 focused residual return is `answered_partial`: it includes exact
  Software reference renders and an earlier live-attempt log, but no successful
  per-pixel rowdriver/rotate-path runtime values. The CDB attempt failed
  before `OLMDirectionalBlur` resolved as a loaded module. Keep the current
  implementation blocked on binary/runtime evidence rather than tuning from
  the returned PNGs alone.
- 2026-06-24 decision matrix:
  `refs/conformance/olmdirectionalblur_8bpc_decision.md`
  classifies the current state as `blocked-await-runtime-or-asm-proof`.
  `rotated-front-strength` is the best numeric scaffold but not AEX-shaped;
  the best AEX-shaped candidate still has high residuals. The residual split
  is angle-0 RGB-only rowdriver/valid-alpha versus diagonal rotate/validity,
  and the latest runtime return is not actionable.
- 2026-06-24 witness contract:
  `refs/reports/olmdirectionalblur_witness_contract_20260624/witness_contract.md`
  freezes the next proof boundary. The 2026-06-24 runtime return remains
  `answered_partial` and value-sparse (`has_per_pixel_values=False`), so do
  not tune from it. Active witnesses are:
  - `case_0001 (494,169)`: angle-0 RGB-only residual, reference
    `[164,0,0,255]`, candidate `[0,0,0,255]`, alpha already matches. Required
    proof is typed rowdriver accumulation or valid-alpha side-channel values.
  - `case_0005 (507,367)`: diagonal rotate/validity residual, reference
    `[1,0,0,255]`, candidate `[252,0,0,255]`. Required proof is typed diagonal
    rotate/sampler/validity values. Do not use the angle-0 witness to tune this
    path.
  Keep `direct` / `rotated-front-strength` as measurement baselines only; they
  are not implementation truth despite lower broad means.
- 2026-06-25 witness plan:
  `refs/reports/olmdirectionalblur_witness_plan_20260625/witness_plan.md`
  narrows that boundary into two independent runtime/asm witness families:
  - `angle0-rowdriver-valid-alpha`: primary `case_0001 (465,169)` with
    `[164,0,0,255] -> [0,0,0,255]`; companion strip
    `(487..494,169)` proves the miss is a long RGB-only row, not a one-pixel
    writeback artifact. Required values are normalized parameters, A/B buffer
    coordinates, rowdriver/group membership, valid-alpha side-channel,
    accumulation numerator/denominator, pre-writeback RGBA, and final bytes.
  - `diagonal-rotate-validity`: primary `case_0005 (507,367)` with
    `[1,0,0,255] -> [252,0,0,255]`; companion `(423,187)` has the opposite
    signed red direction `[254,0,0,255] -> [4,0,0,255]`. Required values are
    rotate sampler coordinates/order, border/validity decision, group-size or
    opacity gate, denominator, pre-writeback RGBA, and final bytes.
  The decision is `two-independent-witness-families`: DirectionalBlur stays
  blocked until both families have typed evidence. Do not tune diagonal
  behavior from the angle-0 witness, and do not promote broad measurement
  scaffolds (`direct`, `rotated-front-strength`) from PNG means alone.

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

- `render_scale = *(int *)(ctx+0x11c) / *(int *)(ctx+0x120)`, mapped to
  `PF_InData.downsample_x.num / PF_InData.downsample_x.den` by AE SDK
  `offsetof` (`0x11c` / `0x120`) and the matching Mac OLMBlur source pattern.
- AEX scales and truncates Front/Back Blur Strength and Alpha Fade by
  `render_scale`.
- Current CLI `--strength-scale auto` reads recorded `ctx_render_scale` or
  `ctx_0x11c / ctx_0x120` from the per-case params JSON when present; without
  those fields it falls back to `1.0`. The old `1 / frame_rate` proxy is now
  only available as `--strength-scale frame-rate` because the 2026-06-12
  DirectionalBlur return produced identical `fr24` and `fr30` images.
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

`FUN_180001830(table, length)` builds, per element:

```text
w[i] = expf(-(i*i) / (2*(length/3.0)^2 + 1e-5))
```

Binary-confirmed constants (PE read, image base 0x180000000):
`DAT_18000b1ec` (RVA 0xb1ec) = float 3.0 (the divisor),
`DAT_18000b1e0` (RVA 0xb1e0) = double 1e-5 (additive eps). 2026-06-14 FIX: the
CLI `gaussian_weights` previously used a divisor of 0.5, which made the
denominator ~36x too large and the gaussian far too flat. Corrected to 3.0.
This is the dominant over-accumulation fix; it lowered all 4 returned
software cases (alpha_fade 29.99->27.37, diagonal_ramp 16.33->11.88,
size_var 23.47->21.01, sharp_tail 16.51->14.93) and did not regress the
existing GPU-rendered pairs. Earlier narrow-table probes that "felt" closer
were chasing this same width error empirically.

### Input Rotate

Use `FUN_180001ec0` semantics:

- strict inner-pixel sampling: source sample must satisfy
  `0 < ix < width - 1` and `0 < iy < height - 1`
- integer coordinates use `CVTTSS2SI` truncation, not round-to-nearest
- bilinear alpha sum is written as output alpha
- RGB corner weights are normalized by the sampled alpha sum
- invalid samples are skipped by the helper rather than explicitly written

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
- A post-output shift sweep of the current `rotated-aex-full-choreo` candidate
  across all `dx/dy = -1..1` worsens both tracked cases. The unshifted candidate
  remains best (`case_0001 mean=4.4483`, `case_0005 mean=1.1703`), so a simple
  final crop/output offset error is unlikely.
- `rotated-aex-float-math` uses `FUN_180001ec0`-shaped float angle trig and
  integer half-width/half-height centers. It is neutral on the tracked refs
  (`case_0001 mean=4.4483`, `case_0005 mean=1.1703`), so those rotate-math
  details are not the visible residual source.
- 2026-06-17 local audit: `FUN_180001ec0` invalid samples are no-write, not
  explicit-black writes. Because the CLI's AEX rowdriver path zero-initializes
  the first rotated destination before sampling, the current alpha-weighted
  input rotate already mirrors that behavior. The next unresolved input-side
  IR target is the `LAB_180006980` PF Iterate8 populate callback that writes
  padded `A`, not another first-rotate validity toggle.

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

2026-06-17 direct `/usr/bin/objdump` recheck on `plugins_2025/OLMDirectionalBlur.aex`
confirms the same callback bodies even though the checked-in Ghidra disasm does
not expose them as standalone labeled functions. Treat host populate/output as
closed unless a future bit-depth-specific host validation contradicts it.

2026-06-17 rowdriver/final-normalization closeout: `FUN_180004a20` guards final
RGB normalization with `denom > 0.0`; the CLI was patched from `> 1.0e-8f` to
match. The context-scale smoke metrics did not change, so this is a correctness
cleanup rather than the visible residual source.

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

The historical table below is useful for seeing which hypotheses were tried,
but the current CLI should be read through the 2026-06-22 matrix immediately
after it.

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
| rotated-aex-global-tail-only | 4.4490 | 1.1702 | disabling component tail is neutral/mixed |
| rotated-aex-no-tail | 4.4597 | 1.1702 | disabling all Sharp Tail is neutral/negative |
| rotated-aex-preserve-invalid-input | 4.4483 | 1.1703 | input rotate invalid-pixel preserve is neutral |
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

2026-06-22 current CLI candidate matrix:

- Script: `scripts/analyze_directionalblur_candidate_matrix.py`.
- Quick report: `refs/reports/olmdirectionalblur_candidate_matrix_20260622_010324/candidate_matrix.md`.
- Wide report: `refs/reports/olmdirectionalblur_candidate_matrix_20260622_010433/candidate_matrix.md`.
- Wide profile covers front-only `case_0001..case_0005`.
- `rotated-front-strength` is the best total-mean candidate
  (`18.197798`, max `252`) and `direct` is second (`18.310725`, max `253`),
  but both are measurement scaffolds and not the AEX-confirmed A/B structure.
- AEX choreography variants cluster tightly around total mean `22.12`:
  `rotated-aex-trunc-output` is the best AEX-shaped wide candidate
  (`22.066680`, max `251`), then `rotated-aex-truncated-span`,
  `rotated-aex-choreo`, `rotated-aex-full-choreo`,
  `rotated-aex-pad-full-choreo`, and `rotated-aex-prepass-full-choreo`.
- `case_0001..case_0004` are effectively identical within each candidate
  family (`rotated-front-strength/direct` around mean `3.7669`; AEX
  choreography around `4.9570`). `case_0005` is the only current front-only
  case where the AEX choreography family clearly beats `direct`
  (`~2.2971` vs `3.2430`).
- `rotated-rowdriver-prepass` remains the worst wide candidate
  (`23.501166`, max `255`), so do not promote the rowdriver prepass branch from
  PNG metrics alone.

Interpretation: the remaining front-only residual is not solved by a single
global A/B choreography, padding, output truncation, span truncation, binary
alpha, or prepass toggle. The next evidence should isolate the angle-0
row-driver accumulation / valid-alpha side channel for `case_0001..0004` and
the diagonal rotate path for `case_0005` separately, preferably with typed
runtime witnesses rather than another broad PNG sweep.

2026-06-24 decision matrix:

- `scripts/analyze_directionalblur_decision_matrix.py` combines the wide
  candidate matrix, residual cluster report, and focused 2026-06-24 runtime
  return.
- Latest report:
  `refs/conformance/olmdirectionalblur_8bpc_decision.md`.
- Machine decision: `blocked-await-runtime-or-asm-proof`.
- Best overall candidate is `rotated-front-strength` (`mean_sum=18.197798`,
  `max=252`), but it is a measurement scaffold and not the confirmed A/B
  structure.
- Best AEX-shaped candidate is `rotated-aex-trunc-output`
  (`mean_sum=22.066680`, `max=251`), still far from exact.
- Residual split:
  - `case_0001`: `angle0-rgb-only-rowdriver-or-valid-alpha`, witness
    `(494,169)`, Windows `[164,0,0,255]` vs local `[0,0,0,255]`.
  - `case_0005`: `diagonal-rgb-alpha-rotate-validity`, witness `(507,367)`.
- Latest runtime trace remains `answered_partial` without typed per-pixel
  rowdriver/rotate-path values. Do not change implementation from broad PNG
  matrices until a narrow asm/runtime proof explains these two witness shapes.

## Implementation Rules

- Keep `direct` as a measurement baseline, not production truth.
- Prefer evolving `rotated-aex-choreo` toward the confirmed A/B order.
- Size Variation is normalized as UI integer / 100.0. The divisor is confirmed
  by `DAT_18000b384 = 100.0` in `plugins_2025/OLMDirectionalBlur.aex`, so raw UI
  scaling is not a tuning knob.
- Do not tune `strength_scale` as the main fix unless Windows references record
  the render-context ratio or the diff becomes clearly scale-dominated. The
  latest full-choreography sweep shows it is not currently scale-dominated.
  Targeted Windows request:
  `refs/reference_requests/directionalblur_context_scale_20260606.json`.
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
4. If angle-0 remains around `mean=4`, use
   `refs/reference_requests/directionalblur_context_scale_20260606.json` to get
   Windows render-context scale (`ctx + 0x11c / ctx + 0x120`) and non-opaque
   alpha references before more parameter sweeps. Host populate/output callbacks
   and the component-map run-merging pass now look consistent with the current
   CLI approximation.
5. Only after front-only improves, add Back Blur / Noise IR sections.

## 2026-06-06 Subagent IR Review

Independent read-only review of the current DirectionalBlur notes/code narrowed
the remaining front-only/no-noise work to the following IR checkpoints:

- Keep `render_scale = *(int *)(ctx+0x11c) / *(int *)(ctx+0x120)` separate from
  frame rate. This is now mapped to `PF_InData.downsample_x.num / den`; the
  older `1/frame_rate` mapping was only a PNG-fit hypothesis and has been
  contradicted by the returned `fr24`/`fr30` references.
- Preserve the A/B choreography explicitly:
  populate A -> rotate A to B -> copy B to A -> row-driver writes B/denom ->
  normalize B -> clear A -> rotate B to A -> output through the repointed
  `+0x8090` callback.
- Model `FUN_180001000` as a prepass that writes `denom`, `alpha_or_valid`, and
  the B seed together.
- Treat `FUN_1800013e0` as the next address-level blocker: source RGB appears
  to come from A, contribution alpha from `alpha_or_valid`, RGB denominator is
  separate, and output alpha is max-like, but this needs one more objdump pass.
- Follow-up argument audit confirms that mapping: `FUN_1800038d0` passes
  A/source as `param_4`, B/destination as `param_5`, denom as `param_6`, and
  `alpha_or_valid` as `param_7`; `FUN_1800013e0` adds RGB/denom and updates
  B alpha by max contribution.
- The current references are opaque, so straight-vs-premultiplied source RGB
  cannot be conclusively separated. If `case_0001` remains around `mean=4`
  after the argument mapping pass, stop further image-only toggles and use
  `refs/reference_requests/directionalblur_context_scale_20260606.json`.

### 2026-06-06 stop condition review

Subagent review of the current DirectionalBlur probes found that the remaining
front-only/no-noise image-only hypotheses are mostly covered:

- A/B choreography, pad/offset, prepass, exact scatter/rowdriver, component
  half-height/center/tail, binary alpha, straight RGB, trunc output, truncated
  span, row init, scale sweep, and sign checks have existing smoke/probe notes.
- Most variants are neutral or negative, and the current tracked references are
  opaque, so source RGB/premul/alpha ownership cannot be separated further.
- Re-running `rotated-aex-full-choreo` or `rotated-aex-exact-rowdriver` is useful
  as a regression check, but it is unlikely to add new algorithmic information.

Stop condition: do not keep fitting DirectionalBlur with PNG-only parameter
sweeps while `case_0001` remains around `mean=4`. The returned
`refs/reference_requests/directionalblur_context_scale_20260606.json` evidence
maps `ctx+0x11c / ctx+0x120` to `PF_InData.downsample_x.num / den`; use the
non-opaque alpha
references.

### 2026-06-06 parallel audit refresh

Sub-agent Tesla reran the DirectionalBlur read-only audit and confirmed that the
current red residual is stable rather than a rowdriver integration issue:

- `smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py` remains around
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- `smoke_olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_cli.py` shows
  `rotated-aex-exact-rowdriver` exactly matching `exact-scatter-helper`
  (`case_0001 mean=4.4392`, `case_0005 mean=1.1761`).
- Span truncation and output truncation probes are only minor/mixed deltas.

Parent action: pause DirectionalBlur implementation tuning until
`directionalblur_context_scale_20260606.json` is rendered/imported. The imported
refs confirmed the frame-rate proxy is wrong and support the
`PF_InData.downsample_x.num / den` mapping. The next DirectionalBlur work should
use the non-opaque alpha cases to verify source RGB ownership, `FUN_180001000`,
and `alpha_or_valid`, not scalar PNG tuning.

2026-06-21 Mac-side recheck while Smoother2 is paused:

- `smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py` is still
  expected-red on the opaque legacy pair:
  `case_0001 max=164 mean=4.9570`,
  `case_0005 max=251 mean=2.2971`.
- `smoke_olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_cli.py` keeps the
  same shape. `rotated-aex-exact-scatter-helper` and
  `rotated-aex-exact-rowdriver` both give
  `case_0001 max=164 mean=4.9910`,
  `case_0005 max=251 mean=2.2670`.
- `smoke_olmdirectionalblur_cpp_rotated_rowdriver_prepass_cli.py` is worse on
  the same pair:
  `rotated-rowdriver-prepass case_0001 max=255 mean=5.2605`,
  `case_0005 max=254 mean=2.4591`; the init variant is essentially identical.

Interpretation: current rowdriver/prepass candidates remain diagnostic only.
The useful next evidence is still exact runtime/asm proof of the sampler and
final normalization/validity pass on the non-opaque alpha cases, not another
PNG-only switch sweep.

2026-06-21 runtime trace comparison guard:

- `scripts/compare_directionalblur_trace.py` now classifies
  `olmdirectionalblur_dense_sampler_trace_20260620` returns and treats
  placeholder text (`not traced`, `not isolated`, `see included IR`, etc.) as
  non-evidence.
- The dense-all 2026-06-20 return classifies as
  `trace-structure-present-values-missing`: it contains the requested case /
  witness schema but no typed sampler, accumulation, pre-writeback, or final
  byte values.
- The dense-live follow-up classifies as `trace-failed-before-module-load`: AE
  hit a WINHTTP access violation before the OLMDirectionalBlur module resolved.
- Therefore these returns do not justify tuning sampler order, accumulation, or
  writeback. Keep DirectionalBlur parked until a typed runtime witness or new
  asm proof arrives.

2026-06-21 reference-set audit:

- `scripts/audit_directionalblur_reference_sets.py` classifies known
  DirectionalBlur reference folders by filename prefix and SHA-256.
- The 20260604 legacy set contains 9 DirectionalBlur PNGs.
- The 20260611 context-scale return contains 30 DirectionalBlur PNGs.
- The 20260619 bulk folder
  `refs/win_references/olm_windows_bulk_png_refs_20260619_014632_all_existing_requests_windows_result_20260619_0210/OLMDirectionalBlur`
  is mixed: 76 PNGs total, only 16 are DirectionalBlur. The remaining 60 are
  KiraKira (13), ColorKey (17), RadialBlur (18), and Smoother2 (12).
- No same-name hash conflicts were found among DirectionalBlur files, but the
  bulk parent folder name is not reliable. Future scripts must classify by
  request filename/manifest rather than parent directory.

## 2026-06-13 non-opaque alpha return audit

Discriminating returned cases from
`directionalblur_context_scale_20260606`:

- `db_angle0_alpha_fade_hard_edges`
- `db_diagonal_alpha_ramp`
- `db_size_variation_component`
- `db_sharp_tail_component`

On those cases, `rotated-aex-exact-rowdriver` remains the best baseline among
the existing large switches:

| algorithm | mean avg | alpha fade | diagonal ramp | size variation | sharp tail |
| --- | ---: | ---: | ---: | ---: | ---: |
| rotated-aex-exact-rowdriver | 22.2983 | 29.9884 | 16.3346 | 23.4683 | 16.5056 |
| rotated-aex-straight-source-rgb | 35.4938 | 31.2920 | 60.3349 | 23.5879 | 18.0268 |
| rotated-aex-binary-alpha | 36.7963 | 31.0441 | 65.2806 | 23.4699 | 17.9851 |
| rotated-aex-rotateback-denom-alpha | 31.6693 | 31.4367 | 46.6301 | 23.7265 | 18.0982 |
| rotated-aex-row-init-zero | 22.9762 | 31.2118 | 16.6175 | 23.5661 | 18.0422 |
| rotated-aex-trunc-output | 22.9332 | 31.0731 | 16.8498 | 23.4053 | 17.8760 |
| rotated-aex-truncated-span | 22.8996 | 31.1853 | 16.5228 | 23.4683 | 17.9442 |

Additional focused rotate-sampler probes keep the exact rowdriver and only
toggle alpha-weighted bilinear sampling during input/output rotate:

| algorithm | mean avg | alpha fade | diagonal ramp | size variation | sharp tail |
| --- | ---: | ---: | ---: | ---: | ---: |
| rotated-aex-exact-rowdriver-plain-input | 22.3134 | 29.9884 | 16.3874 | 23.4683 | 16.5056 |
| rotated-aex-exact-rowdriver-plain-output | 22.2984 | 29.9884 | 16.3349 | 23.4683 | 16.5056 |
| rotated-aex-exact-rowdriver-plain-rotate | 22.3135 | 29.9884 | 16.3876 | 23.4683 | 16.5056 |

Implications:

- Do not promote straight source RGB, binary alpha, rotate-back denom alpha, or
  plain rotate sampling. They are neutral or negative on the returned
  non-opaque cases.
- `FUN_180001000` loop bounds match the decomp shape (`i < scaled_span`), so
  simple inclusive-span tuning is not the next best target.
- The remaining diagonal-ramp signed error has candidate RGB too dark and alpha
  too high, which points back to exact `FUN_1800013e0` denominator/RGB
  normalization or the pre-rotate-back B alpha/RGB relationship rather than
  frame rate, downsample scale, or bilinear alpha-weighting.

## 2026-06-14 Front Alpha Fade is a per-column taper, not a gather window

Measured (not inferred) signed error on `db_diagonal_alpha_ramp` corrects the
prior note: the candidate is too BRIGHT and alpha too HIGH (over-accumulating),
uniform across the full frame, no spread/edge error. See
`OLMDirectionalBlur_ASM_FACTS.md` 2026-06-14 entry for the per-channel numbers.

The asm-grounded cause is how Front Alpha Fade is modeled. In the scatter
caller (`@180003ac1` region, the two `FUN_1800013e0` calls at the back/front
tables `param_7+0x58` / `param_7+0x4068`):

```
fVar10 = max(0, fVar3 - |col - X| * fade_rate(+0x40 / +0x44) / Y(+0xc))
param_11 = fVar10 * fVar11          // per-column taper * gate
FUN_1800013e0(..., front_table, front_strength(+0x48), width, param_11)
```

Inside `FUN_1800013e0`, `param_11` does two things:
- `param_9 = (int)(param_9 * param_11)` -> shortens the effective scatter span
- `fVar17 = DAT_18000b1e8 / param_11` -> steepens the weight-index stride

So Front Alpha Fade is a **per-column linear taper of scatter strength**: it
both shrinks the span and accelerates weight falloff, which reduces total
accumulated alpha/RGB toward the faded columns.

The current CLI (`render_rotated`) instead models Front Alpha Fade as a
**box-average of alpha over a `front_alpha_fade * scale` gather window**
(`use_alpha_fade_gather` -> `front_gather`, applied in the `gather_first` smooth
loop at ~main.cpp:1018 and the `rowdriver_prepass` at ~main.cpp:1057). A box
average smooths but does not reduce total contribution, so it leaves alpha (and
premultiplied RGB) too high on a faded ramp. This is the structural mismatch,
not `FUN_1800013e0` denom-vs-max normalization (max and denom coexist in the
real buffer: `param_5` ch0-2 = sum(fVar16*rgb), ch3 = max(fVar16); `param_6` =
sum(fVar16)).

Next implementation step: add a probe that applies Front Alpha Fade as a
per-column/per-step linear taper on the scatter `coeff` (mirroring `fVar10`)
instead of a gather-window average, and re-measure the 4 returned cases via
`run_reference_test.py`. Keep the gather-window path for comparison until the
taper is shown to win on the mean without regressing the hard-edge case.

RETRACTED 2026-06-14 (live Ghidra param checkout `FUN_180006c50`): the above
"Front Alpha Fade = per-column taper" conclusion is WRONG. Param checkout shows
Front Alpha Fade = `+0x4c` = the gather count (the prepass `FUN_180001000`,
already modeled by the CLI `rowdriver_prepass`), while the per-column taper at
`+0x40` is Front Sharp Tail (`/100`). For `db_diagonal_alpha_ramp` (Sharp Tail
0, Size Var 0) the taper is inactive (guard fills alpha=1.0), so the taper is
not the cause. `FUN_180001000` matches the CLI prepass structurally. The
measured over-accumulation now points at the final two-stage RGB-denominator
normalization / validity pass in `FUN_180004a20` (`param_6[0x1010]`,
`FUN_180001ec0`, `param_6[0x1023]`), not the scatter taper. See the corrected
mapping in `OLMDirectionalBlur_ASM_FACTS.md` 2026-06-14 param-struct entry.

## 2026-06-22 Residual Cluster Witnesses for Focused Runtime Trace

Script: `scripts/analyze_directionalblur_residual_clusters.py`.

Report:
`refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/residual_clusters.md`.

Candidate under test: `rotated-aex-full-choreo`.

The broad candidate matrix is no longer a good tuning surface by itself: the
best total-mean rows (`direct`, `rotated-front-strength`) are useful measuring
scaffolds but not AEX-shaped, while the AEX choreography family stays clustered
around the same residual band. The residual audit therefore narrows the next
runtime request to two concrete, high-signal pixels:

| Case | Witness | Windows ref | Local candidate | Local interpretation |
| --- | --- | --- | --- | --- |
| `case_0001` angle-0/front-only | `(494,169)` | `[164,0,0,255]` | `[0,0,0,255]` | `angle0-rgb-only-rowdriver-or-valid-alpha`; alpha matches exactly |
| `case_0005` diagonal rotate-path | `(507,367)` | `[1,0,0,255]` | `[252,0,0,255]` | `diagonal-rgb-alpha-rotate-validity`; RGB inversion with smaller alpha residual |

Cluster facts:

- `case_0001`: classified as `angle0-rgb-only-rowdriver-or-valid-alpha`.
  Max `164`, mean `4.956984954`, one dominant component of `147593` pixels
  over bbox `[380,0,959,369]`; all diff pixels are RGB-only, alpha diff is
  exactly zero, and signed R has both positive and negative regions
  (`min=-164`, `max=102`). This is not byte writeback noise. It likely sits
  before final writeback: rowdriver/group membership, validity/alpha
  side-channel, or RGB normalization.
- `case_0005`: classified as `diagonal-rgb-alpha-rotate-validity`. Max `251`,
  mean `2.297067901`, many small components plus one broad border-touching
  component; RGB differs on `79003` pixels, alpha differs on `11205` pixels,
  signed R reaches `-250..+251`, and alpha has smaller `-55..+56` residuals.
  This should be traced as a separate diagonal rotate sampler / validity /
  group-size witness, not inferred from the angle-0 case.

Packaged focused Windows request:
`refs/runtime_trace_packages/olm_runtime_trace_directionalblur_residual_witness_20260622_022500.zip`.

The request asks Windows to return parameter normalization, output-to-A/B buffer
coordinates, rowdriver/group membership, rotate sampler source order, validity
or alpha side-channel values, accumulation numerator/denominator, pre-writeback
floats/hex, and final stored RGBA for the two witnesses above.

Return intake/classification command:

```
python3 scripts/compare_directionalblur_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary.json \
  --output-json refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness.json \
  --output-md refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness.md
```

The comparator prefers the focused request
`olmdirectionalblur_angle0_diagonal_residual_witness_20260622` when present and
returns a paired focus string:

- `angle0:rowdriver-or-group-membership`: update the rowdriver/group IR before
  changing sampler math.
- `angle0:valid-alpha-side-channel`: verify the hidden validity/alpha side
  channel used by the final pass.
- `angle0:normalization-or-accumulation`: inspect numerator/denominator and
  final normalization before pixel fitting.
- `diagonal:rotate-sampler`: update rotate source-coordinate order and border
  behavior first.
- `diagonal:border-or-validity`: ground the valid/out-of-frame branch before
  touching weights.
- `diagonal:group-size-or-opacity`: check group-size/opacity gating on the
  diagonal path.
- `writeback-or-prewriteback` on either side means the trace reached final
  values but not the earlier cause; compare pre-writeback floats against local
  logs before changing writeback.
- `trace-structure-present-values-missing` means the returned shape is useful
  only for request debugging, not implementation tuning.
- The comparison JSON/Markdown also emits `recommended_next_evidence`. Use it
  as the stop/go note for the next Mac-side implementation step: angle-0 needs
  rowdriver/group or validity-side-channel proof, while diagonal needs rotate
  sampler/border/validity proof.

Stop line: do not promote another DirectionalBlur implementation toggle from
PNG mean improvements until one of these witnesses is explained by asm/runtime
values.
