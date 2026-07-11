# OLMDistanceGradation 16bpc Rounding Closeout Mac-Side Sort - 2026-07-08

## Scope

This note is a local整理文書 only. It is based on existing 2026-07-08 reports and does not use CLI reimplementation output as Windows truth.

Primary inputs:

- `notes/CONFORMANCE_LEDGER.md` (`OLMDistanceGradation` row and `Latest Overrides`)
- `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`
- `refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_return_intake_20260708.md`
- `refs/conformance/olmdistancegradation_case0012_dominant_channel_closeout_20260708.md`
- `refs/conformance/olmdistancegradation_layer_source_true16_audit_20260708.md`
- supporting intake/classification:
  - `refs/conformance/olmdistancegradation_depthgate_quantization_return_intake_20260708.md`
  - `refs/conformance/olmdistancegradation_depthgate_907_store_export_return_intake_20260708.md`
  - `refs/conformance/olmdistancegradation_case0014_layer_source_return_intake_20260708.md`
  - `refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md`

## 1. Family split

### A. Families that can be classified further on Mac without new Windows data

These are already far enough classified that Mac-side work can stay limited to local observation, representative-pixel bookkeeping, or narrowing of which witness should be asked next.

1. `case_0024..0027` (`max=1` near-miss family)
   - Current state: already classified as `export-quantization-first`.
   - Basis:
     - `olmdistancegradation_depth_gate_result_20260708.md`
     - `olmdistancegradation_depthgate_nearmiss_family_20260708.md`
     - `olmdistancegradation_depthgate_quantization_return_intake_20260708.md`
   - Mac-only value left:
     - keep this family grouped as one quantization/end-of-pipe family;
     - select/confirm representative pixels and pairings for any future witness;
     - avoid topology/source-mask retuning.
   - Important limit:
     - this does **not** close `(907,222)`.

2. Layer/no-bg residual family shape (`case_0012/0013/0014/0016`)
   - Current state: broad source-ownership hypothesis is already narrowed.
   - Basis:
     - `olmdistancegradation_case0012_dominant_channel_closeout_20260708.md`
     - `olmdistancegradation_layer_source_true16_audit_20260708.md`
     - `olmdistancegradation_case0014_layer_source_return_intake_20260708.md`
   - Mac-only classification now justified:
     - this is no longer a broad distance-field/topology family;
     - after the accepted dominant-channel rule, the remaining lane is a shared `max 2/4/2` true16 end-of-pipe/store-export rounding family;
     - `case_0014` preserves alpha while RGB is low, which supports “end-of-pipe/store/export” over “field topology”.
   - Important limit:
     - classification can be tightened, but proof cannot be finished on Mac alone.

3. Smaller residual buckets
   - `case_0016` and `case_0028` remain separate small families per the ledger/depth-gate report.
   - Mac-only value left:
     - keep them separate from the `case_0024..0027` near-miss family and from the shared Layer/no-bg rounding lane;
     - do not merge them into a broader fix hypothesis without new evidence.

### B. Families that require Windows same-run store/export evidence

These cannot be closed by further Mac-only reasoning from the current evidence.

1. `case_0026 (907,222)` inside the `case_0024..0027` near-miss family
   - Required reason:
     - `olmdistancegradation_depthgate_907_store_export_return_intake_20260708.md` says the current return is `answered_partial`;
     - no fresh same-run Windows output-world bind, no directly observed stored PF16 word from the actual write, and no same-run export observation.
   - Needed proof:
     - same-run Windows PF16 store word plus same-run export result for `(907,222)`.

2. Shared Layer/no-bg rounding lane (`case_0012` representative + `case_0014` representative)
   - Required reason:
     - `olmdistancegradation_case0012_case0014_store_export_rounding_return_intake_20260708.md` is `failed_partial`;
     - it lacks fresh same-run pre-store float, PF_Pixel16 store word, and true16 export for both families.
   - Needed proof:
     - one representative from `case_0012` and one from `case_0014`, with the full same-run chain from source input through store and export.

3. Any global export-rounding retune
   - Required reason:
     - `olmdistancegradation_case0012_dominant_channel_closeout_20260708.md` explicitly says output-space `+2` what-if corrections are not implementation proof;
     - current evidence does not justify changing clamp/export rounding globally.
   - Needed proof:
     - direct Windows same-run store/export evidence on the representative pixels above.

## 2. Mac-side safe local A/B check

## Safe to try on Mac

Only observational A/B is justified from the current reports:

1. Representative-pixel Mac same-run observation plan
   - Target:
     - Layer lane representative `+/-2` pixels and the `case_0014` `-4` subset;
     - the unresolved near-miss pixel `(907,222)` as a control.
   - Safe question:
     - does the Mac run show a store-vs-export step change at those pixels, without changing source?
   - Why safe:
     - it does not use CLI as verdict truth;
     - it does not claim Windows parity from Mac-only measurements;
     - it only helps decide whether the next Windows request should stay narrowed exactly where it already is.

2. Representative selection / pairing cleanup
   - Safe question:
     - are the currently named representatives still the best minimal witness set for the remaining lanes?
   - Why safe:
     - existing reports already identify clean representatives:
       - `case_0026` / `(907,222)` for the near-miss family;
       - `case_0012` and `case_0014` representatives for the Layer/no-bg rounding lane.

## Not safe to try on Mac

1. Any new Mac source retune aimed at export rounding
   - blocked by the missing Windows same-run store/export proof.

2. Any verdict that uses the CLI reimplementation as Windows truth
   - forbidden by the standing ledger rule and repeated in the depth-gate report.

3. Any global clamp/export rounding adjustment inferred from the local `+2/-4` residual pattern
   - existing reports call this a what-if only, not proof.

## 3. Closeout reading

- Mac-only progress is still possible for classification hygiene:
  - keep the open residuals split into
    - `near-miss quantization family`,
    - `near-miss 907 unresolved singleton`,
    - `Layer/no-bg shared max 2/4/2 rounding lane`,
    - `small separate families`.
- Mac-only progress is **not** enough for implementation closeout:
  - `(907,222)` needs Windows same-run PF16 store/export proof.
  - `case_0012` and `case_0014` need Windows same-run pre-store/store/export proof.
- Therefore the current Mac-side posture should stay:
  - classification and witness narrowing are allowed;
  - source retuning and global rounding changes are not justified.
