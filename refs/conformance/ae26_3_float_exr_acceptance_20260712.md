# AE 26.3 FLOAT EXR Acceptance Contract

Date: 2026-07-12
Scope: `OLMBlur`, `OLMColorKey`, and `OLMToonDilate` incoming 32bpc AE 26.3
FLOAT EXR requests.

## Decision

Use `refs/scripts/compare_ae26_3_float_exr_acceptance.py` as the intake gate.
It is intentionally separate from production code and does not make an
`AE exact` claim. A case is attributable only when the same package binds:

- AE `26.3`, `32bpc`, and `linear_light: false` (the `OLM EXR 32 Float`
  template is explicitly linear-light off);
- Windows/reference input, Windows no-effect control, Mac no-effect control,
  Windows effect-on output, and Mac effect-on output artifacts;
- uncompressed scanline EXR with exactly four FLOAT channels and matching
  dimensions;
- SHA-256 for every artifact;
- `effect_enabled: false` on the no-effect control; and
- an expected Windows AEX SHA-256 equal to the hash reported by the Windows
  effect render; and
- an expected Mac plug-in SHA-256 equal to the hash reported by the Mac effect
  render;
- Windows/macOS host identity, AE build, and `SOFTWARE` renderer; and
- a case-contract hash binding the input, parameters, and host settings.

Absolute paths are rejected from package metadata. Invoke with a caller-owned
artifact root so reports remain portable.

## Attribution boundary

The comparator emits two independent raw float32 bit comparisons:

| Field | Comparison | Meaning |
| --- | --- | --- |
| `windows_input_conversion` | source input -> Windows no-effect | Windows import/export conversion diagnostic |
| `host_input_conversion` | Windows no-effect -> Mac no-effect | cross-host AE conversion residual; never plugin evidence |
| `mac_effect_delta` | Mac no-effect control -> Mac effect output | diagnostic Mac plug-in delta |
| `cross_host_effect_output` | Windows effect output -> Mac effect output | actual cross-host conformance comparison |

The comparator reports `raw-float-bits-exact` only when the host/input control
is exact and the Windows and Mac effect outputs have identical float32 words.
It does not apply epsilon or normalize values. This is case evidence; ledger
promotion to `AE exact` still requires the complete manifest and host settings.
Use `--require-exact` for conformance intake; it exits nonzero when either host
parity or the cross-host effect output is not raw-float-bit exact.

## Smoke verification

```sh
python3 refs/scripts/smoke_compare_ae26_3_float_exr_acceptance.py
```

Result on 2026-07-12: PASS. The synthetic package proved an exact cross-host
effect output with a nonzero effect delta. Missing Windows effect output,
missing no-effect control, wrong linear-light mode, and mismatched Mac binary
hash were rejected.

The existing `scripts/verify_32bpc_float_return.py` remains the lower-level
Windows/Mac candidate verifier. This contract adds the missing provenance and
attribution binding; it does not replace that verifier or alter plugin code.

## Current readiness

This is an acceptance gate, not new reference evidence. Existing 32bpc
effect-on residuals for these lanes remain unattributed until each incoming
case supplies a matching no-effect FLOAT EXR control and loaded AEX hash.
No production source, ledger status, or exactness claim is changed by this
contract.
