# OLMColorKey case_0005/case_0006 provenance review

Date: 2026-07-18

Scope: read-only audit of repository provenance. This note does not edit
ledger files, request packages, result packages, plug-in source, or reference
images.

## Question

Do the later `max_diff=0` records for `OLMColorKey` `case_0005` and
`case_0006` qualify as `Mac AE exact` under the repository's stricter
provenance rules, or do they only invalidate stale residual evidence?

## Artifacts read

- `notes/CONFORMANCE_LEDGER.md`
- `notes/PROOF_CONTRACT_LEDGER.md`
- `notes/REFERENCE_PROVENANCE_LEDGER.md`
- `refs/conformance/olmcolorkey_edge_residual_20260718.md`
- `refs/conformance/bitdepth_16bpc_exact_manifest_20260709.md`
- `refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json`
- `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625/request_manifest.json`
- `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625/reference_manifest.json`
- `handoff/ae_pixel_validation_20260618/results/bitdepth16_olmcolorkey_exact/AE_PIXEL_VALIDATION_RENDER_RESULT.json`
- `refs/reports/ae_host_validation_20260618_232926/ae_pixel_olmcolorkey_20260606/reports/ae_pixel_edgethin_residual.json`

## Findings

1. The subgroup report cited by the older edge-residual audit is not, by
   itself, a strict-provenance `AE exact` artifact.

   The file
   `refs/reports/ae_host_validation_20260618_232926/ae_pixel_olmcolorkey_20260606/reports/ae_pixel_edgethin_residual.json`
   does record `case_0005` and `case_0006` at `max_diff=0` and
   `nonzero_px=0`, but it contains only `cases` and `summary`.
   It does not carry the request id, canonical-reference declaration,
   renderer metadata, case settings, or output hashes that this repository now
   uses when it promotes a row to committed exactness. Read fail-closed, that
   report alone only invalidates the old stale residual claim.

2. The repository does contain a stricter, later provenance chain that does
   promote these cases to `Mac AE exact` for a declared slice.

   The later committed 16bpc exact-slice package binds:

   - request:
     `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625`
   - result:
     `handoff/ae_pixel_validation_20260618/results/bitdepth16_olmcolorkey_exact`
   - committed promotion:
     `refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json`

   In that chain:

   - `request_manifest.json` declares one threshold group with
     `max_diff=0`, `mean_diff=0.0`, `nonzero_px_percent=0.0` and includes
     both `olmcolorkey__case_0005` and `olmcolorkey__case_0006`.
   - `reference_manifest.json` records the Windows reference settings for both
     cases: `bits_per_channel=16`, `project_gpu_accel_type.current_name=SOFTWARE`,
     `requested_effect.name=OLM Color Key`, and case-specific parameters.
   - `AE_PIXEL_VALIDATION_RENDER_RESULT.json` shows all nine 16bpc OLMColorKey
     outputs were rendered with no listed warnings or errors.
   - the committed exact manifest classifies both cases as
     `result_status = "AE exact"` and records the output hashes:
     - `case_0005`: `a6264b08eae2f81abdc2626815488cef542fedf58d088de07fca3d9c2bec641b`
     - `case_0006`: `53c3a0481c8362e07626159f164dc04972288e4e5855c7d36a7fc130b37b7735`
   - those hashes match the corresponding files in the Mac result directory,
     the handoff request `expected/` directory, and the canonical Windows
     reference directory
     `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/`.

3. The request markdown's older "host integration smoke" wording does not
   block the later committed promotion.

   `AE_PIXEL_VALIDATION_REQUEST.md` describes the request as a host smoke and
   "not a final exact-equivalence claim." The repo's later policy layer is the
   materialized exact-slice manifest, whose correctness bar is explicit:
   `Only result_status == 'AE exact' is complete for the declared bit-depth slice.`
   Under the current ledgers and committed manifest policy, that later layer is
   the operative promotion artifact.

## Verdict

Fail-closed verdict:

- `ae_pixel_edgethin_residual.json` by itself is not enough to claim strict
  `Mac AE exact`; taken alone, it only invalidates stale residual evidence.
- `case_0005` and `case_0006` do qualify as `Mac AE exact` for the
  repository's declared covered 16bpc slice, because the separate committed
  request/reference/result/hash chain in
  `bitdepth_16bpc_exact_manifest_20260709.{md,json}` satisfies the stricter
  provenance bar.

If any element of that exact-slice chain drifts or disappears, fall back to
the narrower classification: stale residual evidence invalidated, but no exact
promotion.

## Verification

```text
python3 scripts/verify_ae_pixel_validation_result.py \
  handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625 \
  handoff/ae_pixel_validation_20260618/results/bitdepth16_olmcolorkey_exact \
  --run-dir /tmp/olmcolorkey_case56_review_verify

python3 tests/test_olmcolorkey_case0005_case0006_provenance_review_20260718.py
```
