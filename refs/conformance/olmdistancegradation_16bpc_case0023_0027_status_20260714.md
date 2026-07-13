# OLMDistanceGradation 16bpc case_0023..0027 status snapshot

Date: 2026-07-14

Scope: existing `refs/conformance`, `notes/CONFORMANCE_LEDGER.md`, local source,
and the latest retained Windows returns only. No code changes. No PNG-only
tuning.

## FACT

### Authority currently in force

- The ledger points current 16bpc status at:
  - `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`
  - `refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md`
  - `refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md`
  - `refs/conformance/windows_runtime_returns_fail_closed_20260713.md`
  See [notes/CONFORMANCE_LEDGER.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/CONFORMANCE_LEDGER.md:607),
  [notes/CONFORMANCE_LEDGER.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/CONFORMANCE_LEDGER.md:614),
  [notes/CONFORMANCE_LEDGER.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/CONFORMANCE_LEDGER.md:230),
  and [notes/CONFORMANCE_LEDGER.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/CONFORMANCE_LEDGER.md:1576).

### Local source fact relevant to this slice

- The installed/current source uses a depth-gated source-mask rule:
  - 8bpc: `alpha > 0`
  - 16bpc and deeper: `alpha > 1.5f / 255.0f`
- The source comment explicitly says this closes `case_0023`.
  See [OLMDistanceGradation.cpp](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMDistanceGradation/OLMDistanceGradation.cpp:378).

### case_0023

- `case_0023` is in the current exact-control set, not in an unresolved family.
  See [olmdistancegradation_16bpc_residual_family_classifier_20260712.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md:5).
- Mac AE bg_on and bg_off probe runs both match the corresponding Windows
  Software references exactly: `nonzero_px=0`, `max_diff=0`.
  See [olmdistancegradation_case0023_alpha_threshold_mac_ae_result_20260707.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_case0023_alpha_threshold_mac_ae_result_20260707.md:7)
  and [olmdistancegradation_opencv_pf16_boundary_20260711.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md:72).

### case_0024..0027

- `case_0024..0027` are currently classified together as the unresolved
  `max-2` family: `broad-field-export-residual-max-2`.
  See [olmdistancegradation_16bpc_residual_family_classifier_20260712.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md:12).
- Current canonical 16bpc measured rows:
  - `case_0024`: `max=2`, `nonzero=991667`
  - `case_0025`: `max=2`, `nonzero=808516`
  - `case_0026`: `max=2`, `nonzero=819532`
  - `case_0027`: `max=2`, `nonzero=505602`
  See [olmdistancegradation_opencv_pf16_boundary_20260711.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md:76)
  and [olmdistancegradation_16bpc_residual_family_classifier_20260712.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md:67).
- The older 2026-07-08 `max=1` near-miss report is retained as historical
  byte-view triage, but the classifier explicitly says not to promote that over
  canonical true16 status.
  See [olmdistancegradation_16bpc_residual_family_classifier_20260712.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md:58).

### Per-case Windows/live-evidence status inside `case_0024..0027`

- `case_0024`: no located return/trace point with both live source and field raw
  words.
- `case_0025`: same; no located live point.
- `case_0026`: 4 coordinate-bound source worlds are located, but `0/4` are exact
  replayable because field raw words and `[RCX+2]` are still missing.
- `case_0027`: no located return/trace point with both live source and field raw
  words.
See [olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md:13).

### Latest Windows return status

- The latest retained Windows return for `OLMDistanceGradation case 0026 live
  field/source` is `exact_bind_failure`, failure boundary `typed_capture`, with
  zero typed records and no same-run identity.
  It is not promoted to algorithm proof.
  See [windows_runtime_returns_fail_closed_20260713.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/windows_runtime_returns_fail_closed_20260713.md:16).

## INFERENCE

- The current status split is:
  - `case_0023`: closed / exact-control
  - `case_0024..0027`: still open, but no longer treated as four unrelated
    failures
- Among `case_0024..0027`, `case_0026` is the strongest live-evidence anchor,
  because it is the only case with any coordinate-bound source/store facts from
  retained returns.
- The current evidence basis for `case_0024..0027` is mostly:
  - canonical true16 diff rows,
  - binary-grounded field/compose boundary knowledge,
  - partial live evidence for `case_0026`,
  not a completed Windows same-run typed witness.

## 未確定

- No current retained Windows return binds the full chain
  `field-world value -> compose input -> PF16 store -> same-run true16 export`
  for any of `case_0024..0027`.
- `case_0024`, `case_0025`, and `case_0027` still have no coordinate-bound live
  source+field witness in retained returns.
- Even for `case_0026`, the missing field raw words mean the retained data are
  insufficient for exact `FUN_181170480` replay.
- The source comment around `dt_to_normalized()` states one threshold-scaling
  detail is still only implementation-grounded, not fully proven from the AEX
  caller path.
  See [OLMDistanceGradation.cpp](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMDistanceGradation/OLMDistanceGradation.cpp:481).

## Commands run

```sh
git status --short
rg -n "case_0023|case_0024|case_0025|case_0026|case_0027|OLMDistanceGradation" notes/CONFORMANCE_LEDGER.md refs/conformance refs/windows_returns
nl -ba mac/OLMDistanceGradation/OLMDistanceGradation.cpp | sed -n '370,510p'
nl -ba refs/conformance/olmdistancegradation_case0023_alpha_threshold_mac_ae_result_20260707.md | sed -n '1,140p'
nl -ba refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md | sed -n '1,160p'
nl -ba refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md | sed -n '1,120p'
nl -ba refs/conformance/windows_runtime_returns_fail_closed_20260713.md | sed -n '1,120p'
nl -ba refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md | sed -n '1,140p'
```
