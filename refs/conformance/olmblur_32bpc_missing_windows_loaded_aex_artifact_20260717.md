# OLMBlur 32bpc loaded-AEX exact-slice blocker

Date: 2026-07-17

## Determination

The existing Windows 32bpc EXR refs and the Mac runner are **not sufficient**
to run or accept a loaded-module-bound cross-host `AE exact` slice.

The smallest eligible slice is `olmblur__case_0001`, because the existing Mac
request/runner already carries the case input hash, seven parameter identities,
32bpc SOFTWARE/working-space/output settings, and a post-render Mac
`vmmap` exact-path proof. The Windows return has valid effect-on and no-effect
FLOAT RGBA EXRs, but its provenance does not bind those EXRs to the required
OLMBlur AEX.

## Exact missing artifact

Provide one same-run Windows AE return for `olmblur__case_0001` containing:

- the loaded OLMBlur AEX absolute path;
- the loaded OLMBlur AEX SHA-256, expected to be
  `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` for the
  current actual-AEX contract;
- the bound AfterFX PID and module base/path observation proving that the
  effect-on EXR was rendered by that loaded module;
- the same-run effect-on and effect-disabled FLOAT RGBA EXR hashes;
- the same-run parameter readbacks for the case, including Legacy and repeat.

The existing Windows artifact set is recorded at
`refs/conformance/olmblur_32bpc_float_focus_audit_20260715.json` and contains
7/7 valid Windows FLOAT EXR pairs, but records `loaded_aex_sha256: missing`.
The retained case-specific audit likewise records the Windows AEX hash as
missing and rejects the comparison on parameter/provenance identity.

## Why no runner was added

The existing Mac runner at
`scripts/run_olmblur_32bpc_mac_validation_20260715.py` already fails closed on
missing input, plugin identity, project/output drift, and absent loaded-module
proof. Its actual run would still produce only a Mac candidate until the
Windows artifact above arrives. No AE launch was performed.

## Claim boundary

This is an evidence/provenance blocker only. It makes no Windows behavioral
claim and does not promote 32bpc `AE exact`.
