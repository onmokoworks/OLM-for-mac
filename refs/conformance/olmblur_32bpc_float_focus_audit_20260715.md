# OLMBlur 32bpc float focus audit

Verdict: `blocked; no AE exact claim`

## Proven

- The focused request is exactly seven OLMBlur cases with 32bpc SOFTWARE requirements.
- The imported Windows return has effect-on and before-effects FLOAT RGBA EXRs for all seven cases.
- The imported Windows EXRs are valid uncompressed float-preserving 1920x1080 artifacts.
- Mac adapter and complete-worker fixture evidence remain local binary/worker evidence, not cross-host AE exactness.
- The prior Mac candidate note reports seven effect EXRs and four exact no-effect controls, but its Mac EXRs are not independently re-verifiable from imported workspace artifacts.

## Imported return

- Windows FLOAT RGBA EXR cases: `7/7`.
- Windows loaded AEX SHA-256: `missing`.
- Mac OLMBlur FLOAT EXR bundle imported: `False`.
- Mac loaded AEX SHA-256: `missing`.
- Prior Mac candidate note: seven effect outputs reported; no-effect controls reported exact for `0001..0004` and input-conversion differences for `0005..0007`.

| case | Windows effect/control hashes distinct |
|---|---:|
| `olmblur__case_0001` | True |
| `olmblur__case_0002` | True |
| `olmblur__case_0003` | True |
| `olmblur__case_0004` | True |
| `olmblur__case_0005` | True |
| `olmblur__case_0006` | True |
| `olmblur__case_0007` | True |

## Smallest missing cross-host gate

Provide one same-contract Mac effect-on/effect-disabled FLOAT RGBA EXR pair with case and parameter identity, bind the loaded Windows OLMBlur AEX SHA-256, and run a machine-readable raw FLOAT32 word comparison. Expand that passing gate to all seven cases before any seven-case `AE exact` claim.

Current effect deltas remain unattributed. No source change or tuning is justified by this return.
