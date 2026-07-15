# OLMBlur 16bpc Current Plugin Revalidation

Immutable conformance record for the just-completed current Mac OLMBlur 16bpc
revalidation on 2026-07-15.

## FACT

- The supplied integer verifier compared 7 cases and reported 5 exact.
- Exact cases are `0001`, `0002`, `0005`, `0006`, and `0007`.
- `case_0003` has `max_diff=2` across 20 reported samples.
- `case_0004` has `max_diff=2` across 2 reported samples.
- The installed current Mac plugin SHA-256 is
  `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
- The `case_0006` output SHA-256 equals the retained Windows canonical
  `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`.
- No conformance claim is made for unresolved cases `0003` and `0004`.

## INFERENCE

- This is a bounded result for the named current Mac plugin instance. It does
  not modify source, orchestration, ledger, or image artifacts.
- The exact count is `5/7`; unresolved cases are excluded from that set.

## Provenance

- Ephemeral candidate set: `olmblur_16bpc_candidates_c76c687c` (not copied).
- Retained verifier report:
  `refs/conformance/olmblur_16bpc_current_plugin_verifier_report_20260715.json`, SHA-256
  `a56f6ba2bb85b75cd9333963efc6e980b431b7a5e2eceacc0fcb993e20d982e8`.
- Retained observation report:
  `refs/conformance/olmblur_case0006_current_plugin_observation_report_20260715.json`,
  SHA-256 `b7f1cb02326879e18cd21ad657cc305781793c69ea2733da7d48a161dc4b8df7`.
- Each case record pins its retained canonical Windows image path/hash. For
  the five exact cases, the candidate hash equals that retained reference hash.
- Retained case-0006 provenance: `refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.json`.
- Retained observation contract: `refs/mac_validation_requests/olmblur_case0006_mac_observation_20260715.json`.

## Smoke

`python3 refs/scripts/smoke_olmblur_16bpc_current_plugin_revalidation_20260715.py`

The smoke validates the retained verifier and observation report hashes, the
record's 7-case/5-exact/2-unresolved counts, the pinned plugin SHA, every
canonical Windows reference hash, and candidate/reference hash equality for
all five exact cases. It does not require or copy ephemeral image outputs.
