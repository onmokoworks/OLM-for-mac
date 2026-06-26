# Binary-Grounded IR: OLMBlur

## Feature

- Plug-in: OLM Blur
- Feature/path: alpha-masked repeated blur, legacy and non-legacy paths
- Bit depth: 8bpc AE exact against normalized Software refs; 16bpc Mac AE
  validation is classified but not exact; 32bpc still needs references
- Reference set:
  - `refs/win_references/20260604_olm/OLMBlur`
  - normalized Software refs under
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur`
- Current status:
  - packaged 8bpc Mac AE return is exact for `case_0001..0007`
  - AE-free CLI remains exact for normalized Software `case_0001/0002/0004/0005`
  - AE-free CLI keeps useful `max=1` residual witnesses for
    `case_0003/0006/0007`
  - 16bpc Mac AE validation is 0/7 exact, but 6/7 residuals are now classified
    as one 512-step 16-bit writeback/PNG-scaling quantization after wraparound,
    not broad blur-kernel failure
  - `case_0007` has the same 16bpc quantization signature plus a remaining
    Legacy border/seed anomaly
  - not binary-complete for 16bpc writeback scaling, Legacy border seed, or
    32bpc behavior
- 2026-06-22 provenance audit confirms the packaged AE-host candidates are
  exact against the 20260618 normalized refs for all seven cases; the large
  differences in `case_0001..0004` are only against the older 20260604
  reference generation.
- Cross-feature canonicalization audit:
  `refs/reports/software_reference_canonicalization_8bpc.md` now verifies the
  same normalized-reference decision alongside OLMColorKey and
  OLMDistanceGradation. OLMBlur is `normalized-software-exact` for 7/7 cases;
  only the older 20260604 generation drifts on `case_0001..0004`.
- 2026-06-24 decision matrix:
  `refs/reports/olmblur_decision_matrix_20260624/decision_matrix.md`
  consolidates the current rule as `preserve-normalized-ae-exact`: normalized
  8bpc is 7/7 exact, old-reference drift is limited to 4 cases, and the
  remaining AE-free CLI `max=1` witnesses are diagnostic. Do not change the
  passing AE behavior from these residuals; only continue them as
  binary-grounding work for accumulation/helper or Legacy border/all-same
  state.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| OLM Blur applies blur to pixels with `alpha > 0`. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMBlur__OLMBlur__doc__OLMBlurUserManualEN.txt`. | manual-backed |
