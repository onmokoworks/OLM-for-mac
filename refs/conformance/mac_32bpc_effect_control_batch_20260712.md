# Mac 32bpc effect/control candidate batch (2026-07-12)

## FACT

`scripts/run_ae_32bpc_candidate_batch.py` now renders two FLOAT EXR artifacts
for every focused ColorKey and ToonDilate case:

- `effect_on`: the requested plug-in and parameters.
- `no_effect`: the identical bridge/input/project with
  `OLM_AE_DISABLE_EFFECT=1`.

Both artifacts are independently checked for runner success, expected
`effect_disabled` state, FLOAT RGBA EXR validity, and SHA-256. A missing or
misbound member fails the entire case. The index preserves both records under
`artifacts`; dry-run still starts no AE process.

## Verification

- `python3 -m py_compile scripts/run_ae_32bpc_candidate_batch.py
  refs/scripts/smoke_run_ae_32bpc_candidate_batch.py`: PASS.
- `python3 refs/scripts/smoke_run_ae_32bpc_candidate_batch.py`: PASS with 12
  mocked cases and 24 paired artifact runs, followed by a no-execution dry run.

This closes Mac candidate/control collection readiness only. It is not an
AE-exact result; AE 26.3 Windows effect/control artifacts, the expected
Windows AEX hash, and the explicitly bound Mac plug-in hash are still required
by the acceptance comparator. The Mac hash binds the intended installed
binary; it is not described as a host-observed loaded module hash.
