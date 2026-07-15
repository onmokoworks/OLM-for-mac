# OLMSmoother2 32bpc No-Key Evidence Audit

Date: 2026-07-15
Scope: OLMSmoother2 v2 evidence and Mac FLOAT EXR validation only.

## Decision

The 2026-07-10 Windows return contains ten 1920x1080 EXR pairs for the
`OLM Smoother v2` effect under AE `26.3x87`, 32bpc, and the `SOFTWARE`
renderer. The EXRs are uncompressed RGBA FLOAT scanline files and are usable
as raw-float inputs. The returned manifest is not admissible to the existing
fail-closed Windows verifier because it has no per-artifact SHA-256 or
required header metadata.

No Mac FLOAT EXR result for OLMSmoother2 is present in the workspace. The
existing Mac evidence is PNG/8bpc or runtime/CLI evidence, so it cannot close
the 32bpc cross-host comparison.

## Exact Coverage

| Slice | Cases | Key flag | Smoother Version | Classification |
|---|---:|---:|---:|---|
| v2/no-key | `07`, `09` | `0` | `2` | higher-depth v2 no-key coverage |
| key-off but v1 mode | `01`, `03`, `05` | `0` | `1` | excluded; do not mix v1/v2 |
| key-on | `02`, `04`, `06`, `08`, `10` | `1` | `1`, `2` | excluded from no-key contract |

The two v2/no-key cases are not a gamma-free claim. Case `07` has
`Gamma Correction=1`, `Number of Gamma Colors=2`; case `09` has
`Gamma Correction=3`, `Number of Gamma Colors=5`. Those values are bound in
the Mac request and must be replayed exactly. This audit does not infer the
semantic meaning of the gamma enum from rendered output.

## Narrowest Mac Contract

The request at
`refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json`
contains only case `07`. It requires, for the same imported before-effects
FLOAT EXR and exact v2 parameters:

- one Mac no-effect control and one Mac effect-on output;
- AE `26.3`, 32bpc, `SOFTWARE`, working space `None`, linear blending off;
- `OLM EXR 32 Float`, exactly four FLOAT channels, uncompressed scanlines,
  1920x1080, and finite samples;
- SHA-256 for every Windows and Mac artifact, the loaded Mac plug-in, and the
  case/parameter contract; and
- raw float32 word comparison with no epsilon, normalization, color
  conversion, or retuning.

The contract is currently `blocked_pending_windows_artifact_attestation`.
The physical case-07 EXRs pass the local header/sample inspection, but the
Windows manifest does not bind their hashes. Until that provenance is added,
the Mac run must remain a candidate run and cannot be reported as AE exact.

## Evidence Boundary

The old `20260605_extra/OLMSmoother2` material is 8bpc PNG evidence. The
20260615 no-key grid is also PNG evidence. Legacy/current-AEX, gamma-color,
runtime-trace, case0012 common-core, production source, shared ledger, and
generic checker artifacts are outside this contract and are not promoted by
it. No raw Windows-vs-Mac comparison exists, so no AE-exact claim is made.
