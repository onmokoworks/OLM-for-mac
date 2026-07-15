# OLMBlur 32bpc case_0001 recapture request

- Request: `olmblur_32bpc_case0001_hash_bound_recapture_20260715`
- ZIP SHA-256: `f0dd409e2455ade7a853386ccaafaadb977af162b839cba88a4a3cb43e76fde4`
- Package-contract SHA-256: `309d4ee9726b0516addf7f93bb72e76e37ed509a75e4a69db9681ed9da5b7301`
- Required `OLMBlur.aex` SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`

The package renders effect-on and no-effect in one AE `26.3x87` process,
project, comp, and input. It reads back all five OLMBlur parameters, removes
the effect before the control, verifies an empty Effect Parade, binds the
launched PID to the loaded AEX hash, and returns hashes plus copies of the
executed input/manifests/JSX/runner.

An `answered_candidate_pending_exr_header_validation` return is not exact
evidence yet. Intake must validate uncompressed FLOAT RGBA EXR headers and all
root/contract/runtime identities before raw FLOAT32 comparison.