| Color Key workflow makes boundary-only blur by creating the alpha/matte region first. | Official manual and product page. | manual-backed |
| Non-legacy path uses repeated Gaussian-like separable passes with decaying radius. | `cli/OLMBlur/main.cpp`, `mac/OLMBlur/OLMBlur.cpp`, and current normalized refs. | binary-grounded / CLI-confirmed |
| Non-legacy radius path uses `pow(double,double)` then float sigma. | `notes/CONFORMANCE_LEDGER.md` and current CLI implementation. | binary-grounded / CLI-confirmed |
| Legacy writeback currently uses `floor(x + 0.5)`. | Binary `.rdata` constant `0.5`, decomp/port notes. | binary-grounded |
| Non-legacy writeback currently uses a compatibility `nearbyint` shim. | Current CLI/Mac implementation; exact for normalized `case_0001..0005`. | CLI-confirmed but not final binary explanation |
| 16bpc standard writer adds `0.5`, passes through the clamp/helper, truncates with `CVTTSS2SI`, then stores 16-bit channel words. | `disasm/OLMBlur.aex.asm.txt` around `180002fad..18000302e`: `MOVSS` loads `0.5`, `ADDSS`, helper call, `CVTTSS2SI`, `MOV word ptr [RBX+...]`. | binary-grounded |
| Legacy/alternate 16bpc writer uses a later direct `CVTTSS2SI` word-store family. | `disasm/OLMBlur.aex.asm.txt` around `1800031f9..`; matches the earlier runtime-trace location family for Legacy `case_0007`. | binary-grounded / runtime-trace |
| Current Mac AE 16bpc OLMBlur residuals are mostly a 512-step writeback/PNG scaling signature. | `refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_distancegradation_inside_no_source.md`: six cases labeled `olmblur-16bpc-writeback-quantization`; all nonzero cyclic deltas are `<=512`. | AE-validation diagnostic |
| 2026-06-26 local Mac AE rerun reproduces the same pattern with tighter delta families: non-Legacy cases use only `-513/-512/+512/+513` on failing channels, while Legacy `case_0007` adds a separate `32513` cyclic border/seed anomaly. | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_204952_rerun/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` and `refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_204952_rerun.md`. | AE-validation diagnostic |
| Non-legacy `case_0006` residual is already present before byte writeback. | 2026-06-20 Windows CDB return: `(498,940)` pre-writeback red is `185.49998474121094` while the Mac CLI baseline is exactly `185.5`; final Windows byte is `185`. | runtime-trace |
| Legacy `case_0007` uses the later `OLMBlur+0x7FDF` writeback family. | 2026-06-20 Windows CDB return hit `(0,0)`, `(488,941)`, and `(488,942)` at the Legacy writeback family. | runtime-trace |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `Blur Amount` | Base radius/extent. | Scaled by comp/image width in the CLI/mac path. | current implementation |
| `Blur Smoothness` | Legacy sigma multiplier; non-legacy smoothness participates in radius/weights through current port logic. | Clamp/scale follows current C++ port. | current implementation |
| `Number of Repeat` | Number of repeated separable blur iterations. | Minimum 1 in CLI parsing. | current implementation |
| `Bias Direction` | Pass order. | Vertical: horizontal then vertical; Horizontal: vertical then horizontal. | current implementation |
| `Legacy` | Selects legacy kernel/iteration path. | Boolean. | current implementation |

## Kernel / Loop Shape

### Shared Setup

1. Load RGB as floats.
2. Load alpha mask as `1` when source alpha is nonzero, else `0`.
3. Allocate two RGB buffers and two alpha masks.
4. Apply separable blur passes according to Legacy and Bias Direction.
5. Store output RGB; output alpha behavior follows the current port path.

### Non-Legacy Path

Current implementation:

1. Compute `decay = pow(3.0 / blur_amount, 1.0 / (repeat - 1))` when
   `repeat > 1`.
2. For `iter = 0..repeat-1`:
   - `radius_d = blur_amount * pow(decay, iter)` using double pow.
   - `radius = (long)radius_d`.
   - stop when radius is zero.
   - `sigma = float(radius_d) / 3.0`.
   - build symmetric weights `exp(-(k*k) / (2*sigma*sigma))`.
   - run two 1D passes in the order selected by `Bias Direction`.

### Legacy Path

Current implementation:

1. `radius = (long)blur_amount`.
2. `sigma_base = ((blur_amount * smoothness) / 100.0) * (blur_amount / 3.0)`.
3. For `iter = 1..repeat`:
   - `sigma = sigma_base / iter`.
   - build symmetric weights.
   - run two legacy 1D passes in the order selected by `Bias Direction`.

## Sampling / Boundary

- Non-legacy pass clamps sample span to available pixels on each side.
- Legacy path has a remaining border/all-same ambiguity. Current negative
  probes show that including border coordinate `0` worsens `case_0007`, so keep
  the current border exclusion unless runtime trace contradicts it.
- 2026-06-20 runtime trace did not isolate the Legacy `all_same` state or direct
  border inclusion rule. It did prove that the residual pixels differ before
  byte output, so broad writeback-only fixes are not justified.
- Alpha mask participates in the blur helper; exact per-pass alpha ownership is
  part of the remaining proof for residual cases.

## Channel / Writeback Rules

- RGB is blurred; alpha is used as a mask/validity channel.
- Legacy writeback: `floor(value + 0.5)`.
- Non-legacy current compatibility writeback: `nearbyint`.
- The non-legacy `nearbyint` rule is not final binary-grounded truth because
  the Windows AEX writeback constant is still known to be `0.5`; the remaining
  mismatch likely belongs in accumulation/order before writeback.
- 16bpc validation should not be treated as a kernel-tuning signal yet. The
  Mac AE residuals for `case_0001..0006` collapse to a one-step 512 cyclic
  delta in 16-bit PNG space, including wraparound examples such as reference
  values near `65535` versus candidates near `0`. Next proof belongs in the
  16bpc AE writeback/PNG scaling path.
- The 2026-06-26 local rerun makes that more specific: the non-Legacy failing
  channels only show `-513/-512/+512/+513`, and `case_0003/0004` collapse
  further to pure `+/-512`. That is strong evidence for an export/writeback
  quantization family rather than a blur-kernel or radius-order failure.
- 16bpc `case_0007` still needs Legacy-specific proof: it has the same
  quantization signature, plus a larger cyclic delta at a small border/seed
  set. Do not change the general blur kernel from this case alone.

## Conformance Cases

| Case | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| `case_0001/0002/0004` | 8bpc | `CLI exact` in current smoke | 2026-06-21 rerun: exact (`max=0`); packaged Mac AE validation is exact | Preserve AE behavior; only revisit true binary-grounded writeback if CLI residual closure becomes necessary |
| `case_0003` | 8bpc | AE exact / guarded CLI residual | 2026-06-21 rerun: CLI `max=1 mean=0.0052`; 2026-06-19 AE pixel return `max=0` | Treat as host-path exact but keep runtime/writeback proof open |
| `case_0005` | 8bpc | `CLI exact` in current residual smoke | 2026-06-21 rerun: exact (`max=0`); packaged Mac AE validation is exact | Preserve AE behavior; add 16/32bpc references |
| `case_0006` | 8bpc | AE exact / residual diagnostic | 2026-06-20 Windows trace: AEX pre-writeback red at `(498,940)` is `185.49998474121094` (`0x1.72fffe0000000p+7`), Mac CLI baseline is exactly `185.5` (`0x1.73p+7`), and Windows final byte is `185`; 2026-06-19 AE pixel return `max=0` | Accumulation/helper order proof before changing the passing AE plug-in path |
| `case_0007` | 8bpc | AE exact / residual diagnostic | 2026-06-20 Windows trace: Legacy writeback family `OLMBlur+0x7FDF`; `(0,0)` pre RGB `[0,0,~1.5528]`, final `[0,0,0,255]`; `(488,941/942)` pre red just above `250.5`, final `251`; Mac CLI stays just below/equal | Isolate Legacy helper state/border source if CLI residual is still worth closing |
| `case_0001..0006` | 16bpc | not exact / writeback diagnostic | 2026-06-26 Mac AE validation and local rerun: all six failing cases are limited to `-513/-512/+512/+513` cyclic deltas, with `case_0003/0004` using only `+/-512`; the large `max=65023` rows are wraparound one-step differences rather than broad kernel mismatch | Inspect 16bpc writeback scaling and AE PNG export normalization before changing blur math |
| `case_0007` | 16bpc | not exact / Legacy diagnostic | 2026-06-26 Mac AE validation and local rerun: one 512-step quantization signature plus a separate `32513` cyclic Legacy border/seed anomaly (`olmblur-16bpc-legacy-border-plus-quantization`) | Isolate Legacy 16bpc border/seed and alternate writer family |

Mac baseline traces for the normalized Software residual witnesses are stored
under `refs/reports/olmblur_trace_baseline_20260619_030633_mac/`. These logs
should be compared with Windows AEX runtime values before changing writeback or
Legacy border rules.

2026-06-20 Windows overnight return:

- Bundle: `handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`
- Blur trace package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_20260620_overnight.zip`
- Imported comparison:
  `refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold_20260620/olmblur_repeat_threshold.md`
