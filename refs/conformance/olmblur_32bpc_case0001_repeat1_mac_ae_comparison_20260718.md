# OLMBlur 32bpc Mac candidate audit

Verdict: `AE exact refused`

| case | parameters identical | no-op exact | no-op mismatches | effect comparison valid | effect exact | effect mismatches | max raw-u32 delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `olmblur__case_0001` | True | True | 0 | False | False | 201576 | 310132694 |
- Effect result classification: `invalid_environment_or_provenance_identity`.

Mac effect/no-op plug-in SHA-256: `71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72`.
Windows AEX SHA-256: `missing`.

Refusal reasons: AE/project/color/output environment mismatch, Windows AEX hash missing from provenance.
