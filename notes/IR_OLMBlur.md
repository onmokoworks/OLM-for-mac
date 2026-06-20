# Binary-Grounded IR: OLMBlur

## Feature

- Plug-in: OLM Blur
- Feature/path: 8bpc alpha-masked repeated blur, legacy and non-legacy paths
- Bit depth: 8bpc documented here; 16/32bpc still need references
- Reference set:
  - `refs/win_references/20260604_olm/OLMBlur`
  - normalized Software refs under
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur`
- Current status:
  - packaged 8bpc Mac AE return is exact for `case_0001..0007`
  - AE-free CLI remains exact for normalized Software `case_0001/0002/0004/0005`
  - AE-free CLI keeps useful `max=1` residual witnesses for
    `case_0003/0006/0007`
  - not binary-complete for 16/32bpc or writeback proof

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| OLM Blur applies blur to pixels with `alpha > 0`. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMBlur__OLMBlur__doc__OLMBlurUserManualEN.txt`. | manual-backed |
| Color Key workflow makes boundary-only blur by creating the alpha/matte region first. | Official manual and product page. | manual-backed |
| Non-legacy path uses repeated Gaussian-like separable passes with decaying radius. | `cli/OLMBlur/main.cpp`, `mac/OLMBlur/OLMBlur.cpp`, and current normalized refs. | binary-grounded / CLI-confirmed |
| Non-legacy radius path uses `pow(double,double)` then float sigma. | `notes/CONFORMANCE_LEDGER.md` and current CLI implementation. | binary-grounded / CLI-confirmed |
| Legacy writeback currently uses `floor(x + 0.5)`. | Binary `.rdata` constant `0.5`, decomp/port notes. | binary-grounded |
| Non-legacy writeback currently uses a compatibility `nearbyint` shim. | Current CLI/Mac implementation; exact for normalized `case_0001..0005`. | CLI-confirmed but not final binary explanation |
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

## Conformance Cases

| Case | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| `case_0001/0002/0004` | 8bpc | `CLI exact` in current smoke | 2026-06-19 rerun: exact (`max=0`) | Mac AE exact validation and true binary-grounded writeback explanation |
| `case_0003` | 8bpc | AE exact / guarded CLI residual | 2026-06-20 rerun: CLI `max=1 mean=0.0052`; 2026-06-19 AE pixel return `max=0` | Treat as host-path exact but keep runtime/writeback proof open |
| `case_0005` | 8bpc | `CLI exact` in current residual smoke | 2026-06-19 rerun: exact (`max=0`) | Mac AE exact validation |
| `case_0006` | 8bpc | AE exact / residual diagnostic | 2026-06-20 Windows trace: AEX pre-writeback red at `(498,940)` is `185.49998474121094` (`0x1.72fffe0000000p+7`), Mac CLI baseline is exactly `185.5` (`0x1.73p+7`), and Windows final byte is `185`; 2026-06-19 AE pixel return `max=0` | Accumulation/helper order proof before changing the passing AE plug-in path |
| `case_0007` | 8bpc | AE exact / residual diagnostic | 2026-06-20 Windows trace: Legacy writeback family `OLMBlur+0x7FDF`; `(0,0)` pre RGB `[0,0,~1.5528]`, final `[0,0,0,255]`; `(488,941/942)` pre red just above `250.5`, final `251`; Mac CLI stays just below/equal | Isolate Legacy helper state/border source if CLI residual is still worth closing |

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

## Open Questions

- True non-legacy final accumulation/writeback order.
- Legacy border/all-same state for the remaining three pixels.
- Mac AE exactness against normalized/current Windows Software refs.
- 16bpc and 32bpc writeback/rounding behavior.