- Conclusion: the return is enough to reject a pure output-rounding diagnosis
  for `case_0006/0007`. It is not enough to rewrite Legacy border/all_same
  behavior, and the packaged Mac AE slices are already exact, so no production
  OLMBlur change should be made from this trace alone.
- The trace comparison helper now treats placeholders such as `0x...`,
  `not isolated`, `unknown`, and selector strings like
  `floorf(value + 0.5) | cvt/trunc | other` as non-evidence. Real hex-float
  values such as `0x1.72fffe0000000p+7`, numeric final bytes, and booleans
  still count. This keeps sparse returns at
  `trace-structure-present-values-missing` while preserving the existing
  2026-06-20 runtime focus classifications.

2026-06-21 Mac-side rerun:

- `smoke_olmblur_cli.py` still passes: `case_0001/0002/0004` exact,
  `case_0005` exact, residual witnesses `case_0003 max=1 mean=0.0052`,
  `case_0006 max=1 mean=0.0000`, and `case_0007 max=1 mean=0.0000`.
- `smoke_compare_olmblur_trace.py` still passes and classifies the next focus
  as `nonlegacy-accumulation-or-writeback`.
- No code change was made: the runtime trace already proves `case_0006` differs
  before byte output, so changing a writeback rounding rule would be
  under-grounded and could break the AE-exact packaged plug-in slice.

