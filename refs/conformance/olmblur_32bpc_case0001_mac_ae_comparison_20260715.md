# OLMBlur 32bpc Mac candidate audit

Verdict: `AE exact refused`

| case | parameters identical | no-op exact | no-op mismatches | effect comparison valid | effect exact | effect mismatches | max raw-u32 delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `olmblur__case_0001` | False | True | 0 | False | False | 207108 | 929154906 |
- Windows parameter mismatch `OLM OLM Blur-0003`: requested `2`, read back `1`.
- Effect result classification: `invalid_parameter_or_control_identity`.

Mac effect/no-op plug-in SHA-256: `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
Windows AEX SHA-256: `missing`.

Refusal reasons: Windows/Mac effect parameter identity mismatch, AE/project/color/output environment mismatch, Windows AEX hash missing from provenance.
