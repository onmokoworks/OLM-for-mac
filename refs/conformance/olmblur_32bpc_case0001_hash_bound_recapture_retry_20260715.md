# OLMBlur 32bpc case_0001 hash-bound recapture retry

## Classification

The first hash-bound return is `failed_observation_gate`, not render evidence.
Its ZIP SHA-256 is
`de5c55c003150251726dc25b1a24035ae1a1d91cc738c4f94a5833afd09a67ac`.
It contains only duplicate status/manifest JSON files and reports that the
loaded AEX was not observed. It contains no EXR, AE result, AE log, module
inventory, or process diagnostics.

The old runner inspected only the PID returned by `Start-Process`. It did not
pause AE after effect setup, so launcher/worker PID separation or a missed
module-loaded time window could produce a false negative. This is an
inference, not a fact established by the sparse return. The return does not
show an AEX version mismatch and does not change OLMBlur correctness status.

## Retry contract

The retry request ID is
`olmblur_32bpc_case0001_hash_bound_recapture_retry_20260715`.

- Request ZIP SHA-256: `d178ff2a56eea84cb2b87261f28cd9a285d7936246a16423f45fbf3a3dcb7c53`
- Package contract SHA-256: `06f81dadf9da07151f7197a7208d44ccc857ed778af90a32a51e337a343021df`
- Required AEX SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`

The JSX now pauses after the effect and parameters are live. Its ready marker
contains a fresh nonce and the actual AfterFX PID. The runner verifies that PID
against the session, executable path, creation time, and launcher ancestry,
then requires the exact loaded AEX path and hash before writing the continue
marker. Module-probe attempts and AE/process diagnostics are retained on
failure. Effect-on and effect-free control still render in one AE process.

The retry remains only a request. It cannot become `AE exact` evidence until a
returned pair passes contract, EXR-header, no-effect-control, parameter, and
raw FLOAT comparison gates.