2026-06-22 reference provenance audit:

- `scripts/analyze_olmblur_reference_provenance.py` compares the 2026-06-19
  AE-host candidates against the older 20260604 refs and the 20260618
  normalized Software refs.
- `scripts/analyze_soft_reference_canonicalization.py` includes the same
  OLMBlur check in the cross-feature 8bpc Software audit:
  `refs/reports/software_reference_canonicalization_8bpc.md`.
- Latest report:
  `refs/reports/olmblur_reference_provenance_20260622_025614/audit.md`.
- Machine classification:
  `normalized-software-exact-with-legacy-drift`.
- All seven candidates are exact against the normalized refs.
- Old-reference drift is limited to non-legacy `case_0001..0004`:
  - `case_0001`: old-ref `max=59 mean=1.287920525`
  - `case_0002`: old-ref `max=59 mean=1.287920525`
  - `case_0003`: old-ref `max=14 mean=1.727592593`
  - `case_0004`: old-ref `max=58 mean=1.268115355`
- `case_0005..0007` are exact against both old and normalized refs.
- Interpretation: do not tune the plug-in toward the older non-legacy
  `case_0001..0004` PNGs. The remaining `max=1` CLI witnesses are useful for
  binary-grounding accumulation/writeback, but they are not current 8bpc AE
  failures.

2026-06-24 decision matrix:

- `scripts/analyze_olmblur_decision_matrix.py` combines the provenance audit,
  cross-feature canonicalization, and repeat-threshold runtime trace.
- Latest report:
  `refs/reports/olmblur_decision_matrix_20260624/decision_matrix.md`.
- Machine decision: `preserve-normalized-ae-exact`.
- Normalized 8bpc: 7/7 exact.
- Legacy drift: 4 old-reference cases (`case_0001..0004`).
- CLI residuals: `diagnostic-max1`, with 4 nonzero pixels across
  `case_0006/0007`.
- Runtime classification: `prewriteback-or-helper-state`; `case_0006` differs
  before byte output (`0x1.72fffe...` vs `0x1.73p+7`), and `case_0007` is in
  the Legacy `OLMBlur+0x7FDF` writer family with border/all-same still
  unisolated.
- Action: preserve the passing normalized 8bpc AE behavior. Do not change
  writeback rounding or Legacy borders from these witnesses unless a later
  binary proof isolates the helper state and proves the AE path is wrong.

## Open Questions

- True non-legacy final accumulation/writeback order.
- Legacy border/all-same state for the remaining three pixels.
- 16bpc writeback/PNG scaling rule, including why most residuals differ by a
  single 512 step in PNG space.
- Legacy 16bpc border/seed state for `case_0007`.
- 32bpc Software reference behavior.
- Whether closing the AE-free CLI max=1 diagnostic is worth another narrow
  helper/border trace after 16bpc is checked.
