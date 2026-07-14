# FLOAT EXR Control vs Cross-Host Exactness

Date: 2026-07-14

## Decision

`refs/scripts/compare_ae26_3_float_exr_acceptance.py` is the fail-closed
verifier/report for AE 26.3 FLOAT EXR packages. It must be read as two
independent gates:

| Report field | Gate | Permitted conclusion |
| --- | --- | --- |
| `host_input_conversion` | Windows no-effect control vs Mac no-effect control | Mac-side control parity; never plugin evidence |
| `mac_effect_delta` | Mac no-effect control vs Mac effect output | Mac-side plugin delta evidence; not Windows-vs-Mac AE exactness |
| `cross_host_effect_output` | Windows effect output vs Mac effect output | Eligible for exactness only when the control gate is exact |
| `attribution` / `cross_host_status` | fail-closed verdicts | `eligible` plus `raw-float-bits-exact` is required for a cross-host exactness claim |

The verifier requires the same case contract, AE/depth/renderer settings,
source, both no-effect controls, both effect outputs, and loaded binary hashes.
It accepts only uncompressed scanline EXR with four FLOAT channels and compares
raw float32 words. It applies no epsilon, color conversion, or normalization.

## Current evidence

The accepted second-generation return proves Mac/Windows-independent plugin
delta behavior for ColorKey `case_0002` and ToonDilate `case_0001`: Windows
effect vs Windows no-effect is exact, and the corresponding Mac effect/control
pairs are exact. It does **not** prove cross-host AE exactness. The retained
control evidence reports Windows-vs-Mac no-effect RGB mismatch in `6,220,800`
samples (`1920*1080*3`, alpha excluded), with `max_raw_u32_delta=36,717,327`.
Therefore the cross-host verdict remains blocked by the AE import/control
boundary. Do not tune plugin pixel math from it.

## Regression evidence

```sh
python3 refs/scripts/smoke_32bpc_control_vs_cross_host.py
```

The smoke covers a raw-bit exact two-gate pass and a case where effect outputs
match but the Mac control differs by one FLOAT sample. The latter must exit
nonzero under `--require-exact` and report
`blocked-by-host-input-conversion` / `not-exact-or-not-attributable`.

This note and smoke test do not modify plugin code and do not promote any
existing case to `AE exact`.
